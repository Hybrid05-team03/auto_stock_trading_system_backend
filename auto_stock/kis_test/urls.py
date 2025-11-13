from django.urls import path

from .views import RealtimeSymbolView, RealtimeQuoteView, DailyPriceView, TokenStatusView

urlpatterns = [
    path("symbols/", RealtimeSymbolView.as_view(), name="kis-realtime-symbols"),
    path("quotes/", RealtimeQuoteView.as_view(), name="kis-realtime-quotes"), # 테스트 필요 
    path("daily/", DailyPriceView.as_view(), name="kis-daily-price"),
    path("token/", TokenStatusView.as_view(), name="kis-auth-token-status"),
]