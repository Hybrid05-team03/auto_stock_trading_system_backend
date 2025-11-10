from django.urls import path
from trading.views import rsi_trade_view

urlpatterns = [
    path('auto/<str:symbol>/', rsi_trade_view, name='rsi-trade'),
]