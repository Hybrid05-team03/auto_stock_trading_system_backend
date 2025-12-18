import os
from dotenv import load_dotenv

from celery import Celery
from celery.schedules import crontab

# .env 자동 로딩
load_dotenv()

## django settings.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auto_stock.settings")

app = Celery("auto_stock")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# 미체결 주문건 재주문 스케줄 등록
app.conf.beat_schedule = {
    "retry-pending-tradings-per-1min": {
        "task": "trading.tasks.auto_re_order.retry_unfilled_sells_chain",
        "schedule": 60, # execute per 1min
    }
}