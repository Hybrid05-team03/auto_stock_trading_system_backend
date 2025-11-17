from typing import Optional
import json
from datetime import datetime
from websocket import WebSocketTimeoutException, WebSocketConnectionClosedException
from .IndexTick import IndexTick

def _wait_for_index_frame(
    ws,
    index_code: str,
    expected_tr_id: str,
    raw_frame: Optional[str] = None,
) -> Optional[IndexTick]:
    try:
        if raw_frame is None:
            frame = ws.recv()
        else:
            frame = raw_frame
    except (WebSocketTimeoutException, WebSocketConnectionClosedException) as e:
        print(f"[WS-INDEX] recv error: {e}")
        return None
    except Exception as e:
        print(f"[WS-INDEX] unknown recv error: {e}")
        return None

    if not frame:
        return None

    if "|" in frame and frame[0].isdigit():
        try:
            head, trid, cnt, body = frame.split("|", 3)
        except ValueError:
            return None

        if trid != expected_tr_id:
            return None

        fields = body.split("^")
        if len(fields) < 30:
            return None

        def to_float(v):
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

        def to_int(v):
            try:
                return int(v)
            except (ValueError, TypeError):
                return None

        bstp_cls_code = fields[0]

        # ✅ 구독한 index_code 와 실제 코드 비교
        if bstp_cls_code != index_code:
            return None


        ### ------------  Body 필드 매핑



        bsop_hour_raw          = fields[1]
        prpr_nmix              = to_float(fields[2])
        prdy_vrss_sign         = fields[3]
        bstp_nmix_prdy_vrss    = to_float(fields[4])
        prdy_ctrt              = to_float(fields[5])
        acml_vol               = to_int(fields[6])
        acml_tr_pbmn           = to_int(fields[7])
        pcas_vol               = to_int(fields[8])
        pcas_tr_pbmn           = to_int(fields[9])
        oprc_nmix              = to_float(fields[10])
        nmix_hgpr              = to_float(fields[11])
        nmix_lwpr              = to_float(fields[12])
        oprc_vrss_nmix_prpr    = to_float(fields[13])
        oprc_vrss_nmix_sign    = fields[14]
        hgpr_vrss_nmix_prpr    = to_float(fields[15])
        hgpr_vrss_nmix_sign    = fields[16]
        lwpr_vrss_nmix_prpr    = to_float(fields[17])
        lwpr_vrss_nmix_sign    = fields[18]
        prdy_clpr_vrss_oprc_rate = to_float(fields[19])
        prdy_clpr_vrss_hgpr_rate = to_float(fields[20])
        prdy_clpr_vrss_lwpr_rate = to_float(fields[21])
        uplm_issu_cnt          = to_int(fields[22])
        ascn_issu_cnt          = to_int(fields[23])
        stnr_issu_cnt          = to_int(fields[24])
        down_issu_cnt          = to_int(fields[25])
        lslm_issu_cnt          = to_int(fields[26])
        qtqt_ascn_issu_cnt     = to_int(fields[27])
        qtqt_down_issu_cnt     = to_int(fields[28])
        tick_vrss              = to_int(fields[29])

        if len(bsop_hour_raw) >= 6:
            hh, mm, ss = bsop_hour_raw[0:2], bsop_hour_raw[2:4], bsop_hour_raw[4:6]
            bsop_hour = f"{hh}:{mm}:{ss}"
        else:
            bsop_hour = bsop_hour_raw

        if prpr_nmix is None:
            return None

        return IndexTick(
            bstp_cls_code=bstp_cls_code,
            bsop_hour=bsop_hour,
            prpr_nmix=prpr_nmix,
            prdy_vrss_sign=prdy_vrss_sign,
            bstp_nmix_prdy_vrss=bstp_nmix_prdy_vrss or 0.0,
            acml_vol=acml_vol,
            acml_tr_pbmn=acml_tr_pbmn,
            pcas_vol=pcas_vol,
            pcas_tr_pbmn=pcas_tr_pbmn,
            prdy_ctrt=prdy_ctrt or 0.0,
            oprc_nmix=oprc_nmix,
            nmix_hgpr=nmix_hgpr,
            nmix_lwpr=nmix_lwpr,
            oprc_vrss_nmix_prpr=oprc_vrss_nmix_prpr,
            oprc_vrss_nmix_sign=oprc_vrss_nmix_sign,
            hgpr_vrss_nmix_prpr=hgpr_vrss_nmix_prpr,
            hgpr_vrss_nmix_sign=hgpr_vrss_nmix_sign,
            lwpr_vrss_nmix_prpr=lwpr_vrss_nmix_prpr,
            lwpr_vrss_nmix_sign=lwpr_vrss_nmix_sign,
            prdy_clpr_vrss_oprc_rate=prdy_clpr_vrss_oprc_rate,
            prdy_clpr_vrss_hgpr_rate=prdy_clpr_vrss_hgpr_rate,
            prdy_clpr_vrss_lwpr_rate=prdy_clpr_vrss_lwpr_rate,
            uplm_issu_cnt=uplm_issu_cnt,
            ascn_issu_cnt=ascn_issu_cnt,
            stnr_issu_cnt=stnr_issu_cnt,
            down_issu_cnt=down_issu_cnt,
            lslm_issu_cnt=lslm_issu_cnt,
            qtqt_ascn_issu_cnt=qtqt_ascn_issu_cnt,
            qtqt_down_issu_cnt=qtqt_down_issu_cnt,
            tick_vrss=tick_vrss,
            raw=frame,
        )

    frame_stripped = frame.strip()
    if frame_stripped.startswith("{"):
        try:
            data = json.loads(frame_stripped)
        except json.JSONDecodeError as e:
            print(f"[WS-INDEX] JSON decode error: {e} frame={frame_stripped!r}")
            return None
        return None

    return None
