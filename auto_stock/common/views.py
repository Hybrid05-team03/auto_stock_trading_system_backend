from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers

class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()

class HealthCheckView(APIView):
    @swagger_auto_schema(
        operation_summary="Health Check",
        responses={200: HealthSerializer()}
    )
    def get(self, request):
        return Response({"status": "ok"})