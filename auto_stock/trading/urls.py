from django.urls import path
from trading. views import rsi_trade_view, start_auto_trading

urlpatterns = [
    path('rsi/<str:symbol>/', rsi_trade_view, name='rsi-vaule'), # 테스트용
    path('auto/<str:symbol>/', start_auto_trading, name='rsi-auto-trade'),
]