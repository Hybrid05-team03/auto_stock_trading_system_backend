from datetime import datetime, time, timedelta, timezone

KST = timezone(timedelta(hours=9))

def is_after_market_close(now: datetime | None = None) -> bool:
    if now is None:
        now = datetime.now(KST)
        # 장 마감된 경우 
        if now.time() >= time(15, 20) or now.time() <= time(9, 10): 
            return False # 15:20 ~ 09:10 
    # 장 열린 경우 
    return True
