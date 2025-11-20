from django.urls import path

from kis_test import views


urlpatterns = [
    # this urls are included under the prefix: /api/kis-test/
    path("price/", views.RealtimeQuoteView.as_view(), name="kis-realtime-quotes"), # websocket (OK)
    path("daily/", views.DailyPriceView.as_view(), name="kis-daily-price"),        # restapi   (OK)
    path("token/", views.TokenStatusView.as_view(), name="kis-auth-token-status"), # restapi   (OK)
    path("index/", views.RealtimeIndexView.as_view(), name="kis-index"),           # websocket (..)
    path("rank/", views.PopularStockRankingView.as_view(), name="kis-rank"),       # websocket (..)
]