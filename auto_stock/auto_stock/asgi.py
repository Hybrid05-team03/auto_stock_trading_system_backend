"""
ASGI config for auto_stock project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

# .env 자동 로딩
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auto_stock.settings')

application = get_asgi_application()
