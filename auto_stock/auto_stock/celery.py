import os
from celery import Celery
from dotenv import load_dotenv


# .env 자동 로딩
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

## django settings.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auto_stock.settings")
## celery 앱 name
app = Celery("auto_stock")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "start-websocket-manager-once": {
        "task": "tmp.websocket.manage.ws_connect.start_ws_manager",
        "schedule": 10.0,
        "options": {"queue": "websocket"},
    }
}

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")