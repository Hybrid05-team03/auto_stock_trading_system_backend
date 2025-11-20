# # auto_stock/indices/views.py
# import logging
#
# from django.http import JsonResponse
# from drf_yasg.utils import swagger_auto_schema
#
# from rest_framework import status, serializers
# from rest_framework.decorators import api_view, renderer_classes
# from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
# from rest_framework.response import Response
#
# from .services import get_indices_payload, get_indices_realtime_payload
#
#
# logger = logging.getLogger(__name__)
#
# def indices_view(request):
#     payload = get_indices_payload()
#     # 한글 깨짐 방지: ensure_ascii=False
#     return JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
#
# # --- DRF Browsable API version (overrides the plain JsonResponse view) --
#
# class IndexDataPointSerializer(serializers.Serializer):
#     date = serializers.CharField()
#     value = serializers.FloatField()
#
#
# class IndexSeriesSerializer(serializers.Serializer):
#     id = serializers.CharField()
#     name = serializers.CharField()
#     data = IndexDataPointSerializer(many=True)
#
#
# class IndicesResponseSerializer(serializers.Serializer):
#     indices = IndexSeriesSerializer(many=True)
#
#
# class IndexQuoteSerializer(serializers.Serializer):
#     id = serializers.CharField()
#     name = serializers.CharField()
#     price = serializers.FloatField(allow_null=True)
#     timestamp = serializers.CharField(allow_null=True)
#
#
# class IndicesRealtimeResponseSerializer(serializers.Serializer):
#     quotes = IndexQuoteSerializer(many=True)
#
#
# @swagger_auto_schema(
#     method='get',
#     operation_summary="Market indices (KIS/ETF based)",
#     responses={200: IndicesResponseSerializer()}
# )
# @api_view(["GET"])
# @renderer_classes([JSONRenderer, BrowsableAPIRenderer])
# def indices_view(request):
#     payload = get_indices_payload()
#     return Response(payload)
#
#
# @swagger_auto_schema(
#     method='get',
#     operation_summary="Market indices realtime quotes (KIS WebSocket)",
#     responses={200: IndicesRealtimeResponseSerializer()}
# )
# @api_view(["GET"])
# @renderer_classes([JSONRenderer, BrowsableAPIRenderer])
# def indices_realtime_view(request):
#     try:
#         payload = get_indices_realtime_payload(request)
#     except Exception as exc:
#         logger.exception("Failed to fetch realtime indices: %s", exc)
#         return Response(
#             {"detail": "Failed to fetch realtime quotes."},
#             status=status.HTTP_502_BAD_GATEWAY,
#         )
#     return Response(payload)
