import logging
from .base import *
from celery.schedules import crontab


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

NAME = "production"

TIME_ZONE = os.environ.get("TZ")


# Added for testing purposes
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [os.environ.get("PUBLIC_URL")]

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{server_time}] {message}",
            "style": "{",
        }
    },
    "handlers": {
        # 'file_warning': {
        #     'class': 'logging.FileHandler',
        #     'filename': '/var/log/django.debug.log',
        #     'formatter': 'django.server',
        # },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
    },
    "root": {
        # 'handlers': ['file_warning', 'console'],
        "handlers": ["console"],
        "level": "DEBUG",
    },
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", True)
EMAIL_PORT = os.environ.get("EMAIL_PORT", 587)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_COMPLETE = os.environ.get("EMAIL_COMPLETE")
DEFAULT_FROM_EMAIL = os.environ.get("EMAIL_COMPLETE")

# Celery Settings
# CELERY_RESULT_BACKEND = 'django-db'
CELERY_BROKER_URL = "redis://" + os.environ.get("REDIS_HOST") + ":6379"
CELERY_TIMEZONE = os.environ.get("TZ")
# CELERY BEAT
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CELERY_BEAT_SCHEDULE = {
    # "db_backup_task": {
    #     "task": "general_tasks.tasks.run_dbbackup",
    #     "schedule": crontab(minute=0, hour=1),
    # },
    "initiateEventPDFs": {
        "task": "general_tasks.tasks.initiateEventPDFs",
        "schedule": crontab(minute=0, hour=3),
    },
    "look_for_open_inquiries": {
        "task": "general_tasks.tasks.look_for_open_inquiries",
        "schedule": crontab(minute=0, hour=6, day_of_week=1),
    },
    "update_date_lead_status": {
        "task": "general_tasks.tasks.update_date_lead_status",
        "schedule": crontab(minute=0, hour=2),
    },
    "update_lead_task": {
        "task": "general_tasks.tasks.update_event_lead_status",
        "schedule": crontab(minute=30, hour=1),
    },
}

# RUN_CELERY_THREAD = False

# Backup configuration
# if os.environ.get("USE_FTP_BACKUP", False):
#     if (
#         not os.environ.get("FTP_USERNAME")
#         or not os.environ.get("FTP_USER_PASSWORD")
#         or not os.environ.get("FTP_SERVER")
#     ):
#         raise "Es sind nicht alle Daten angegeben um ein Backup auf einen FTP Server durchzuführen"
#     DBBACKUP_STORAGE = "storages.backends.ftp.FTPStorage"
#     DBBACKUP_STORAGE_OPTIONS = {
#         "location": "ftp://"
#         + os.environ.get("FTP_USERNAME")
#         + ":"
#         + os.environ.get("FTP_USER_PASSWORD")
#         + "@"
#         + os.environ.get("FTP_SERVER")
#         + ":"
#         + os.environ.get("FTP_PORT", 21)
#     }
# else:
#     DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
#     DBBACKUP_STORAGE_OPTIONS = {"location": os.path.join(BASE_DIR, "backup")}

# DBBACKUP_SERVER_EMAIL = os.environ.get("EMAIL_COMPLETE")
# DBBACKUP_CLEANUP_KEEP = 30
# DBBACKUP_CLEANUP_KEEP_MEDIA = 30


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://" + os.environ.get("REDIS_HOST") + ":6379",
    },
    "select2": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://" + os.environ.get("REDIS_HOST") + ":6379",
    },
}

SELECT2_CACHE_BACKEND = "select2"
