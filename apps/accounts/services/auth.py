"""Authentication flows: signup, credential check, refresh and logout."""
from functools import lru_cache

from django.contrib.auth.hashers import check_password, make_password

from apps.common.exceptions import AuthenticationError

from .. import tokens
from ..models import User, UserRole
from .sessions import SessionService, TokenPair
from .users import UserService

INVALID_CREDENTIALS = "Incorrect email or password"


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    return make_password("fairaid-dummy-password")


class AuthService:
    @staticmethod
    def signup_student(email: str, full_name: str, password: str) -> User:
        """Public signup always creates a STUDENT account."""
        return UserService.create_user(email, full_name, password, role=UserRole.STUDENT)

    @staticmethod
    def authenticate(email: str, password: str) -> User:
        user = UserService.get_by_email(email)
        if user is None:
            check_password(password, _dummy_hash())  # equalise timing: don't reveal which emails exist
            raise AuthenticationError(INVALID_CREDENTIALS)
        if not user.check_password(password):
            raise AuthenticationError(INVALID_CREDENTIALS)
        if not user.is_active:
            raise AuthenticationError("This account has been deactivated")
        return user

    @staticmethod
    def login(email: str, password: str) -> TokenPair:
        return SessionService.issue(AuthService.authenticate(email, password))

    @staticmethod
    def refresh(refresh_token: str) -> TokenPair:
        return SessionService.rotate(refresh_token)

    @staticmethod
    def logout_by_access_token(access_token: str) -> bool:
        return AuthService._logout_with(access_token, tokens.ACCESS_TOKEN_TYPE)

    @staticmethod
    def logout_by_refresh_token(refresh_token: str) -> bool:
        return AuthService._logout_with(refresh_token, tokens.REFRESH_TOKEN_TYPE)

    @staticmethod
    def logout_all(user_id: int) -> None:
        SessionService.revoke_all_for_user(user_id)

    @staticmethod
    def _logout_with(token: str, expected_type: str) -> bool:
        try:
            payload = tokens.decode_token(token, expected_type=expected_type)
        except tokens.TokenError:
            return False
        SessionService.revoke_session(payload["sid"])
        return True
