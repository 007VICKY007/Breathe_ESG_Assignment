from django.urls import path

from .views import (
    AnomalyListView,
    DashboardSummaryView,
    EmissionRecordDetailView,
    EmissionRecordListView,
    RecordApproveView,
    RecordHistoryView,
    RecordLockView,
    RecordRejectView,
)

urlpatterns = [
    path("records/", EmissionRecordListView.as_view(), name="record-list"),
    path("records/<uuid:pk>/", EmissionRecordDetailView.as_view(), name="record-detail"),
    path("records/<uuid:pk>/approve/", RecordApproveView.as_view(), name="record-approve"),
    path("records/<uuid:pk>/reject/", RecordRejectView.as_view(), name="record-reject"),
    path("records/<uuid:pk>/lock/", RecordLockView.as_view(), name="record-lock"),
    path("records/<uuid:pk>/history/", RecordHistoryView.as_view(), name="record-history"),
    path("anomalies/", AnomalyListView.as_view(), name="anomaly-list"),
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
]
