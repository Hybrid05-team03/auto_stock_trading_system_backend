from django.urls import path

from .views import RealtimeSymbolView, RealtimeQuoteView, DailyPriceView, TokenStatusView, IndexView


urlpatterns = [
    # this urls are included under the prefix: /api/kis-test/
    path("symbols/", RealtimeSymbolView.as_view(), name="kis-realtime-symbols"),
    path("quotes/", RealtimeQuoteView.as_view(), name="kis-realtime-quotes"),
    path("daily/", DailyPriceView.as_view(), name="kis-daily-price"),
    path("token/", TokenStatusView.as_view(), name="kis-auth-token-status"),
    path("stock/", IndexView.as_view(), name="kis-index"),
]