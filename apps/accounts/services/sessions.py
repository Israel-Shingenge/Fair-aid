"""Server-side session tracking: issuing, rotating (with reuse detection) and revoking tokens."""
from dataclasses import dataclass
from typing import Optional, Tuple

from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import AuthenticationError

from .. import tokens
from ..models import RefreshToken, User


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class SessionService:
    @staticmethod
    def issue(user: User, session_id: Optional[str] = None) -> TokenPair:
        """Issue an access/refresh pair and persist the refresh token. Starts a new session if needed."""
        return SessionService._issue(user, session_id)[0]

    @staticmethod
    def _issue(user: User, session_id: Optional[str] = None) -> Tuple[TokenPair, str]:
        session_id = session_id or tokens.new_session_id()
        access = tokens.create_access_token(user.pk, user.role, session_id)
        refresh, jti, expires_at = tokens.create_refresh_token(user.pk, session_id)
        RefreshToken.objects.create(jti=jti, user=user, session_id=session_id, expires_at=expires_at)
        return TokenPair(access, refresh, tokens.access_token_lifetime_seconds()), jti

    @staticmethod
    def rotate(refresh_token: str) -> TokenPair:
        """
        Exchange an unused refresh token for a new pair. Presenting an already-used token is treated
        as theft and revokes the whole session.
        """
        try:
            payload = tokens.decode_token(refresh_token, expected_type=tokens.REFRESH_TOKEN_TYPE)
        except tokens.TokenError as exc:
            raise AuthenticationError(str(exc)) from exc

        session_id = payload["sid"]
        reuse_detected = False

        with transaction.atomic():
            record = RefreshToken.objects.select_for_update().select_related("user").filter(pk=payload["jti"]).first()
            if record is None:
                raise AuthenticationError("Refresh token not found or already invalidated")

            now = timezone.now()
            if record.used_at is not None:
                reuse_detected = True
            else:
                if record.revoked_at is not None:
                    raise AuthenticationError("Session or refresh token has been revoked")
                if record.expires_at < now:
                    raise AuthenticationError("Refresh token has expired")
                user = record.user
                if not user.is_active:
                    raise AuthenticationError("User no longer exists or is deactivated")

                new_pair, new_jti = SessionService._issue(user, session_id)
                record.used_at = now
                record.replaced_by = new_jti
                record.save(update_fields=["used_at", "replaced_by"])
                return new_pair

        # Reuse handling happens outside the atomic block so the revocation is committed.
        if reuse_detected:
            SessionService.revoke_session(session_id)
            raise AuthenticationError("Refresh token reuse detected. All sessions for this token have been revoked.")
        raise AssertionError("unreachable")  # pragma: no cover

    @staticmethod
    def revoke_session(session_id: str) -> None:
        RefreshToken.objects.filter(session_id=session_id, revoked_at__isnull=True).update(revoked_at=timezone.now())

    @staticmethod
    def revoke_all_for_user(user_id: int) -> None:
        RefreshToken.objects.filter(user_id=user_id, revoked_at__isnull=True).update(revoked_at=timezone.now())
