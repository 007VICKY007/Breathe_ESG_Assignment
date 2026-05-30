from django.contrib import admin

from .models import ReviewAction


@admin.register(ReviewAction)
class ReviewActionAdmin(admin.ModelAdmin):
    list_display = ("action", "emission_record", "performed_by", "tenant", "created_at")
    list_filter = ("action", "tenant")
    readonly_fields = ("created_at",)
