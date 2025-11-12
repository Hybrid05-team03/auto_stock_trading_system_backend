from rest_framework import serializers

from .models import RealtimeSymbol


class RealtimeSymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealtimeSymbol
        fields = ["id", "identifier", "code", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
