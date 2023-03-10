from .base import *


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Added for testing purposes
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = [os.environ.get("PUBLIC_URL")]

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get("DB_NAME"),
        'USER': os.environ.get("DB_USER"),
        'PASSWORD': os.environ.get("DB_PASSWORD"),
        'HOST': os.environ.get("DB_HOST")
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", True)
EMAIL_PORT = os.environ.get("EEMAIL_PORT", 587)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")


# Celery Settings
CELERY_BROKER_URL = "redis://"+os.environ.get("REDIS_HOST")+":6379"
CELERY_RESULT_BACKEND = "redis://"+os.environ.get("REDIS_HOST")+":6379"
