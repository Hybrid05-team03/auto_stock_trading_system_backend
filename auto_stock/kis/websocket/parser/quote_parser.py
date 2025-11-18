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
            "symbol": tr_key,
            "time": fields[1],  # 예: HHMMSS 형식
            "price": int(fields[2]),  # 현재가
            # 필드 추가 가능: fields[3], fields[4], ...
        }
    except Exception as e:
        logger.warning(f"[parse_quote] 파싱 실패: {e}")
        return None