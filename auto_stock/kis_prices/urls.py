from django.urls import path

from .views import DailyPriceView

urlpatterns = [
    path("daily/", DailyPriceView.as_view(), name="kis-daily-price"),
]
