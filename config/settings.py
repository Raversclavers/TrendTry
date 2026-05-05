import environ
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="changeme-set-a-real-secret-key-in-railway")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Railway sends healthcheck requests with Host: healthcheck.railway.app,
# not the public domain — both must be allowed.
_railway_hosts = [
    os.environ.get("RAILWAY_PUBLIC_DOMAIN", ""),
    "healthcheck.railway.app",
]
for _host in _railway_hosts:
    if _host and _host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_host)

# CSRF trusted origins — Django 4+ requires the scheme + host for POST
# requests (admin login, HTMX subscribe form, etc.) to pass CSRF checks.
CSRF_TRUSTED_ORIGINS = []
_railway_public = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
if _railway_public:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_railway_public}")

# ---------------------------------------------------------------------------
# Apps
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    # Third-party
    "tailwind",
    "theme",
    "meta",
    # Local
    "catalog",
    "pages",
]

TAILWIND_APP_NAME = "theme"
NPM_BIN_PATH = env("NPM_BIN_PATH", default=r"C:\Program Files\nodejs\npm.cmd")

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.context_processors.year",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database — PostgreSQL (local + production-ready)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="sqlite:///" + str(BASE_DIR / "db.sqlite3"),
    ),
}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# i18n / l10n
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Third-party API keys
# ---------------------------------------------------------------------------
FIRECRAWL_API_KEY = env("FIRECRAWL_API_KEY", default="")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")

# ---------------------------------------------------------------------------
# django-meta
# ---------------------------------------------------------------------------
META_SITE_PROTOCOL = "https"
META_SITE_DOMAIN = env("SITE_DOMAIN", default="trendtry.com")
META_USE_OG_PROPERTIES = True
META_USE_TWITTER_PROPERTIES = True
META_SITE_NAME = "TrendTry"

# ---------------------------------------------------------------------------
# Production security (only when DEBUG is False)
# ---------------------------------------------------------------------------
if not DEBUG:
    # Railway's edge proxy redirects HTTP→HTTPS for public traffic, so we
    # leave SECURE_SSL_REDIRECT off — otherwise Railway's internal healthcheck
    # (which talks plain HTTP to the pod) gets 301'd and reports "service
    # unavailable". The proxy header below is still set so Django reports
    # request.is_secure() correctly for cookies.
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 31_536_000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
