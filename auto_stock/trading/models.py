from django.db import models

from trading.constants.trading_status import ORDER_STATUS, ORDER_EXECUTION_SIDE

## 주문 요청 테이블
class OrderRequest(models.Model):
    symbol = models.CharField(max_length=20)
    quantity = models.IntegerField() # 매수 수량
    target_profit = models.IntegerField(null=True)  # 목표 수익률
    target_price = models.IntegerField(null=True)  # 목표 수익금
    strategy = models.CharField(max_length=20)
    risk = models.CharField(max_length=10)

    status = models.CharField(
        max_length=50,
        choices=[(s, s) for s in ORDER_STATUS], ## 상태값 제한
        default='PENDING'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "order_request"


## 매매 기록
class OrderExecution(models.Model):
    order_request = models.ForeignKey(OrderRequest, on_delete=models.CASCADE)

    kis_order_id = models.CharField(max_length=100, null=True) # KIS 주문 체결 번호
    kis_message = models.CharField(max_length=200, null=True) # KIS 주문 체결 메시지
    executed_side = models.CharField(
        max_length=10,
        choices=[(s, s) for s in ORDER_EXECUTION_SIDE]
    )
    executed_price = models.IntegerField(null=True) # 체결가
    executed_quantity = models.IntegerField(null=True) # 체결 수량
    executed_at = models.DateTimeField(null=True) # 체결 시간

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "order_execution"