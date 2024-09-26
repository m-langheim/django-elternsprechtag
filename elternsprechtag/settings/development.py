from .base import *
from celery.schedules import crontab

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "södfdsafölkdsalödsfpokewafpoewlkfaüir3qwolkfeäkfewfWKT$I$OKRPOKREWLKFD<LKNFD<OIU$OIJFEWÖJFEW"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

NAME = "development"

TIME_ZONE = "Europe/Berlin"

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
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
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = os.path.join(BASE_DIR, "emails")
EMAIL_HOST_USER = "test@examle.com"
EMAIL_COMPLETE = "test@example.com"

# Celery Settings
# CELERY_BROKER_URL = "sqla+sqlite:///" + os.path.join(BASE_DIR, 'db.sqlite3')
CELERY_BROKER_URL = "redis://localhost:6379"
CELERY_RESULT_BACKEND = "redis://localhost:6379"
CELERY_TIMEZONE = "Europe/Berlin"

# CELERY BEAT
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

RUN_CELERY_THREAD = False

# CELERY_BEAT_SCHEDULE = {
#     'db_backup_task': {
#         'task': 'general_tasks.tasks.run_dbbackup',
#         'schedule': crontab(minute=0, hour=1)
#     }
# }
# Backup settings
DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": os.path.join(BASE_DIR, "backup")}

CELERY_BEAT_SCHEDULE = {
    "initiateEventPDFs": {
        "task": "general_tasks.tasks.initiateEventPDFs",
        "schedule": crontab(minute="*/15"),
    },
    "look_for_open_inquiries": {
        "task": "general_tasks.tasks.look_for_open_inquiries",
        "schedule": crontab(minute="*/1"),
    },
    "dayly_cleanup_task": {
        "task": "general_tasks.tasks.dayly_cleanup_task",
        "schedule": crontab(minute="*/1"),
    },
    "update_lead_task": {
        "task": "general_tasks.tasks.update_event_lead_status",
        "schedule": crontab(minute="*/1"),
    },
}


CACHES = {
    "select2": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "elternsprechtag-select2",
    }
}

# Tell select2 which cache configuration to use:
SELECT2_CACHE_BACKEND = "select2"
