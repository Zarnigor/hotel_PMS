import logging
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response

from .base import BaseAppException

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    view = context.get("view")
    view_name = view.__class__.__name__ if view else None

    # 1.custom exceptions
    if isinstance(exc, BaseAppException):
        logger.warning(f"[{exc.error_code}] {exc.message} | view={view_name}")
        return Response(
            {
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "extra": exc.extra,
            },
            status=exc.status_code,
        )

    # 2. (ValidationError, NotFound...) DRF exceptions
    response = drf_exception_handler(exc, context)
    if response is not None:
        response.data = {
            "success": False,
            "error_code": getattr(exc, "default_code", "error"),
            "message": response.data.get("detail", response.data)
            if isinstance(response.data, dict) else response.data,
            "extra": response.data if isinstance(response.data, dict) else {},
        }
        return response

    # 3. Kutilmagan xatolar
    logger.error(f"Kutilmagan xato: {exc}", exc_info=True)
    return None