from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from .exceptions import (
    AuthenticationError,
    AutomatedActionBlocked,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ServiceError,
)

_STATUS_BY_ERROR = {
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    AutomatedActionBlocked: status.HTTP_403_FORBIDDEN,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
}

def api_exception_handler(exc, context):
    """Translate service errors to HTTP responses; defer everything else to DRF."""
    if isinstance(exc, ServiceError):
        code = _STATUS_BY_ERROR.get(type(exc), status.HTTP_400_BAD_REQUEST)
        body = exc.details if isinstance(exc, AutomatedActionBlocked) else {"detail": exc.message}
        headers = {"WWW-Authenticate": "Bearer"} if code == status.HTTP_401_UNAUTHORIZED else None
        return Response(body, status=code, headers=headers)
    return exception_handler(exc, context)
