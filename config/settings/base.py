import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]

# --- Core ---------------------------------------------------------------------------------------
# No default on purpose: JWTs and sessions must never be signed with a known value.
SECRET_KEY = os.environ.get("SECRET_KEY", "")
DEBUG = False
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
APPEND_SLASH = False  # the public API has always used URLs without trailing slashes
API_V1_PREFIX = "/api"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "apps.common",
    "apps.accounts",
    "apps.schemes",
    "apps.prescreening",
    "apps.fairness",
    "apps.governance",
    "apps.explanations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# --- Database -----------------------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL"),
        conn_max_age=60,
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Auth ---------------------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",  # same algorithm the FastAPI app used
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = []  # signup enforces length 8-128 in its serializer, as before

JWT = {
    "ALGORITHM": os.environ.get("JWT_ALGORITHM", "HS256"),
    "ACCESS_TOKEN_LIFETIME_MINUTES": int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    "REFRESH_TOKEN_LIFETIME_DAYS": int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
}

# --- LLM (Gemini free tier) ---------------------------------------------------------------------
# Defaults assume the strictest published free-tier numbers (about 5 requests/minute, 20/day, one at a
# time). Raise DAILY_LIMIT / lower MIN_INTERVAL only after checking your project's limits in AI Studio.
GEMINI = {
    "API_KEY": os.environ.get("GEMINI_API_KEY", ""),
    "MODEL": os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"),
    "BASE_URL": os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
    "MIN_INTERVAL_SECONDS": float(os.environ.get("GEMINI_MIN_INTERVAL_SECONDS", "13")),
    "DAILY_LIMIT": int(os.environ.get("GEMINI_DAILY_LIMIT", "18")),
    "QUEUE_WAIT_SECONDS": float(os.environ.get("GEMINI_QUEUE_WAIT_SECONDS", "20")),
    "REQUEST_TIMEOUT_SECONDS": float(os.environ.get("GEMINI_REQUEST_TIMEOUT_SECONDS", "30")),
    "MAX_OUTPUT_TOKENS": int(os.environ.get("GEMINI_MAX_OUTPUT_TOKENS", "2048")),
    "TEMPERATURE": float(os.environ.get("GEMINI_TEMPERATURE", "0.2")),
}

# Which model writes the explanations. "gemini" = hosted free tier (strict limits, handled by the gate);
# "ollama" = a local model such as Llama 3.2 3B (no quota, but you host it and it is less reliable).
LLM = {
    "PROVIDER": os.environ.get("LLM_PROVIDER", "gemini").lower(),
    "ENABLED": os.environ.get("LLM_ENABLED", "true").lower() == "true",
    "HISTORY_TURNS": int(os.environ.get("LLM_HISTORY_TURNS", "3")),  # previous Q&A pairs sent with a follow-up
    # Let the model also word the what-if answer (a 2nd call). "auto" = on for ollama, off for gemini.
    "WHATIF_NARRATION": os.environ.get("LLM_WHATIF_NARRATION", "auto").lower(),
}
OLLAMA = {
    "BASE_URL": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
    "MODEL": os.environ.get("OLLAMA_MODEL", "llama3.2:3b"),
    "REQUEST_TIMEOUT_SECONDS": float(os.environ.get("OLLAMA_REQUEST_TIMEOUT_SECONDS", "120")),
    "QUEUE_WAIT_SECONDS": float(os.environ.get("OLLAMA_QUEUE_WAIT_SECONDS", "60")),
    "NUM_CTX": int(os.environ.get("OLLAMA_NUM_CTX", "8192")),  # Ollama's default window is too small for our prompts
    "NUM_PREDICT": int(os.environ.get("OLLAMA_NUM_PREDICT", "700")),
    "TEMPERATURE": float(os.environ.get("OLLAMA_TEMPERATURE", "0.2")),
}

# --- DRF ----------------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.accounts.authentication.SessionJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",  # /auth/login is form-encoded (OAuth2 password flow)
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.common.handlers.api_exception_handler",
    "UNAUTHENTICATED_USER": None,
    # Per-student caps so one user cannot drain the shared LLM quota (counted per process; use a shared
    # cache backend such as Redis if you run several workers).
    "DEFAULT_THROTTLE_RATES": {"llm_explain": "20/hour", "llm_ask": "10/hour"},
}

SPECTACULAR_SETTINGS = {
    "TITLE": "FairAid Pre-Screening API",
    "DESCRIPTION": (
        "Human-Centered Explainable AI (HCAI) pre-screening engine for bursary and financial aid "
        "schemes. Advisory only: the system never submits applications or makes binding funding "
        "decisions."
    ),
    "VERSION": "3.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# --- i18n / static ------------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
