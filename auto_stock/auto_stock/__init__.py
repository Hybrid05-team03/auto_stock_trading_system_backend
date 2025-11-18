import os
from pathlib import Path
from dotenv import load_dotenv

# 현재 파일: auto_stock/__init__.py
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"

load_dotenv(ENV_FILE)

from .celery import app as celery_app

__all__ = ("celery_app",)