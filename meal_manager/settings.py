import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Core security / debug
# -----------------------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

# e.g. "meal-management-1-dlcj.onrender.com"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

# -----------------------------------------------------------------------------
# CSRF trusted origins (needed for HTTPS on Render)
# -----------------------------------------------------------------------------
CSRF_TRUSTED_ORIGINS = []

# Render automatically sets this, like "https://meal-management-1-dlcj.onrender.com"
render_external_url = os.environ.get("RENDER_EXTERNAL_URL")
if render_external_url:
    # ensure it starts with scheme
    CSRF_TRUSTED_ORIGINS.append(render_external_url)

# Optional extra origins via env, e.g.
# DJANGO_CSRF_TRUSTED_ORIGINS="https://meal-management-1-dlcj.onrender.com"
extra_csrf = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS")
if extra_csrf:
    CSRF_TRUSTED_ORIGINS.extend(
        [origin.strip() for origin in extra_csrf.split(",") if origin.strip()]
    )

# -----------------------------------------------------------------------------
# Apps & middleware
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

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

ROOT_URLCONF = "meal_manager.urls"

# -----------------------------------------------------------------------------
# Templates
# -----------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "meal_manager.wsgi.application"

# -----------------------------------------------------------------------------
# Database (SQLite locally, Postgres on Render via DATABASE_URL)
# -----------------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=False,  # Render free Postgres often works without SSL
    )
}

# -----------------------------------------------------------------------------
# Internationalization
# -----------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# Static files
# -----------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# -----------------------------------------------------------------------------
# Auth redirects
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"
