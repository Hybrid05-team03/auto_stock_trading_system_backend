# trading/urls.py
from django.urls import path
from trading.views import RSIView

urlpatterns = [
    path('rsi/', RSIView.as_view(), name='rsi-view'),
]