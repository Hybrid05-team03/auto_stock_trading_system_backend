# auto_stock/indices/views.py
from django.http import JsonResponse
from .services import get_indices_payload

def indices_view(request):
    payload = get_indices_payload()
    # 한글 깨짐 방지: ensure_ascii=False
    return JsonResponse(payload, json_dumps_params={"ensure_ascii": False})


# --- DRF Browsable API version (overrides the plain JsonResponse view) ---
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers


class IndexDataPointSerializer(serializers.Serializer):
    date = serializers.CharField()
    value = serializers.FloatField()


class IndexSeriesSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    data = IndexDataPointSerializer(many=True)


class IndicesResponseSerializer(serializers.Serializer):
    indices = IndexSeriesSerializer(many=True)


@swagger_auto_schema(
    method='get',
    operation_summary="Market indices (KIS/ETF based)",
    responses={200: IndicesResponseSerializer()}
)
@api_view(["GET"])
@renderer_classes([JSONRenderer, BrowsableAPIRenderer])
def indices_view(request):
    payload = get_indices_payload()
    return Response(payload)