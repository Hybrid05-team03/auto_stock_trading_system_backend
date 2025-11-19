import logging

logger = logging.getLogger(__name__)


def parse_quote(raw: str) -> dict:
    try:
        parts = raw.split("|")
        if len(parts) < 4:
            raise ValueError("Invalid quote format")

        tr_id = parts[1]
        tr_key = parts[3].split("^")[0]
        fields = parts[3].split("^")

        return {
            "tr_id": tr_id,
            "symbol": tr_key,                  # 종목 코드
            "time": fields[1],                 # HHMMSS
            "quote": int(fields[2]),           # 현재가
        }
    except Exception as e:
        logger.warning(f"[parse_quote] 파싱 실패: {e}")
        return None