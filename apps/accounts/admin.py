from django.contrib import admin
from .models import RefreshToken, User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("email", "full_name")
    exclude = ("password",)  # never edit hashes by hand; use the API or `createsuperuser`

@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ("jti", "user", "session_id", "expires_at", "used_at", "revoked_at")
    readonly_fields = [f.name for f in RefreshToken._meta.fields]
