from django.urls import path
from .views import indices_realtime_view, indices_view

urlpatterns = [
    # this file is included under the prefix: /api/market/
    path("indices/", indices_view, name="market-indices"),
    path("indices/realtime/", indices_realtime_view, name="market-indices-realtime"),
]
