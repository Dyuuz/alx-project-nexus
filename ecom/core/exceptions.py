from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
import sentry_sdk
import os

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.exceptions import (
    AuthenticationFailed, ValidationError,
    NotAuthenticated, PermissionDenied
)
from jwt import ExpiredSignatureError
from core.errors import AppError
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """ 
    
    """
    # Handle custom app exceptions first
    if isinstance(exc, AppError):
        return Response(
            {
                "status": "error",
                "code": exc.code,
                "errors": exc.message,
            },
            status=exc.status
        )
    
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data

        # --- Handle SimpleJWT / AuthenticationFailed ---
        if isinstance(exc, AuthenticationFailed):
            detail = getattr(exc, "detail", None)

            # Handle nested SimpleJWT error payloads
            if isinstance(detail, dict):
                messages = detail.get("messages")
                if messages and isinstance(messages, list):
                    msg = messages[0]
                    message = msg.get("message", detail.get("detail"))
                    token_type = msg.get("token_type", "").lower()

                    # Customize based on token type
                    if "expired" in message.lower():
                        if token_type == "access":
                            message = "Your access token has expired. Please log in again."
                        elif token_type == "refresh":
                            message = "Your refresh token has expired. Please sign in again to continue."
                        else:
                            message = "Your authentication token has expired. Please reauthenticate."

                    code = detail.get("code", "UNAUTHORIZED")

                    response.data = {
                        "status": "error",
                        "code": code.upper(),
                        "errors": message,
                    }
                else:
                    response.data = {
                        "status": "error",
                        "code": detail.get("code", "UNAUTHORIZED").upper(),
                        "errors": detail.get("detail", "Authentication failed"),
                    }

            else:
                response.data = {
                    "status": "error",
                    "code": "UNAUTHORIZED",
                    "errors": str(detail or "Invalid credentials"),
                }

        # --- Handle JWT Expired Token ---
        elif isinstance(exc, ExpiredSignatureError):
            response.data = {
                "status": "error",
                "code": "TOKEN_EXPIRED",
                "errors": "Authentication token expired. Obtain a new token to continue.",
            }

        # --- Handle ValidationError ---
        elif isinstance(exc, ValidationError):
            if isinstance(exc.detail, dict):
                # Preserve field-specific errors (dict)
                errors = exc.detail
            elif isinstance(exc.detail, list):
                # Multiple non-field errors
                errors = exc.detail
            else:
                # Single general error
                errors = str(exc.detail)

            response.data = {
                "status": "error",
                "code": "VALIDATION_ERROR",
                "errors": errors,
            }

        # --- Handle NotAuthenticated / PermissionDenied ---
        elif isinstance(exc, (NotAuthenticated, PermissionDenied)):
            response.data = {
                "status": "error",
                "code": "FORBIDDEN" if isinstance(exc, PermissionDenied) else "UNAUTHORIZED",
                "errors": str(exc.detail),
            }

        # --- Fallback for all other exceptions ---
        else:
            # print("Unhandled exception:", response.data)
            
            # errorMessage = {}
            # if isinstance(data, dict):
            #     detail = data.get("detail")
            #     if isinstance(detail, dict):
            #         # Merge all keys from the detail dict (including redirect_url)
            #         errorMessage = {**detail}
            #     else:
            #         # If detail is a string, wrap it
            #         errorMessage = {"detail": detail}
                
            #     # Merge any other keys at the top level (like redirect_url if not inside detail)
            #     for k, v in data.items():
            #         if k not in ["detail", "code"]:
            #             errorMessage[k] = v

            # elif isinstance(data, list):
            #     errorMessage = {"detail": ", ".join(map(str, data))}
            # else:
            #     errorMessage = {"detail": str(data) if data else "An unexpected error occurred"}

            code = (
                (data.get("code") if isinstance(data, dict) else None)
                or getattr(exc, "default_code", None)
                or "ERROR"
            )
            
            dataMessage = (data.get("data") if isinstance(data, dict) else {})
            
            response.data = {
                "status": "error",
                "code": str(code).upper(),
                "errors": data.get("detail", "An unexpected error occurred"),
                "data": dataMessage ,
            }   

    elif response is None:  # ← truly unexpected, DRF couldn't handle it
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return Response(
            {
                "status": "error",
                "code": "SERVER_ERROR",
                "errors": "Something went wrong. Try again later.",
            },
            status=500
        )
        
    return response
