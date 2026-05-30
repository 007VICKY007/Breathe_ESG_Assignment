import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Return JSON {error, detail} for all API errors — never HTML."""
    response = exception_handler(exc, context)

    if response is not None:
        detail = response.data
        if isinstance(detail, dict):
            if "detail" in detail and len(detail) == 1:
                message = str(detail["detail"])
            else:
                message = str(detail)
        elif isinstance(detail, list):
            message = "; ".join(str(item) for item in detail)
        else:
            message = str(detail)

        response.data = {
            "error": exc.__class__.__name__,
            "detail": message,
        }
        return response

    logger.exception("Unhandled exception in API view", exc_info=exc)
    return Response(
        {"error": "ServerError", "detail": "An unexpected error occurred."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
