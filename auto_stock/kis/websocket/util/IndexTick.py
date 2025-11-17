from dataclasses import dataclass
from typing import Optional

@dataclass
class IndexTick:
    bstp_cls_code: str                         # 업종 구분 코드
    bsop_hour: str                             # 영업 시간 (HH:MM:SS)
    prpr_nmix: float                           # 현재가 지수
    prdy_vrss_sign: str                        # 전일 대비 부호
    bstp_nmix_prdy_vrss: float                 # 업종 지수 전일 대비
    acml_vol: Optional[int]                    # 누적 거래량
    acml_tr_pbmn: Optional[int]                # 누적 거래 대금
    pcas_vol: Optional[int]                    # 건별 거래량
    pcas_tr_pbmn: Optional[int]                # 건별 거래 대금
    prdy_ctrt: float                           # 전일 대비율
    oprc_nmix: Optional[float]                 # 시가 지수
    nmix_hgpr: Optional[float]                 # 지수 최고가
    nmix_lwpr: Optional[float]                 # 지수 최저가
    oprc_vrss_nmix_prpr: Optional[float]       # 시가 대비 지수 현재가
    oprc_vrss_nmix_sign: Optional[str]         # 시가 대비 지수 부호
    hgpr_vrss_nmix_prpr: Optional[float]       # 최고가 대비 지수 현재가
    hgpr_vrss_nmix_sign: Optional[str]         # 최고가 대비 지수 부호
    lwpr_vrss_nmix_prpr: Optional[float]       # 최저가 대비 지수 현재가
    lwpr_vrss_nmix_sign: Optional[str]         # 최저가 대비 지수 부호
    prdy_clpr_vrss_oprc_rate: Optional[float]  # 전일 종가 대비 시가2 비율
    prdy_clpr_vrss_hgpr_rate: Optional[float]  # 전일 종가 대비 최고가 비율
    prdy_clpr_vrss_lwpr_rate: Optional[float]  # 전일 종가 대비 최저가 비율
    uplm_issu_cnt: Optional[int]               # 상한 종목 수
    ascn_issu_cnt: Optional[int]               # 상승 종목 수
    stnr_issu_cnt: Optional[int]               # 보합 종목 수
    down_issu_cnt: Optional[int]               # 하락 종목 수
    lslm_issu_cnt: Optional[int]               # 하한 종목 수
    qtqt_ascn_issu_cnt: Optional[int]          # 기세 상승 종목 수
    qtqt_down_issu_cnt: Optional[int]          # 기세 하락 종목 수
    tick_vrss: Optional[int]                   # TICK 대비
    raw: str                                   # 원본 프레임 (디버깅용)
