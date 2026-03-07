class AppError(Exception):
    """Base exception for all app-level errors."""
    code = "SERVER_ERROR"
    message = "An unexpected error occurred."
    status = 500
    

class ConflictException(AppError):
    status = 409
    message = "Conflict detected. Record was modified by another request."
    code = "conflict"