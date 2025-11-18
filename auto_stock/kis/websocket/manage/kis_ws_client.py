import os, asyncio, json, redis, signal, logging
import django, dotenv
import websockets

from kis.auth.kis_ws_key import get_web_socket_key
from kis.websocket.parser.quote_parser import parse_quote
from kis.websocket.parser.price_parser import parse_price

# ------------------ 환경 설정 ------------------
dotenv.load_dotenv(".env.local")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auto_stock.settings")
django.setup()

WS_BASE_URL = os.getenv("KIS_WS_BASE_URL", "ws://ops.koreainvestment.com:31000")
CUST_TYPE = os.getenv("KIS_WS_CUSTOMER_TYPE", "P")
REDIS_TTL = 60
REDIS_CHANNEL = "subscribe.add"

r = redis.Redis(decode_responses=True)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

active_connections = {}  # {(tr_id, tr_key): websocket}
stop_event = asyncio.Event()

# ------------------ 구독 작업 ------------------
async def subscribe_worker(tr_id, tr_key, redis_key_prefix):
    approval_key = get_web_socket_key()
    try:
        async with websockets.connect(WS_BASE_URL) as ws:
            active_connections[(tr_id, tr_key)] = ws
            await ws.send(json.dumps({
                "header": {
                    "approval_key": approval_key,
                    "tr_type": "1",
                    "custtype": CUST_TYPE,
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {"tr_id": tr_id, "tr_key": tr_key}
                }
            }))
            logger.info(f"[ SUBSCRIBE START ]: {tr_id}  구독 시작 → {tr_key}")

            while not stop_event.is_set():
                raw = await ws.recv()

                # 메시지 필터링 및 저장
                redis_key = f"{redis_key_prefix}:{tr_key}"
                try:
                    parsed_json = json.loads(raw)
                    msg_cd = parsed_json.get("body", {}).get("msg_cd", "")
                    if msg_cd in ["OPSP0000", "OPSP0003", "OPSP9991"] or parsed_json.get("body", {}).get("rt_cd") != "0":
                        continue
                except:
                    pass

                try:
                    parsed = parse_quote(raw) if redis_key_prefix == "quote" else parse_price(raw)
                    if parsed:
                        r.set(redis_key, json.dumps(parsed), ex=REDIS_TTL)
                        logger.info(f"[WS:{tr_id}] 저장됨 → {redis_key}")
                except Exception as e:
                    logger.warning(f"[WS:{tr_id}] 파싱 오류: {e}")
    except Exception as e:
        logger.error(f"[WS:{tr_id}] 연결 오류: {e}")

# ------------------ 구독 메시지 수신 ------------------
async def redis_subscribe_listener():
    pubsub = r.pubsub()
    pubsub.subscribe(REDIS_CHANNEL)
    logger.info(f"📡 Redis 구독 대기 중... 채널: {REDIS_CHANNEL}")

    while not stop_event.is_set():
        message = pubsub.get_message()
        if message and message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                tr_id = data["tr_id"]
                tr_key = data["tr_key"]
                redis_key_prefix = data["type"]

                key = (tr_id, tr_key)
                if key in active_connections:
                    logger.info(f"⚠️ 이미 구독 중: {key}")
                    continue

                asyncio.create_task(subscribe_worker(tr_id, tr_key, redis_key_prefix))
            except Exception as e:
                logger.warning(f"[!] 메시지 처리 실패: {e}")
        await asyncio.sleep(0.5)

# ------------------ 종료 처리 ------------------
def handle_sigint():
    logger.info("🛑 종료 요청 수신됨...")
    stop_event.set()

signal.signal(signal.SIGINT, lambda sig, frame: handle_sigint())

# ------------------ 메인 ------------------
async def main():
    await redis_subscribe_listener()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        logger.info("✅ 정상 종료 완료")