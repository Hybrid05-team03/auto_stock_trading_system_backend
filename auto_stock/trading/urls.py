from django.urls import path
from trading import views

urlpatterns = [
    # 테스트용
    path('rsi/<str:symbol>/', views.rsi_trade_view, name='rsi-vaule'),
    # 자동 주문 요청
    path('auto/<str:symbol>/', views.start_auto_trading, name='rsi-auto-trade'),
]