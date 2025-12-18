from dotenv import load_dotenv

load_dotenv()

from .celery import app as celery_app

__all__ = ("celery_app",)