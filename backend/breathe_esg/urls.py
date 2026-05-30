from django.contrib import admin
from django.urls import include, path

from .views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", HealthCheckView.as_view(), name="health"),
    path("api/v1/", include("apps.organizations.urls")),
    path("api/v1/", include("apps.ingestion.urls")),
    path("api/v1/", include("apps.emissions.urls")),
    path("api/v1/", include("apps.reviews.urls")),
]
