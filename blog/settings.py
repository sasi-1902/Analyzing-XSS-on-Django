"""
Django settings for the Django blog + XSS security layer project.

The blog (core/users) is the primary application and is safe by default.
It intentionally ships a small, clearly-labelled security layer (the
xss_lab app, under /xss/, /auditor/ and /guide/) that demonstrates
Stored/Reflected/DOM-based XSS using the blog's own posts, comments and
search, alongside their secure equivalents, plus a static-analysis
Auditor.

This is a LOCAL educational project. Do not deploy it publicly.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: this fallback key is for local development only.
# Override it with a real secret via the SECRET_KEY environment variable
# for anything other than running the lab on your own machine.
SECRET_KEY = os.environ.get(
    'SECRET_KEY', 'dev-only-insecure-secret-key-do-not-deploy'
)

# Local lab: DEBUG defaults to on. Set DJANGO_DEBUG=false to turn it off.
DEBUG = os.environ.get('DJANGO_DEBUG', 'true').lower() not in ('false', '0', 'no')

# This project is only meant to run on the developer's own machine.
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'core',
    # Security layer: XSS demonstrations built on the blog's real models,
    # plus the static-analysis Auditor. See the in-app Guide for details.
    'xss_lab',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'blog.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'blog.wsgi.application'


# Database
# SQLite is sufficient for this local lab; no external DB server is used.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

AUTH_USER_MODEL = 'users.User'

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

LOGIN_URL = '/users/login/'

# Local-only lab: emails (password reset, etc.) are printed to the console
# instead of actually being sent anywhere.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
