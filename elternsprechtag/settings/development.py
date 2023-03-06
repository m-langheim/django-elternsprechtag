from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "södfdsafölkdsalödsfpokewafpoewlkfaüir3qwolkfeäkfewfWKT$I$OKRPOKREWLKFD<LKNFD<OIU$OIJFEWÖJFEW"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True 


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Django-Email Setup
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'emails')

# Celery Settings
CELERY_BROKER_URL = "redis://localhost:6379"
CELERY_RESULT_BACKEND = "redis://localhost:6379"
