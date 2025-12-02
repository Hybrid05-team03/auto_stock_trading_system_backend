from django.db import models


class RealtimeSymbol(models.Model):
    """
    Persist user-defined symbol metadata for realtime streaming.
    """

    identifier = models.CharField(max_length=64, unique=True)
    code = models.CharField(max_length=16)
    name = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["identifier"]

    def __str__(self) -> str:  # pragma: no cover - admin readability
        label = self.name or self.identifier
        return f"{label} ({self.code})"
