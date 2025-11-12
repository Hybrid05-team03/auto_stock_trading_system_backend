from django.urls import path

from .views import TokenStatusView

urlpatterns = [
    path("token/", TokenStatusView.as_view(), name="kis-auth-token-status"),
]
