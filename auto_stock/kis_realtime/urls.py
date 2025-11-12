from django.urls import path

from .views import RealtimeQuoteView, RealtimeSymbolView

urlpatterns = [
    path("symbols/", RealtimeSymbolView.as_view(), name="kis-realtime-symbols"),
    path("quotes/", RealtimeQuoteView.as_view(), name="kis-realtime-quotes"),
]
