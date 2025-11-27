import logging, time

from auto_stock.celery import app
from kis.api.account import fetch_balance
from trading.services.rsi_process import get_rsi_signal

logger = logging.getLogger(__name__)


# celery 비트로 주기적 비동기 실행
## celery -A auto_stock beat -l info
@app.task
def auto_sell():
    balance = fetch_balance()

    print(f"확인 ----- {balance}")
    if not balance or "stocks" not in balance:
        logger.info("[AUTO-SELL] 보유 종목 없음")
        return

    top_stocks = balance["stocks"][:3]
    for item in top_stocks:
        symbol = item["symbol"]
        qty = item["quantity"]

        if qty <= 0:
            continue

        time.sleep(1.2)
        signal, rsi = get_rsi_signal(symbol, period=14)

        logger.info(f"[AUTO-SELL] 종목={symbol}, 보유수량={qty}, RSI={rsi}, 신호={signal}")

        if signal == "SELL":
            logger.info(f"[AUTO-SELL] 시장가 매도 완료 : {symbol} {qty}주")
        else:
            logger.info(f"[AUTO-SELL] 매도 실패 : 조건 미충족")