from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import RefreshToken, User
from .tokens import ACCESS_TOKEN_TYPE, TokenError, decode_token


class SessionJWTAuthentication(BaseAuthentication):
    """
    Bearer access-token authentication backed by a server-side session.

    Validates signature and expiry, checks that the session was not logged out or revoked, and that
    the user still exists and is active.
    """

    keyword = b"bearer"

    def authenticate_header(self, request) -> str:
        return "Bearer"

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header or header[0].lower() != self.keyword:
            return None
        if len(header) != 2:
            raise AuthenticationFailed("Invalid Authorization header")

        try:
            payload = decode_token(header[1].decode(), expected_type=ACCESS_TOKEN_TYPE)
            user_id = int(payload["sub"])
        except (TokenError, ValueError, UnicodeError) as exc:
            raise AuthenticationFailed(str(exc)) from exc

        session_id = payload["sid"]
        if not RefreshToken.objects.filter(session_id=session_id, revoked_at__isnull=True).exists():
            raise AuthenticationFailed("Session has been logged out or revoked")

        user = User.objects.filter(pk=user_id).first()
        if user is None:
            raise AuthenticationFailed("User not found")
        if not user.is_active:
            raise AuthenticationFailed("This account has been deactivated")

        # `auth` carries the decoded claims so views can read the session id without re-decoding.
        return user, payload


try:  # lets drf-spectacular show the "Authorize" button in Swagger UI
    from drf_spectacular.extensions import OpenApiAuthenticationExtension

    class SessionJWTAuthenticationScheme(OpenApiAuthenticationExtension):
        target_class = "apps.accounts.authentication.SessionJWTAuthentication"
        name = "BearerAuth"

        def get_security_definition(self, auto_schema):
            return {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}

except ImportError:  # pragma: no cover
    pass
