from django.db import models


class OrderRequest(models.Model):
    symbol = models.CharField(max_length=20)
    quantity = models.IntegerField()
    strategy = models.CharField(max_length=20)
    risk = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_request"