import logging

logger = logging.getLogger(__name__)


def parse_price(raw: str) -> dict:
    try:
        parts = raw.split("|")
        tr_id = parts[1]
        tr_key = parts[3].split("^")[0]
        fields = parts[3].split("^")

        current_price = float(fields[11])
        change = int(fields[4])
        previous_price = current_price - change
        change_rate = round((change / previous_price) * 100, 2) if previous_price != 0 else 0.0

        return {
            "tr_id": tr_id,
            "symbol": tr_key, # 종목 코드
            "timestamp": fields[1],
            "current_price": current_price,
            "change_rate": change_rate,
            "trade_value": int(fields[10]),
        }

    except Exception as e:
        logger.warning(f"[parse_price] 파싱 실패: {e}")
        return None