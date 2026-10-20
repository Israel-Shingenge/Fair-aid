"""Thin HTTP layer: parse and validate input, call a service, serialise the result."""
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import serializers as s
from .models import UserRole
from .permissions import IsSuperuser
from .services import AuthService, UserService

AUTH = ["Authentication"]
USERS = ["User Management"]

class SignupView(APIView):
    @extend_schema(request=s.StudentSignupSerializer, responses={201: s.UserOutSerializer}, tags=AUTH,
                   summary="Register a new student account")
    def post(self, request):
        data = _validated(s.StudentSignupSerializer, request.data)
        user = AuthService.signup_student(data["email"], data["full_name"], data["password"])
        return Response(s.UserOutSerializer(user).data, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    @extend_schema(request=s.LoginSerializer, responses=s.TokenPairSerializer, tags=AUTH,
                   summary="Log in with email and password")
    def post(self, request):
        data = _validated(s.LoginSerializer, request.data)
        pair = AuthService.login(email=data["username"], password=data["password"])
        return Response(s.TokenPairSerializer(pair).data)

class RefreshView(APIView):
    @extend_schema(request=s.RefreshRequestSerializer, responses=s.TokenPairSerializer, tags=AUTH,
                   summary="Exchange a refresh token for a new token pair")
    def post(self, request):
        data = _validated(s.RefreshRequestSerializer, request.data)
        return Response(s.TokenPairSerializer(AuthService.refresh(data["refresh_token"])).data)

class LogoutView(APIView):
    """Logs out the current session via the Bearer access token, a refresh token in the body, or both."""

    @extend_schema(request=s.LogoutRequestSerializer, responses=s.AuthMessageSerializer, tags=AUTH,
                   summary="Log out of the current session")
    def post(self, request):
        body = _validated(s.LogoutRequestSerializer, request.data or {})
        logged_out = False

        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            logged_out |= AuthService.logout_by_access_token(header.split(" ", 1)[1])
        if body.get("refresh_token"):
            logged_out |= AuthService.logout_by_refresh_token(body["refresh_token"])

        if not logged_out:
            return Response(
                {"detail": "A valid Bearer access token or refresh token is required to log out"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(s.AuthMessageSerializer({"message": "Successfully logged out of session"}).data)

class LogoutAllView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=s.AuthMessageSerializer, tags=AUTH,
                   summary="Log out of all active sessions across all devices")
    def post(self, request):
        AuthService.logout_all(request.user.pk)
        return Response(s.AuthMessageSerializer({"message": "Successfully logged out of all sessions"}).data)

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=s.UserOutSerializer, tags=AUTH, summary="Get the currently authenticated user")
    def get(self, request):
        return Response(s.UserOutSerializer(request.user).data)

# --- Superuser-only user management ------------------------------------------------------------
class UserListCreateView(APIView):
    permission_classes = [IsSuperuser]

    @extend_schema(responses=s.UserOutSerializer(many=True), tags=USERS, summary="List users (superuser)")
    def get(self, request):
        role = request.query_params.get("role")
        if role and role not in UserRole.values:
            raise ValidationError({"role": [f"Must be one of: {', '.join(UserRole.values)}"]})
        return Response(s.UserOutSerializer(UserService.list_users(role=role), many=True).data)

    @extend_schema(request=s.UserCreateBySuperuserSerializer, responses={201: s.UserOutSerializer}, tags=USERS,
                   summary="Create a user with any role, e.g. an admin (superuser)")
    def post(self, request):
        data = _validated(s.UserCreateBySuperuserSerializer, request.data)
        user = UserService.create_user(data["email"], data["full_name"], data["password"], role=data["role"])
        return Response(s.UserOutSerializer(user).data, status=status.HTTP_201_CREATED)

class UserDetailView(APIView):
    permission_classes = [IsSuperuser]

    @extend_schema(responses=s.UserOutSerializer, tags=USERS, summary="Get a user (superuser)")
    def get(self, request, user_id: int):
        return Response(s.UserOutSerializer(UserService.get_or_404(user_id)).data)

class UserRoleView(APIView):
    permission_classes = [IsSuperuser]

    @extend_schema(request=s.UserRoleUpdateSerializer, responses=s.UserOutSerializer, tags=USERS,
                   summary="Change a user's role (superuser)")
    def patch(self, request, user_id: int):
        data = _validated(s.UserRoleUpdateSerializer, request.data)
        return Response(s.UserOutSerializer(UserService.update_role(request.user, user_id, data["role"])).data)

class UserStatusView(APIView):
    permission_classes = [IsSuperuser]

    @extend_schema(request=s.UserStatusUpdateSerializer, responses=s.UserOutSerializer, tags=USERS,
                   summary="Activate or deactivate a user (superuser)")
    def patch(self, request, user_id: int):
        data = _validated(s.UserStatusUpdateSerializer, request.data)
        return Response(s.UserOutSerializer(UserService.set_active(request.user, user_id, data["is_active"])).data)

def _validated(serializer_class, data) -> dict:
    serializer = serializer_class(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data
