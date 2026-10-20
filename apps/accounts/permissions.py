from rest_framework.permissions import BasePermission
from .models import UserRole

class HasRole(BasePermission):
    """Base for role checks; subclasses set ``allowed_roles``."""

    allowed_roles: tuple = ()

    def has_permission(self, request, view) -> bool:
        user = request.user
        if user is None or not getattr(user, "is_authenticated", False):
            return False  # DRF turns this into 401 because the authenticator defines a header
        if user.role in self.allowed_roles:
            return True
        self.message = f"Requires one of roles: {', '.join(sorted(r.value for r in self.allowed_roles))}"
        return False

class IsStudent(HasRole):
    allowed_roles = (UserRole.STUDENT,)

class IsStaff(HasRole):
    allowed_roles = (UserRole.ADMIN, UserRole.SUPERUSER)

class IsSuperuser(HasRole):
    allowed_roles = (UserRole.SUPERUSER,)
