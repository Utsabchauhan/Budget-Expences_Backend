from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or "insecure-local-development-key"
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "core",
    "departments",
    "categories",
    "budgets",
    "expenses",
    "income",
    "approvals",
    "reports",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


ORACLE_SERVICE_NAME = os.getenv("ORACLE_SERVICE_NAME", "")
ORACLE_NAME = os.getenv("ORACLE_NAME", "") or ORACLE_SERVICE_NAME
ORACLE_TEST_USER = os.getenv("ORACLE_TEST_USER", "BUDGETFLOW_TEST")
ORACLE_TEST_PASSWORD = os.getenv("ORACLE_TEST_PASSWORD", "")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.oracle",
        "NAME": ORACLE_NAME,
        "USER": os.getenv("ORACLE_USER", ""),
        "PASSWORD": os.getenv("ORACLE_PASSWORD", ""),
        "HOST": os.getenv("ORACLE_HOST", "localhost"),
        "PORT": os.getenv("ORACLE_PORT", "1521"),
        "TEST": {
            "CREATE_DB": False,
            "CREATE_USER": False,
            "USER": ORACLE_TEST_USER,
            "PASSWORD": ORACLE_TEST_PASSWORD,
        },
    }
}

if ORACLE_SERVICE_NAME:
    DATABASES["default"]["OPTIONS"] = {"service_name": ORACLE_SERVICE_NAME}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")
CORS_ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]
CORS_ALLOWED_ORIGINS = list(dict.fromkeys(CORS_ALLOWED_ORIGINS))

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
