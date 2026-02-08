# core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return response

    if isinstance(exc, ValidationError):
        payload = {
            "status": "error",
            "code": "VALIDATION_ERROR",
            "message": "Invalid input.",
        }

        # Always expose original validation details under `errors`
        if isinstance(response.data, list):
            payload["errors"] = {
                "non_field_errors": response.data
            }
        elif isinstance(response.data, dict):
            payload["errors"] = response.data

        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    return response
