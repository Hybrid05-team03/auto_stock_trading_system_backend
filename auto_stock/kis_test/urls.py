from django.urls import path

from .views import RealtimeQuoteView, DailyPriceView, TokenStatusView

urlpatterns = [
    path("quotes/", RealtimeQuoteView.as_view(), name="kis-realtime-quotes"),
    path("daily/", DailyPriceView.as_view(), name="kis-daily-price"),
    path("token/", TokenStatusView.as_view(), name="kis-auth-token-status"),
]