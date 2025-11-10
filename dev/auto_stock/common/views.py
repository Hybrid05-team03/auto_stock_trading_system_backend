# common/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers

from indices.services import get_indices_payload

class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()

class HealthCheckView(APIView):
    @swagger_auto_schema(operation_summary="Health Check", responses={200: HealthSerializer()})
    def get(self, request):
        return Response({"status": "ok"})

class IndexDataPointSerializer(serializers.Serializer):
    date = serializers.CharField()
    value = serializers.FloatField()

class IndexSeriesSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    data = IndexDataPointSerializer(many=True)

class IndicesResponseSerializer(serializers.Serializer):
    indices = IndexSeriesSerializer(many=True)

class MarketIndicesView(APIView):
    @swagger_auto_schema(operation_summary="Market indices (real data via KIS)", responses={200: IndicesResponseSerializer()})
    def get(self, request):
        payload = get_indices_payload()
        return Response(payload)
