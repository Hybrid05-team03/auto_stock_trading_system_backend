# routing.py
from django.urls import re_path
from .consumers import IndicesConsumer, RankConsumer, StockPriceConsumer

websocket_urlpatterns = [
    re_path(r'ws/index/$', IndicesConsumer.as_asgi()),    # IndicesConsumer
    re_path(r'ws/rank/$', RankConsumer.as_asgi()),        # RankConsumer
    re_path(r'ws/price/$', StockPriceConsumer.as_asgi()), # StockPriceConsumer
]