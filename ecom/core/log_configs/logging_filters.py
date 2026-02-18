import logging
from core.log_configs.logging_context import get_request_id, get_request


class InfoOnlyFilter(logging.Filter):
    """
    Logging filter that allows only exact INFO-level records.

    This filter prevents hierarchical level behavior (where INFO-level
    handlers also capture WARNING, ERROR, and CRITICAL logs).

    Intended usage:
        Attach to a handler that should contain only informational
        business logs (e.g., app.log), excluding warnings and errors.

    Returns:
        bool: True if the record level is exactly logging.INFO,
              False otherwise.
    """
    def filter(self, record):
        return record.levelno == logging.INFO


class RequestUserFilter(logging.Filter):
    """
    Logging filter that injects request-specific metadata into log records.

    This filter attaches:
        - request_id: Unique identifier generated per HTTP request.
        - user_id: Authenticated user ID (if available).

    Designed for JWT / DRF authentication environments where:
        - Authentication occurs inside the view layer.
        - Middleware cannot reliably access authenticated users.
        - Request context must be injected at log emission time.

    The filter retrieves the current request from a context variable
    (contextvars-based storage) and safely extracts authentication details.

    This enables structured JSON logging with traceability and accountability.

    Returns:
        bool: Always True to allow the log record to be processed.
    """
    def filter(self, record):
        # Always set defaults first
        record.request_id = get_request_id() or None
        record.user_id = None

        request = get_request()

        if request and hasattr(request, "user") and request.user.is_authenticated:
            record.user_id = request.user.id

        return True
