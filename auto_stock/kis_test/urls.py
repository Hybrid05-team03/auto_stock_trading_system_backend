from django.urls import path

from .views import RealtimeQuoteView, DailyPriceView, TokenStatusView


urlpatterns = [
    # this urls are included under the prefix: /api/kis-test/
    path("quotes/", RealtimeQuoteView.as_view(), name="kis-realtime-quotes"), # OK
    path("daily/", DailyPriceView.as_view(), name="kis-daily-price"),
    path("token/", TokenStatusView.as_view(), name="kis-auth-token-status"),
]