import os
import logging

import django, dotenv
from kis.api.util.overseas_index import extract_overseas_index_daily_price
from kis.constants.const_index import OVERSEAS_INDEX_CODE_NAME_MAP
from kis.api.util.request_real import request_get


from typing import List, Dict, Optional, Any, Tuple
from datetime import date, timedelta


logger = logging.getLogger(__name__)

dotenv.load_dotenv(".env.local")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auto_stock.settings")
django.setup()



###### 현재 사용되지 않고 있음 ##############
def kis_get_index_last2(code: str) -> dict:
    path = os.getenv("KIS_BASE_URL")
    tr_id = os.getenv("KIS_INDEX_DAILY_TR_ID", "FHKUP03500100")

    today_d = date.today()
    start_d = today_d - timedelta(days=10)

    params = {
        "FID_COND_MRKT_DIV_CODE": "U",
        "FID_INPUT_ISCD": code,
        "FID_INPUT_DATE_1": start_d.strftime("%Y%m%d"),
        "FID_INPUT_DATE_2": today_d.strftime("%Y%m%d"),
        "FID_PERIOD_DIV_CODE": "D",
    }

    try:
        data = request_get(path, tr_id, params)
    except Exception as e:
        logger.error(f"[KIS INDEX ERROR] Failed to fetch index {code}: {e}")
        return {"today": None, "yesterday": None}

    rows = data.get("output2", [])
    if not rows:
        return {"today": None, "yesterday": None}

    parsed = []
    for row in rows:
        ymd = row.get("stck_bsop_date")
        price_str = row.get("bstp_nmix_prpr")
        if not ymd or not price_str:
            continue
        try:
            close = float(price_str)
            parsed.append({"date": ymd, "close": close})
        except:
            continue

    if len(parsed) < 2:
        return {"today": None, "yesterday": None}

    parsed.sort(key=lambda r: r["date"])
    return {
        "today": parsed[-1],
        "yesterday": parsed[-2]
    }




#----------------------------------------------------------------------
# 해외 지수 기간별 조회
#----------------------------------------------------------------------
def fetch_overseas_index_period_series(
        fid_cond_mrkt_div_code: str,
        fid_input_iscd: str,
        start_d: date,
        end_d: date,
        period_div_code: str = "D",
) -> List[Dict[str, Any]]:
    path = "/uapi/overseas-price/v1/quotations/inquire-daily-chartprice"
    tr_id = "FHKST03030100"

    params = {
        "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
        "FID_INPUT_ISCD": fid_input_iscd,
        "FID_INPUT_DATE_1": start_d.strftime("%Y%m%d"),
        "FID_INPUT_DATE_2": end_d.strftime("%Y%m%d"),
        "FID_PERIOD_DIV_CODE": period_div_code,
    }
    logger.debug("[OVERSEAS_PERIOD] request params=%s", params)

    try:
        data = request_get(path, tr_id, params)

    except Exception as e:
        logger.error("[OVERSEAS_PERIOD] request error: %s", e)
        return []

    logger.debug(
        "[OVERSEAS_PERIOD] resp keys=%s rt_cd=%s msg_cd=%s msg1=%s",
        list(data.keys()),
        data.get("rt_cd"),
        data.get("msg_cd"),
        data.get("msg1"),
    )

    if data.get("rt_cd") != "0":
        logger.error(
            "[OVERSEAS_PERIOD] KIS error rt_cd=%s msg_cd=%s msg1=%s",
            data.get("rt_cd"),
            data.get("msg_cd"),
            data.get("msg1"),
        )
        return []

    # 문서상 body 구조: output1(기본정보) + output2(기간별 시세 리스트) :contentReference[oaicite:3]{index=3}
    rows = data.get("output2") or data.get("output1") or []
    if isinstance(rows, dict):
        rows = [rows]

    return rows


