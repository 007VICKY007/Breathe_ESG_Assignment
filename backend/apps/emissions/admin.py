from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import AnomalyFlag, EmissionRecord


class AnomalyFlagInline(admin.TabularInline):
    model = AnomalyFlag
    extra = 0
    readonly_fields = ("flag_type", "severity", "message", "affected_field", "created_at")


@admin.register(EmissionRecord)
class EmissionRecordAdmin(SimpleHistoryAdmin):
    list_display = (
        "activity_date",
        "source_type",
        "scope",
        "normalized_value_kg",
        "review_status",
        "tenant",
    )
    list_filter = ("source_type", "scope", "review_status", "tenant")
    search_fields = ("location", "vendor_or_carrier", "source_row_hash")
    inlines = [AnomalyFlagInline]
    readonly_fields = ("source_row_hash", "created_at", "updated_at")


@admin.register(AnomalyFlag)
class AnomalyFlagAdmin(admin.ModelAdmin):
    list_display = ("flag_type", "severity", "emission_record", "tenant", "created_at")
    list_filter = ("severity", "flag_type", "tenant")
