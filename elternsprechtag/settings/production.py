from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

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

# Celery Settings
CELERY_BROKER_URL = "redis://"+os.environ.get("REDIS_HOST")+":6379"
CELERY_RESULT_BACKEND = "redis://"+os.environ.get("REDIS_HOST")+":6379"
