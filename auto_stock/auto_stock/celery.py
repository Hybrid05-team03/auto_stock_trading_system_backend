import os
from dotenv import load_dotenv

from celery import Celery
from celery.schedules import crontab

# .env 자동 로딩
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

## django settings.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auto_stock.settings")

app = Celery("auto_stock")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# 미체결 주문건 재주문 태스크
CELERY_BEAT_SCHEDULE = {
    "retry-unfilled-sells-every-morning": {
        "task": "trading.tasks.retry_unfilled_sells",
        "schedule": crontab(hour=9, minute=1),  # 오전 9시 1분 정기 실행
    },
}