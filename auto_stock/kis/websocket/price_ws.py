from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests
from kis.auth.kis_auth import APP_KEY, APP_SECRET, BASE_URL
from kis.api.price import get_daily_price_payload

try:
    from websocket import (
        WebSocketConnectionClosedException,
        WebSocketTimeoutException,
        create_connection,
    )
    _WEBSOCKET_IMPORT_ERROR = None
except ImportError as exc:  # pragma: no cover - optional dependency
    WebSocketConnectionClosedException = WebSocketTimeoutException = Exception
    create_connection = None
    _WEBSOCKET_IMPORT_ERROR = exc

from kis_realtime.models import RealtimeSymbol

logger = logging.getLogger(__name__)


def _env_float(key: str, default: str) -> float:
    try:
        return float(os.getenv(key, default))
    except ValueError:
        return float(default)


def _env_int(key: str, default: str) -> int:
    try:
        return int(os.getenv(key, default))
    except ValueError:
        return int(default)


_WS_ENDPOINT = os.getenv("KIS_WS_ENDPOINT")
_WS_BASE_URL = os.getenv("KIS_WS_BASE_URL", "ws://ops.koreainvestment.com:31000")
_REALTIME_TR_ID = os.getenv("KIS_REALTIME_TR_ID", "H0STCNT0")
_WS_CONNECT_TIMEOUT = _env_float("INDICES_WS_CONNECT_TIMEOUT", "5")
_WS_MESSAGE_TIMEOUT = _env_float("INDICES_WS_MESSAGE_TIMEOUT", "3")
_WS_HTTP_TIMEOUT = _env_float("INDICES_WS_HTTP_TIMEOUT", "5")
_WS_SYMBOL_DELAY = _env_float("INDICES_WS_SYMBOL_DELAY", "0")
_WS_CUST_TYPE = os.getenv("KIS_WS_CUSTOMER_TYPE", "P")
_APPROVAL_TTL = _env_int("KIS_APPROVAL_TTL_SECONDS", "600")
_APPROVAL_STATE = {"key": None, "expires_at": 0.0}
_KST = timezone(timedelta(hours=9))
_DOMESTIC_REALTIME_FIELD_COUNT = 46


def _get_ws_url(tr_id: Optional[str] = None) -> str:
    if _WS_ENDPOINT:
        return _WS_ENDPOINT
    target = tr_id or _REALTIME_TR_ID
    base = _WS_BASE_URL.rstrip("/")
    return f"{base}/tryitout/{target}"

# key, secret 확인
def _ensure_kis_credentials():
    if not APP_KEY or not APP_SECRET:
        raise RuntimeError("KIS_APP_KEY and KIS_APP_SECRET must be configured for websocket streaming.")


