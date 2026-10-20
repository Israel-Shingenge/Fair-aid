from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models

class UserRole(models.TextChoices):
    STUDENT = "student", "Student"
    ADMIN = "admin", "Admin"
    SUPERUSER = "superuser", "Superuser"

class UserManager(BaseUserManager):
    use_in_migrations = True

    @staticmethod
    def normalise_email(email: str) -> str:
        return email.strip().lower()

    def create_user(self, email, full_name, password, role=UserRole.STUDENT, **extra):
        user = self.model(email=self.normalise_email(email), full_name=full_name.strip(), role=role, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password, **extra):
        return self.create_user(email, full_name, password, role=UserRole.SUPERUSER, **extra)

class User(AbstractBaseUser):
    """
    Account identified by email. ``role`` is the single source of truth for authorisation;
    ``is_staff`` / ``is_superuser`` are derived so Django admin keeps working.
    """

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.STUDENT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"

    def __str__(self) -> str:
        return self.email

    @property
    def is_superuser(self) -> bool:
        return self.role == UserRole.SUPERUSER

    @property
    def is_staff(self) -> bool:
        return self.role in (UserRole.ADMIN, UserRole.SUPERUSER)

    # Minimal permission API required by django.contrib.admin
    def has_perm(self, perm, obj=None) -> bool:
        return self.is_active and self.is_superuser

    def has_module_perms(self, app_label) -> bool:
        return self.is_active and self.is_superuser

class RefreshToken(models.Model):
    """
    Server-side record of every issued refresh token.

    * ``session_id`` groups the chain of rotated tokens that started at one login. Access tokens carry
      the same id (``sid`` claim), so revoking a session also invalidates its access tokens at once.
    * ``used_at``    set when the token is exchanged for a new pair (rotation).
    * ``revoked_at`` set on logout, logout-all, deactivation or detected reuse.

    A session is active while it has a token that is unused, unrevoked and unexpired.
    """

    jti = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refresh_tokens")
    session_id = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    replaced_by = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        db_table = "refresh_tokens"
