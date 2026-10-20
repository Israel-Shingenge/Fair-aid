from django.core.exceptions import ImproperlyConfigured
from .base import *  # noqa: F401,F403
from .base import SECRET_KEY

if not SECRET_KEY:
    raise ImproperlyConfigured(
        'SECRET_KEY is not set. Generate one with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
    )

DEBUG = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
