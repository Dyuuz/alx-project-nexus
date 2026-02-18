import contextvars
import threading

_request_local = threading.local()
request_var = contextvars.ContextVar("request", default=None)

def set_request(request):
    """
    Store the current HTTP request in a context variable.

    Used to make the request accessible during log record processing.
    """
    request_var.set(request)
    

def get_request():
    """
    Retrieve the current HTTP request from context storage.

    Returns:
        HttpRequest | None: The active request if available.
    """
    return request_var.get()


def get_request_id():
    """
    Return the request_id associated with the current execution context.

    Returns:
        str | None: Unique request identifier if set.
    """
    return getattr(_request_local, "request_id", None)


def set_request_id(request_id):
    """
    Attach a unique request_id to the current execution context.

    Args:
        request_id (str): UUID identifying the request lifecycle.
    """
    _request_local.request_id = request_id
    


def before_send(event, hint):
    """
    Attach request_id to Sentry even
    """
    event.setdefault("tags", {})
    event["tags"]["request_id"] = get_request_id()
    return event