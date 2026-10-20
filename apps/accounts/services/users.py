"""User account management: creation, lookup, role changes, (de)activation."""
from typing import List, Optional

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.common.exceptions import ConflictError, NotFoundError, PermissionDeniedError

from ..models import RefreshToken, User, UserManager, UserRole


class UserService:
    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        return User.objects.filter(pk=user_id).first()

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        return User.objects.filter(email=UserManager.normalise_email(email)).first()

    @staticmethod
    def get_or_404(user_id: int) -> User:
        user = UserService.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user

    @staticmethod
    def list_users(role: Optional[str] = None) -> List[User]:
        queryset = User.objects.order_by("id")
        return list(queryset.filter(role=role) if role else queryset)

    @staticmethod
    def create_user(email: str, full_name: str, password: str, role: str = UserRole.STUDENT) -> User:
        if UserService.get_by_email(email) is not None:
            raise ConflictError("An account with this email already exists")
        try:
            with transaction.atomic():
                return User.objects.create_user(email=email, full_name=full_name, password=password, role=role)
        except IntegrityError as exc:  # race: same email inserted concurrently
            raise ConflictError("An account with this email already exists") from exc

    @staticmethod
    def update_role(acting_user: User, target_id: int, new_role: str) -> User:
        target = UserService.get_or_404(target_id)
        if target.pk == acting_user.pk:
            # Prevents a superuser accidentally locking everyone out of user management
            raise PermissionDeniedError("You cannot change your own role")
        target.role = new_role
        target.save(update_fields=["role"])
        return target

    @staticmethod
    def set_active(acting_user: User, target_id: int, is_active: bool) -> User:
        target = UserService.get_or_404(target_id)
        if target.pk == acting_user.pk:
            raise PermissionDeniedError("You cannot deactivate your own account")
        with transaction.atomic():
            target.is_active = is_active
            target.save(update_fields=["is_active"])
            if not is_active:
                RefreshToken.objects.filter(user=target, revoked_at__isnull=True).update(revoked_at=timezone.now())
        return target
