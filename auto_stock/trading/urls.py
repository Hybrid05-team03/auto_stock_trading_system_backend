from django.urls import path

from trading import views


urlpatterns = [
    # this urls are included under the prefix: /api/trading/
    # 자동 매매
    path('request/', views.AutoOrderCreateView.as_view(), name='request-auto-trading'),

    # 수동 매수
    path('buy/', views.ManualBuyView.as_view(), name='manual-buy'),
    # 수동 매도
    path('sell/', views.ManualSellView.as_view(), name='manual-sell'),
    # 주문 취소
    path('cancel/', views.OrderCancelView.as_view(), name='order-cancel'),


    # 매수 가능 여부 조회
    path("psl-buy/", views.IsPossibleBuyView.as_view(), name="is-possible-buy"),
    # 매도 가능 여부 조회
    path("psl-sell/", views.IsPossibleSellView.as_view(), name="is-possible-sell"),
]