# --------------------------------------------------------------------
# 해외 지수/환율 스냅샷 (오늘/전일 종가) – 기간별시세 기반
# --------------------------------------------------------------------
def fetch_overseas_index_snapshot(index_key: str) -> Optional[Dict[str, Optional[float]]]:
    """
    OVERSEAS_INDEX_CODE_NAME_MAP 에 정의된 해외 지수/환율 1종에 대해
    기간별시세 API로 오늘/전일 '종가'를 가져온다.

    Returns:
        {
            "name": 지수명 (예: '환율', '나스닥 100'),
            "today": float | None,      # 가장 최근 종가
            "yesterday": float | None,  # 전일 종가 (없으면 None)
        }
    """
    info = OVERSEAS_INDEX_CODE_NAME_MAP.get(index_key)
    if not info:
        logger.error("[OVERSEAS_PERIOD] unknown index key=%s", index_key)
        return None

    fid_cond_mrkt_div_code = info["fid_cond_mrkt_div_code"]
    symbol = info["symbol"]

    today_d = date.today()
    start_d = today_d - timedelta(days=10)  # 여유 있게 10일치만 조회

    rows = fetch_overseas_index_period_series(
        fid_cond_mrkt_div_code=fid_cond_mrkt_div_code,
        fid_input_iscd=symbol,
        start_d=start_d,
        end_d=today_d,
        period_div_code="D",  # 일봉 기준
    )

    if not rows:
        logger.warning(
            "[OVERSEAS_PERIOD] no rows for key=%s symbol=%s",
            index_key,
            symbol,
        )
        return None

    # stck_bsop_date / ovrs_nmix_xxx 계열이 있을 거라 가정하고 날짜 기준 정렬 :contentReference[oaicite:4]{index=4}
    def _get_date(r: Dict[str, Any]) -> str:
        # 해외 기간별시세에서 사용되는 날짜 필드명 (문서 기준) :contentReference[oaicite:5]{index=5}
        return r.get("stck_bsop_date") or r.get("ovrs_bsop_date") or ""

    rows_sorted = sorted(rows, key=_get_date)

    today_row = rows_sorted[-1]
    yest_row = rows_sorted[-2] if len(rows_sorted) > 1 else None

    today_price = extract_overseas_index_daily_price(today_row)
    yesterday_price = (
        extract_overseas_index_daily_price(yest_row) if yest_row else None
    )

    if today_price is None:
        logger.warning(
            "[OVERSEAS_PERIOD] cannot extract today price for key=%s row=%s",
            index_key,
            today_row,
        )
        return None

    return {
        "name": info["name"],
        "today": today_price,
        "yesterday": yesterday_price,
    }

def fetch_overseas_index_intraday_series(
    fid_cond_mrkt_div_code: str,
    symbol: str,                      # 이미 정규화된 symbol ("NDX", "FX@KRW" 등)
    fid_hour_cls_code: str = "0",     # 0 정규장 / 1 시간외
    fid_pw_data_incu_yn: str = "Y",   # 과거 데이터 포함 여부
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    해외 지수 / 환율 / 해외종목 분봉 데이터 조회
    output1: 요약 정보
    output2: 분봉 리스트
    """

    path = "/uapi/overseas-price/v1/quotations/inquire-time-indexchartprice"
    tr_id = "FHKST03030200"

    params = {
        "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,   # N, X, KX, ...
        "FID_INPUT_ISCD": symbol,                           # NDX, FX@KRW 등
        "FID_HOUR_CLS_CODE": fid_hour_cls_code,
        "FID_PW_DATA_INCU_YN": fid_pw_data_incu_yn,
    }

    logger.debug("[OVERSEAS_INTRADAY] request params=%s", params)

    try:
        data = request_get(path, tr_id, params)
    except Exception as e:
        logger.error("[OVERSEAS_INTRADAY] request error: %s", e)
        return [], []

    logger.debug("[OVERSEAS_INTRADAY] raw response=%r", data)

    if data.get("rt_cd") != "0":  # 정상처리 여부
        logger.error(
            "[OVERSEAS_INTRADAY] KIS error - rt_cd=%s msg=%s",
            data.get("rt_cd"),
            data.get("msg1"),
        )
        return [], []

    output1 = data.get("output1") or []
    output2 = data.get("output2") or []

    if isinstance(output1, dict):
        output1 = [output1]
    if isinstance(output2, dict):
        output2 = [output2]

    return output1, output2


# --------------------------------------------------------------------
# key 기반 조회 (usdkrw / nasdaq100 등)
# --------------------------------------------------------------------
def fetch_overseas_index_intraday_by_key(
    index_key: str,
    fid_hour_cls_code: str = "0",
    fid_pw_data_incu_yn: str = "Y",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    meta = OVERSEAS_INDEX_CODE_NAME_MAP.get(index_key)
    if not meta:
        logger.error("[OVERSEAS_INTRADAY] invalid index_key=%s", index_key)
        return [], []

    return fetch_overseas_index_intraday_series(
        fid_cond_mrkt_div_code=meta["fid_cond_mrkt_div_code"],
        symbol=meta["symbol"],
        fid_hour_cls_code=fid_hour_cls_code,
        fid_pw_data_incu_yn=fid_pw_data_incu_yn,
    )