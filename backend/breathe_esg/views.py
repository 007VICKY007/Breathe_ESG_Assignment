import logging

from django.db import connection
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Liveness/readiness probe for Railway and local dev.
    Verifies database connectivity — does not require authentication.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        db_ok = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_ok = cursor.fetchone()[0] == 1
        except Exception:
            logger.exception("Health check database probe failed")

        if not db_ok:
            return Response(
                {
                    "status": "unhealthy",
                    "database": "down",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "status": "healthy",
                "database": "up",
                "service": "breathe-esg-api",
            },
            status=status.HTTP_200_OK,
        )
