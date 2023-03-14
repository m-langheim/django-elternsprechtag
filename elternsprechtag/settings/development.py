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

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'django.server': {
#             '()': 'django.utils.log.ServerFormatter',
#             'format': '[{server_time}] {message}',
#             'style': '{',
#         }
#     },
#     'handlers': {
#         'file_warning': {
#             'class': 'logging.FileHandler',
#             'filename': os.path.join(BASE_DIR, 'logs/essential.log'),
#             'formatter': 'django.server',
#         },
#         'console': {
#             'level': 'INFO',
#             'class': 'logging.StreamHandler',
#             'formatter': 'django.server',
#         },
#     },
#     'loggers': {
#         'django.server': {
#             'handlers': ['file_warning', 'console'],
#             'level': 'INFO',
#             'propagate': True,
#         }
#     },
# }


# Django-Email Setup
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'emails')
EMAIL_HOST_USER = "test@examle.com"
EMAIL_COMPLETE = "test@example.com"

# Celery Settings
CELERY_BROKER_URL = "redis://localhost:6379"
CELERY_RESULT_BACKEND = "redis://localhost:6379"
