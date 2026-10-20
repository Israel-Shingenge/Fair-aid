from rest_framework import serializers
from .models import User, UserRole

class UserOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "is_active", "created_at"]
        read_only_fields = fields

class StudentSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(min_length=1, max_length=120)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True, trim_whitespace=False)

class UserCreateBySuperuserSerializer(StudentSignupSerializer):
    role = serializers.ChoiceField(choices=UserRole.choices, default=UserRole.ADMIN)

class UserRoleUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserRole.choices)

class UserStatusUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class LoginSerializer(serializers.Serializer):
    """OAuth2 password flow (form-encoded): put the *email* in ``username``."""

    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)


class RefreshRequestSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

class LogoutRequestSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=False, allow_null=True, allow_blank=True)

class TokenPairSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField()
    expires_in = serializers.IntegerField(help_text="Access token lifetime in seconds")

class AuthMessageSerializer(serializers.Serializer):
    message = serializers.CharField()
