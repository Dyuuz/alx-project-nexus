import uuid
from core.log_configs.logging_context import set_request_id, set_request
from sentry_sdk import set_user, set_context, set_tag


class LoggingContextMiddleware:
    """
    Middleware that initializes request-scoped logging context.

    Responsibilities:
        - Stores the current HTTP request in context storage.
        - Generates and assigns a unique request_id per request.

    This enables log filters to inject request_id and user_id
    dynamically at log emission time, supporting JWT/DRF authentication
    where user resolution occurs inside the view layer.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_request(request)  # store full request

        request_id = str(uuid.uuid4())
        set_request_id(request_id)
        
        # Attach request ID to Sentry
        set_context("request_meta", {"request_id": request_id})
        set_tag("request_id", request_id)
        set_tag("endpoint", request.path)
        set_tag("method", request.method)

        response = self.get_response(request)
        return response
