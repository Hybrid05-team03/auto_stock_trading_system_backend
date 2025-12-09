import logging

logger = logging.getLogger(__name__)

## 체결 정보 파싱
def parse_exec(raw: str):
    try:
        parts = raw.split("|")
        body = parts[3].split("^")

        logger.info(f"체결 데이터 구독 parts 정보 확인={parts}")
        logger.info(f"체결 데이터 구독 body 정보 확인={body}")

        return {
            "tr_key": parts[3].split("^")[0],
            "exec_type": body[10],      # CNTG_YN 1=체결, 2=정정/취소
            "order_no": body[5],        # ODER_NO
            "price": body[11],          # CNTG_UNPR
            "qty": body[12],            # CNTG_QTY
            "ts": body[2],              # 체결시간
        }
    except:
        return None