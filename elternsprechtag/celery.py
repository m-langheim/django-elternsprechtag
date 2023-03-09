import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "elternsprechtag.settings.production")  # ! Always needs to be changed befor build

app = Celery("elternsprechtag")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
