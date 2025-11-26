# kis/api/util/overseas_index.py

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _to_float(val: Any) -> Optional[float]:
    if val in (None, ""):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        logger.debug("[OVERSEAS] cannot convert to float: %r", val)
        return None


def extract_overseas_index_daily_price(row: Dict[str, Any]) -> Optional[float]:
    """
    해외 기간별시세(일/주/월/년) 1개 row에서 '종가'에 해당하는 값을 추출.

    문서 기준으로 종가 후보 필드들:
      - ovrs_nmix_clpr : 지수 종가
      - ovrs_nmix_prpr : 현재가/지수값 (일봉일 경우 종가와 같을 수 있음)
    실제 응답 구조에 맞게 우선순위를 두고 파싱한다. :contentReference[oaicite:6]{index=6}
    """
    if not row:
        return None

    # 우선 종가 전용 필드 시도
    for key in ("ovrs_nmix_clpr", "ovrs_nmix_prpr"):
        price = _to_float(row.get(key))
        if price is not None:
            return price

    return None
