from django.db import models

from trading.constants.trading_status import ORDER_STATUS, ORDER_EXECUTION_SIDE

## 주문 요청 테이블
class OrderRequest(models.Model):
    symbol = models.CharField(max_length=20)
    quantity = models.IntegerField() # 매수 수량
    target_profit = models.IntegerField(null=True)  # 목표 수익률
    strategy = models.CharField(max_length=20)
    risk = models.CharField(max_length=10)

    status = models.CharField(
        max_length=20,
        choices=[(s, s) for s in ORDER_STATUS], ## 상태값 제한
        default='PENDING'
    )

    kis_order_id = models.CharField(max_length=20, null=True)
    kis_message = models.CharField(max_length=200, null=True)

    buy_requested_at = models.DateTimeField(null=True) # KIS 매수 요청 시간
    sell_requested_at = models.DateTimeField(null=True) # KIS 매도 요청 시간
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "order_request"


## 매매 기록
class OrderExecution(models.Model):
    order_request = models.ForeignKey(OrderRequest, on_delete=models.CASCADE)

    side = models.CharField(
        max_length=10,
        choices=[(s, s) for s in ORDER_EXECUTION_SIDE]
    )

    executed_price = models.IntegerField(null=True) # 체결가
    executed_qty = models.IntegerField() # 체결 수량
    executed_at = models.DateTimeField() # 체결 시간

    class Meta:
        db_table = "order_execution"