# WebSocket approval key 발급
def _fetch_ws_approval_key() -> str:
    _ensure_kis_credentials()
    url = f"{BASE_URL}/oauth2/Approval"
    payload = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": APP_SECRET,
    }
    response = requests.post(url, json=payload, timeout=_WS_HTTP_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    approval_key = data.get("approval_key") or data.get("approvalKey")
    if not approval_key:
        raise RuntimeError("KIS websocket approval key missing in response.")
    _APPROVAL_STATE["key"] = approval_key
    _APPROVAL_STATE["expires_at"] = time.time() + _APPROVAL_TTL
    return approval_key


# WS approval 키 가져오기
def _get_ws_approval_key() -> str:
    cached = _APPROVAL_STATE.get("key")
    if cached and time.time() < _APPROVAL_STATE.get("expires_at", 0):
        return cached
    return _fetch_ws_approval_key()


#
def _safe_float(value: Optional[str]) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _chunk_realtime_rows(body: str, tr_id: str, count: int) -> list[list[str]]:
    parts = body.split("^")
    if parts and parts[-1] == "":
        parts = parts[:-1]
    if not parts:
        return []

    chunk_size = None
    if tr_id == "H0STCNT0":
        chunk_size = _DOMESTIC_REALTIME_FIELD_COUNT

    if not chunk_size:
        if count <= 0:
            count = 1
        chunk_size = max(len(parts) // count, 1)
    elif len(parts) % chunk_size != 0 and count > 0:
        chunk_size = max(len(parts) // count, 1)

    rows = []
    for i in range(0, len(parts), chunk_size):
        rows.append(parts[i : i + chunk_size])
    return rows

# time stamp
def _compose_kst_timestamp(date_str: Optional[str], time_str: Optional[str]) -> Optional[str]:
    if not date_str or not time_str:
        return None
    try:
        base = datetime.strptime(f"{date_str}{time_str[:6]}", "%Y%m%d%H%M%S")
    except ValueError:
        return None
    return base.replace(tzinfo=_KST).isoformat()


def _parse_event_payload(raw: str, expected_tr_id: str, code: str) -> Optional[Dict[str, Optional[float]]]:
    try:
        encrypted_flag, tr_id, count_str, body = raw.split("|", 3)
    except ValueError:
        return None
    if tr_id != expected_tr_id:
        return None
    if encrypted_flag == "1":
        logger.warning("Encrypted websocket payload received for %s; ignoring.", tr_id)
        return None
    try:
        count = int(count_str)
    except ValueError:
        count = 1
    for row in _chunk_realtime_rows(body, tr_id, count or 1):
        if not row:
            continue
        symbol = row[0]
        if symbol and symbol != code:
            continue
        price = _safe_float(row[2] if len(row) > 2 else None)
        if price is None:
            continue
        timestamp = _compose_kst_timestamp(row[33] if len(row) > 33 else "", row[1] if len(row) > 1 else "")
        return {"price": price, "timestamp": timestamp}
    return None


def _send_subscription(ws, approval_key: str, tr_id: str, code: str, tr_type: str):
    message = {
        "header": {
            "approval_key": approval_key,
            "custtype": _WS_CUST_TYPE,
            "tr_type": tr_type,
            "content-type": "utf-8",
        },
        "body": {
            "input": {
                "tr_id": tr_id,
                "tr_key": code,
            }
        },
    }
    ws.send(json.dumps(message))


def _wait_for_trade_frame(ws, code: str, tr_id: str) -> Optional[Dict[str, Any]]:
    deadline = time.time() + _WS_MESSAGE_TIMEOUT
    while time.time() < deadline:
        remaining = max(deadline - time.time(), 0.1)
        try:
            ws.settimeout(remaining)
            raw = ws.recv()
        except (WebSocketTimeoutException, WebSocketConnectionClosedException):
            return None
        if not raw:
            continue
        if raw[0] in ("0", "1") and raw.count("|") >= 3:
            event = _parse_event_payload(raw, tr_id, code)
            if event:
                return event
            logger.debug("Websocket event payload could not be parsed for %s: %s", code, raw)
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            logger.debug("Invalid websocket payload for %s: %s", code, raw)
            continue
        header = payload.get("header", {})
        payload_tr_id = header.get("tr_id")
        if payload_tr_id == "PINGPONG":
            try:
                ws.send(raw)
            except Exception:
                logger.debug("Failed to acknowledge websocket ping.")
            continue
        output = payload.get("body", {}).get("output")
        if not isinstance(output, dict):
            continue
        payload_code = output.get("tr_key") or output.get("shrn_iscd")
        if payload_code and payload_code != code:
            continue
        price = _safe_float(output.get("stck_prpr"))
        if price is None:
            continue
        timestamp = output.get("gen_time") or datetime.utcnow().isoformat() + "Z"
        return {"price": price, "timestamp": timestamp}
    return None


def fetch_realtime_quotes(
    targets: Dict[str, Dict[str, str]],
    tr_id: Optional[str] = None,
) -> list[Dict[str, Any]]:
    """
    Iterate through the provided targets and fetch the latest realtime price snapshot.
    """
    if not targets:
        return []
    if create_connection is None:
        raise RuntimeError(
            "websocket-client is required for realtime streaming."
        ) from _WEBSOCKET_IMPORT_ERROR
    approval_key = _get_ws_approval_key()
    ws = None
    quotes = []
    resolved_tr_id = tr_id or _REALTIME_TR_ID
    try:
        ws = create_connection(_get_ws_url(resolved_tr_id), timeout=_WS_CONNECT_TIMEOUT)
        for symbol_id, meta in targets.items():
            code = meta.get("code")
            if not code:
                continue
            try:
                _send_subscription(ws, approval_key, resolved_tr_id, code, tr_type="1")
                result = _wait_for_trade_frame(ws, code, resolved_tr_id)
            except Exception as exc:
                logger.warning("Realtime quote fetch failed for %s: %s", code, exc)
                result = None
            finally:
                try:
                    _send_subscription(ws, approval_key, resolved_tr_id, code, tr_type="2")
                except Exception:
                    pass
            quotes.append(
                {
                    "id": symbol_id,
                    "name": meta.get("name", symbol_id),
                    "price": result["price"] if result else None,
                    "timestamp": result["timestamp"] if result else None,
                }
            )
            if _WS_SYMBOL_DELAY > 0:
                time.sleep(_WS_SYMBOL_DELAY)
    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
    return quotes


def _lookup_symbol_name(code: str) -> Optional[str]:
    """
    Use the daily price API metadata to resolve a human-friendly name.
    """
    try:
        payload = get_daily_price_payload(code)
    except Exception as exc:
        logger.warning("Failed to fetch metadata for %s: %s", code, exc)
        return None
    rows = payload.get("output1") or []
    if isinstance(rows, dict):
        rows = [rows]
    for row in rows:
        name = row.get("hts_kor_isnm") or row.get("hts_kor_iscd") or row.get("hts_kor_isnm")
        if name:
            return name
    return None


def ensure_symbols_registered(codes: List[str]) -> None:
    """
    Persist identifiers for any codes that are not already saved.
    """
    normalized = [code.strip() for code in codes if code and code.strip()]
    if not normalized:
        return
    existing = set(
        RealtimeSymbol.objects.filter(identifier__in=normalized).values_list("identifier", flat=True)
    )
    missing = [code for code in normalized if code not in existing]
    if not missing:
        return
    for code in missing:
        name = _lookup_symbol_name(code) or code
        RealtimeSymbol.objects.update_or_create(
            identifier=code,
            defaults={"code": code, "name": name},
        )
