"""
Domain-level exceptions raised by services. They carry no HTTP knowledge; the exception handler in
``apps.common.handlers`` maps them to status codes in one place.
"""

class ServiceError(Exception):
    """Base class for expected, user-facing errors."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class NotFoundError(ServiceError):
    """Requested resource does not exist (HTTP 404)."""

class ConflictError(ServiceError):
    """Resource already exists or conflicts with current state (HTTP 409)."""

class PermissionDeniedError(ServiceError):
    """Action not allowed for the acting user (HTTP 403)."""

class AuthenticationError(ServiceError):
    """Credentials or tokens are invalid (HTTP 401)."""

class AutomatedActionBlocked(ServiceError):
    """An automated submission/award was attempted; the human-in-the-loop policy forbids it (HTTP 403)."""

    def __init__(self, message: str, details: dict):
        super().__init__(message)
        self.details = details
