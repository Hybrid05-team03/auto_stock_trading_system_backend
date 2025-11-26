from django.db import models
from trading.constants.trading_status import ORDER_REQUEST_STATUS


class OrderRequest(models.Model):
    symbol = models.CharField(max_length=20)
    quantity = models.IntegerField()
    strategy = models.CharField(max_length=20)
    risk = models.CharField(max_length=10)
    status = models.CharField(
        max_length=20,
        choices=[(s, s) for s in ORDER_REQUEST_STATUS], ## 상태값 제한
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_request"