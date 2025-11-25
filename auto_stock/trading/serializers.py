from rest_framework import serializers
from .models import OrderRequest


class OrderRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderRequest
        fields = ["symbol", "quantity", "strategy", "risk"]