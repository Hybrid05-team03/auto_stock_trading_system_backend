import logging

logger = logging.getLogger(__name__)

def parse_price(raw: str) -> dict:
    """
    실시간 체결 데이터 파서 (H0STCNT0 용)
    예시 raw: 0|H0STCNT0|001|005930^145557^0^71200^100^71200^71200^71200^1563661^0^0^...
    """
    try:
        parts = raw.split("|")
        if len(parts) < 4:
            raise ValueError("Invalid price format")

        tr_id = parts[1]  # H0STCNT0
        tr_key = parts[3].split("^")[0]
        fields = parts[3].split("^")

        return {
            "tr_id": tr_id,
            "symbol": tr_key,
            "time": fields[1],               # 체결시간 (예: HHMMSS)
            "sign": fields[2],               # 대비기호
            "price": int(fields[3]),         # 현재가
            "change": int(fields[4]),        # 전일 대비
            "open": int(fields[5]),          # 시가
            "high": int(fields[6]),          # 고가
            "low": int(fields[7]),           # 저가
            "volume": int(fields[8]),        # 체결량
            "acc_volume": int(fields[9]),    # 누적 거래량
            "acc_value": int(fields[10]),    # 누적 거래대금
        }

    except Exception as e:
        logger.warning(f"[parse_price] 파싱 실패: {e}")
        return None