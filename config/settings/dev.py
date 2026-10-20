from .base import *  # noqa: F401,F403
from .base import SECRET_KEY as _SECRET_KEY

DEBUG = True
# Convenience for local work only; production refuses to start without a real SECRET_KEY.
SECRET_KEY = _SECRET_KEY or "dev-only-insecure-key-change-me-0123456789-abcdefghijklmnopqrstuvwxyz"
