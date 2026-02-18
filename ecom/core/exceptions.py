from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
import sentry_sdk
import os
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler.

    - Formats validation errors consistently.
    - Sends unexpected server errors (5xx) to Sentry.
    """

    response = exception_handler(exc, context)

    # Custom formatting for validation errors (400)
    if isinstance(exc, ValidationError):
        payload = {
            "status": "error",
            "code": "VALIDATION_ERROR",
            "message": "Invalid input.",
        }

        if isinstance(response.data, list):
            payload["errors"] = {
                "non_field_errors": response.data
            }
            
        elif isinstance(response.data, dict):
            payload["errors"] = response.data

        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    return response
