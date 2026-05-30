from django.urls import path

from apps.emissions.views import JobBulkApproveView, JobEmissionRecordsView

from .views import (
    IngestSapView,
    IngestTravelView,
    IngestUtilityView,
    IngestionJobDetailView,
    IngestionJobListView,
    IngestionJobRetryView,
)

urlpatterns = [
    path("ingest/sap/", IngestSapView.as_view(), name="ingest-sap"),
    path("ingest/utility/", IngestUtilityView.as_view(), name="ingest-utility"),
    path("ingest/travel/", IngestTravelView.as_view(), name="ingest-travel"),
    path("jobs/", IngestionJobListView.as_view(), name="job-list"),
    path("jobs/<uuid:pk>/", IngestionJobDetailView.as_view(), name="job-detail"),
    path("jobs/<uuid:pk>/retry/", IngestionJobRetryView.as_view(), name="job-retry"),
    path(
        "jobs/<uuid:pk>/records/",
        JobEmissionRecordsView.as_view(),
        name="job-records",
    ),
    path(
        "jobs/<uuid:pk>/bulk-approve/",
        JobBulkApproveView.as_view(),
        name="job-bulk-approve",
    ),
]
