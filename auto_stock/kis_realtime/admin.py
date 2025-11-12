from django.contrib import admin

from .models import RealtimeSymbol


@admin.register(RealtimeSymbol)
class RealtimeSymbolAdmin(admin.ModelAdmin):
    list_display = ("identifier", "code", "name", "updated_at")
    search_fields = ("identifier", "code", "name")
