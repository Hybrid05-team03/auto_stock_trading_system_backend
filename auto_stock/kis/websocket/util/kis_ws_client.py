import os, asyncio, json, redis, signal, logging
import websockets
import django, dotenv

dotenv.load_dotenv(".env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auto_stock.settings")
django.setup()

from trading.models import OrderRequest
from trading.services.save_order_execution import save_execution_data

from kis.auth.kis_ws_key import get_web_socket_key
from kis.websocket.parser.quote_parser import parse_quote
from kis.websocket.parser.price_parser import parse_price
from kis.websocket.parser.index_parser import parse_index
from kis.websocket.parser.execution_parser import parse_exec


# ------------------ 환경 변수 ------------------
WS_BASE_URL_REAL = os.getenv("WS_BASE_URL_REAL")
CUST_TYPE = os.getenv("CUST_TYPE")
REDIS_TTL = 60 * 60 * 18
REDIS_CHANNEL = "subscribe.add"

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# ------------------ 글로벌 상태 ------------------
stop_event = asyncio.Event()
send_queue = asyncio.Queue()  # 소켓 구독 요청 저장 큐
subscriptions = {}  # {(tr_id, tr_key): redis_prefix}
shared_ws = None  # 하나의 웹 소켓 공유


# 체결 데이터 저장 작업
def handle_execution(parsed):
    """
    H0STCNI0 체결 데이터 처리:
    - 체결 발생 시 OrderRequest 조회
    - 체결 데이터 저장
    - 상태 SELL_DONE 으로 변경
    """
    try:
        order_no = parsed["order_no"]      # 주문번호
        cntg_yn = parsed["cntg_yn"]        # 체결 여부 (1: 체결, 2: 정정/취소)

        # 체결이 아닌 경우 무시
        if cntg_yn != "1":
            return

        # DB에서 주문 찾기
        try:
            order = OrderRequest.objects.get(kis_order_id=order_no)
        except OrderRequest.DoesNotExist:
            logger.warning(f"[EXEC] 주문번호 {order_no} 에 해당하는 OrderRequest 없음")
            return

        logger.info(f"[EXEC] 매도 체결 발생 → 주문번호 {order_no}")

        # 체결 정보 저장
        save_execution_data(order, {
            "EXEC_QTY": parsed["qty"],
            "EXEC_PRICE": parsed["price"],
            "EXEC_TIME": parsed["time"],
        }, "SELL")

        # 상태 업데이트
        order.status = "SELL_DONE"
        order.save()

        logger.info(f"[EXEC] SELL_DONE 업데이트 완료 → 주문 {order_no}")

    except Exception as e:
        logger.error(f"[EXEC] 체결 처리 실패: {e}")


# ------------------ 구독 작업 ------------------
async def subscribe_worker(tr_id, tr_key, redis_key_prefix):

    # 구독 요청 -> send_queue & subscriptions dict 등록
    key = (tr_id, tr_key)

    if key in subscriptions:
        logger.info(f"[WARN] 이미 등록된 구독: {key}")
        return

    subscriptions[key] = redis_key_prefix
    payload = {
        "tr_id": tr_id,
        "tr_key": tr_key,
        "redis_prefix": redis_key_prefix
    }
    logging.debug(f"[ SUBSCRIBE ] 구독 요청 body → {payload}")
    await send_queue.put(payload)

    logger.info(f"[ QUEUE ] 구독 요청 큐 등록 → {redis_key_prefix}:{tr_key}")


