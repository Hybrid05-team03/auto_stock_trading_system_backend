# kis/websocket/parser/index_parser.py

import logging
from kis.constants.const_index import INDEX_CODE_NAME_MAP

logger = logging.getLogger(__name__)

def parse_index(raw: str) -> dict | None:
    if "|" not in raw or not raw[0].isdigit():
        return None

    try:
        _, _, _, body = raw.split("|", 3)
        fields = body.split("^")
        if len(fields) < 30:
            return None

        code = fields[0]
        time_str = fields[1]
        price_str = fields[2]

        price = float(price_str)
        timestamp = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}" if len(time_str) >= 6 else time_str

        return {
            "code": code,
            "name": INDEX_CODE_NAME_MAP.get(code, code),
            "price": price,
            "timestamp": timestamp
        }

    except Exception as e:
        logger.warning(f"[parse_index] error: {e}")
        return None