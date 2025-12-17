from django.urls import re_path
from .consumers import IndicesConsumer

websocket_urlpatterns = [
    re_path(r'ws/index/$', IndicesConsumer.as_asgi()),
]