# ------------------ WebSocket 수신 루프 ------------------
async def ws_recv_loop():
    global shared_ws

    while not stop_event.is_set():
        try:
            raw = await asyncio.wait_for(shared_ws.recv(), timeout=10)
            print("\n================ RAW FRAME ================")
            print(raw)
            print("===========================================\n")

            # JSON 메시지 처리
            try:
                obj = json.loads(raw)
                tr_id = obj.get("header", {}).get("tr_id")

                # PING (최초 연결 확인)
                if tr_id == "PINGPONG":
                    logger.info("[INFO] KIS와 ping 연결 확인 ")

                # SUBSCRIBE SUCCESS
                msg_cd = obj.get("body", {}).get("msg_cd", "")
                if msg_cd in ["OPSP0000", "OPSP0003"]:
                    logger.info("[WS] 구독 성공 메시지 수신")
                    continue
            except json.JSONDecodeError:
                pass

            # 가격 데이터 처리 (PIPE format)
            if "|" in raw:
                parts = raw.split("|")
                if len(parts) < 4:
                    continue

                tr_id = parts[1]
                tr_key = parts[3].split("^")[0]

                redis_prefix = subscriptions.get((tr_id, tr_key))
                if not redis_prefix:
                    logger.warning(f"[WS] 알 수 없는 종목 데이터 수신 → {tr_id}:{tr_key}")
                    continue

                # 파싱 실행
                if redis_prefix == "price":
                    parsed = parse_price(raw)
                elif redis_prefix == "quote":
                    parsed = parse_quote(raw)
                elif redis_prefix == "index":
                    parsed = parse_index(raw)
                elif redis_prefix == "exec":
                    parsed = parse_exec(raw)
                else:
                    parsed = None

                if parsed:
                    # 체결 데이터
                    if redis_prefix == "exec":
                        handle_execution(parsed)
                    redis_key = f"{redis_prefix}:{tr_key}"
                    r.set(redis_key, json.dumps(parsed), ex=REDIS_TTL)
                    logger.info(f"[WS:{tr_id}] 저장됨 → {redis_key}")
                else:
                    logger.warning(f"[WS] 파싱 실패 → {tr_id}:{tr_key}")

        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error(f"[WS] 수신 오류: {e}")
            break


# ------------------ WebSocket 송신 루프 ------------------
async def ws_send_loop(approval_key):
    # 큐의 모든 구독 요청을 하나의 웹 소켓으로 전송
    global shared_ws

    while not stop_event.is_set():
        try:
            data = await send_queue.get()

            msg = {
                "header": {
                    "approval_key": approval_key,
                    "tr_type": "1",
                    "custtype": CUST_TYPE,
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": data["tr_id"],
                        "tr_key": data["tr_key"]
                    }
                }
            }

            await shared_ws.send(json.dumps(msg))
            logger.info(f"[WS] 구독 전송 → {data['tr_id']} / {data['tr_key']}")
            print(msg)
        except Exception as e:
            logger.error(f"[WS] 구독 전송 실패: {e}")

        await asyncio.sleep(0.03)


# ------------------ Redis 이벤트 수신 → 구독 요청 ------------------
async def redis_subscribe_listener():
    pubsub = r.pubsub()
    pubsub.subscribe(REDIS_CHANNEL)
    logger.info("[INFO] Redis 구독 요청 대기")

    while not stop_event.is_set():
        message = pubsub.get_message()
        if message and message["type"] == "message":
            try:
                data = json.loads(message["data"])
                tr_id = data["tr_id"]
                tr_key = data["tr_key"]
                redis_prefix = data["type"]
                await subscribe_worker(tr_id, tr_key, redis_prefix)
            except Exception as e:
                logger.warning(f"Redis 메시지 처리 실패: {e}")

        await asyncio.sleep(0.3)


# ------------------ WebSocket 단일 연결 관리 ------------------
async def main_websocket():
    global shared_ws

    approval_key = get_web_socket_key()
    async with websockets.connect(WS_BASE_URL_REAL) as ws:
        shared_ws = ws
        logger.info("[WS] 연결 완료")

        recv_task = asyncio.create_task(ws_recv_loop())
        send_task = asyncio.create_task(ws_send_loop(approval_key))
        redis_task = asyncio.create_task(redis_subscribe_listener())

        await asyncio.gather(recv_task, send_task, redis_task)


# ------------------ 종료 처리 ------------------
def handle_sigint():
    logger.info(" [WAIT] 종료 수신")
    stop_event.set()


signal.signal(signal.SIGINT, lambda sig, frame: handle_sigint())


# ------------------ 메인 ------------------
async def main():
    await main_websocket()


if __name__ == "__main__":
    asyncio.run(main())