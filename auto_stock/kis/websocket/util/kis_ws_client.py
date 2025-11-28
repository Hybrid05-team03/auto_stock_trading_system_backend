import os, asyncio, json, redis, signal, logging
import websockets
import django, dotenv

from kis.auth.kis_ws_key import get_web_socket_key
from kis.websocket.parser.quote_parser import parse_quote
from kis.websocket.parser.price_parser import parse_price
from kis.websocket.parser.index_parser import parse_index

dotenv.load_dotenv(".env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auto_stock.settings")
django.setup()

# ------------------ 환경 변수 ------------------
WS_BASE_URL_REAL = os.getenv("KIS_WS_BASE_URL_REAL")
CUST_TYPE = os.getenv("KIS_WS_CUSTOMER_TYPE", "P")
REDIS_TTL = 60 * 60 * 18
REDIS_CHANNEL = "subscribe.add"

r = redis.Redis(decode_responses=True)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ------------------ 글로벌 상태 ------------------
stop_event = asyncio.Event()
send_queue = asyncio.Queue()  # 소켓 구독 요청 저장 큐
subscriptions = {}  # {(tr_id, tr_key): redis_prefix}
shared_ws = None  # 하나의 웹 소켓 공유


# ------------------ 구독 작업 ------------------
async def subscribe_worker(tr_id, tr_key, redis_key_prefix):

    # 구독 요청 -> send_queue & subscriptions dict 등록
    key = (tr_id, tr_key)

    if key in subscriptions:
        logger.info(f"[WARN] 이미 등록된 구독: {key}")
        return

    subscriptions[key] = redis_key_prefix

    await send_queue.put({
        "tr_id": tr_id,
        "tr_key": tr_key,
        "redis_prefix": redis_key_prefix
    })

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
                else:
                    parsed = None

                if parsed:
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