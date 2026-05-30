from django.contrib import admin

from .models import DataSource, IngestionJob


@admin.register(IngestionJob)
class IngestionJobAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "source_category",
        "status",
        "rows_total",
        "rows_created",
        "tenant",
        "created_at",
    )
    list_filter = ("status", "source_category", "tenant")
    readonly_fields = ("created_at", "updated_at", "error_log")


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("display_name", "source_type", "is_active", "tenant")
    list_filter = ("source_type", "is_active")
