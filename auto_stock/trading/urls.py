from django.urls import path

from trading import views


urlpatterns = [
    # this urls are included under the prefix: /api/trading/
    # 자동 매매
    path('request/', views.AutoOrderCreateView.as_view(), name='request-auto-trading'),

    # 수동 매매
    path('buy/', views.ManualBuyView.as_view(), name='manual-buy'),
    path('sell/', views.ManualSellView.as_view(), name='manual-sell'),
]