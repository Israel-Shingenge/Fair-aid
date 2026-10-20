"""JWT creation and verification. Knows nothing about the database or HTTP."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple

import jwt
from django.conf import settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


class TokenError(Exception):
    """A JWT is invalid, expired, or of the wrong type."""

def new_session_id() -> str:
    return uuid.uuid4().hex

def access_token_lifetime_seconds() -> int:
    return settings.JWT["ACCESS_TOKEN_LIFETIME_MINUTES"] * 60

def _secret() -> str:
    if not settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set")
    return settings.SECRET_KEY

def _create(subject: str, token_type: str, lifetime: timedelta, extra: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + lifetime,
        "jti": uuid.uuid4().hex,
        **extra,
    }
    return jwt.encode(payload, _secret(), algorithm=settings.JWT["ALGORITHM"]), payload

def create_access_token(user_id: int, role: str, session_id: str) -> str:
    # `role` is informational for clients; the server always re-reads the role from the database.
    # `sid` ties the token to a server-side session so logout revokes it immediately.
    token, _ = _create(
        str(user_id),
        ACCESS_TOKEN_TYPE,
        timedelta(minutes=settings.JWT["ACCESS_TOKEN_LIFETIME_MINUTES"]),
        {"role": role, "sid": session_id},
    )
    return token

def create_refresh_token(user_id: int, session_id: str) -> Tuple[str, str, datetime]:
    """Returns ``(token, jti, expires_at)`` so the caller can persist the token."""
    token, payload = _create(
        str(user_id),
        REFRESH_TOKEN_TYPE,
        timedelta(days=settings.JWT["REFRESH_TOKEN_LIFETIME_DAYS"]),
        {"sid": session_id},
    )
    return token, payload["jti"], payload["exp"]

def decode_token(token: str, expected_type: str) -> Dict[str, Any]:
    """Decode and validate a JWT; raises ``TokenError`` on any problem."""
    try:
        payload = jwt.decode(
            token,
            _secret(),
            algorithms=[settings.JWT["ALGORITHM"]],
            options={"require": ["exp", "iat", "sub", "type", "jti", "sid"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Invalid token") from exc

    if payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token")
    return payload
