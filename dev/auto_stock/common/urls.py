from django.urls import path
from .views import HealthCheckView, MarketIndicesView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('market/indices/', MarketIndicesView.as_view(), name='market-indices'),
]
