from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RealtimeSymbol
from .serializers import RealtimeSymbolSerializer
from .services import ensure_symbols_registered, fetch_realtime_quotes


class RealtimeSymbolView(APIView):
    """
    Manage persisted realtime symbols (identifier/code/name triples).
    """

    def get(self, request):
        serializer = RealtimeSymbolSerializer(RealtimeSymbol.objects.all(), many=True)
        return Response({"symbols": serializer.data})

    def post(self, request):
        serializer = RealtimeSymbolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        obj, created = RealtimeSymbol.objects.update_or_create(
            identifier=payload["identifier"],
            defaults={"code": payload["code"], "name": payload.get("name", "")},
        )
        response_serializer = RealtimeSymbolSerializer(obj)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(response_serializer.data, status=status_code)


class RealtimeQuoteView(APIView):
    """
    Lightweight proxy for requesting realtime quotes via websocket.
    """

    def get(self, request):
        targets = {}

        raw_codes = request.query_params.get("codes", "")
        codes = [code.strip() for code in raw_codes.split(",") if code.strip()]
        if codes:
            ensure_symbols_registered(codes)
            for record in RealtimeSymbol.objects.filter(identifier__in=codes):
                targets[record.identifier] = {
                    "code": record.code,
                    "name": record.name or record.identifier,
                }

        raw_symbols = request.query_params.get("symbols", "")
        identifiers = [identifier.strip() for identifier in raw_symbols.split(",") if identifier.strip()]

        symbol_qs = None
        if identifiers:
            symbol_qs = RealtimeSymbol.objects.filter(identifier__in=identifiers)
        elif not codes:
            symbol_qs = RealtimeSymbol.objects.all()

        if symbol_qs is not None:
            for record in symbol_qs:
                targets[record.identifier] = {
                    "code": record.code,
                    "name": record.name or record.identifier,
                }

        if not targets:
            return Response(
                {"detail": "Provide 'codes' query params or register symbols first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            quotes = fetch_realtime_quotes(targets)
        except Exception as exc:
            return Response(
                {"detail": f"Failed to fetch realtime quotes: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"quotes": quotes})
