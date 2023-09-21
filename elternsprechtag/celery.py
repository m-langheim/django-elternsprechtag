import os
from celery import Celery
from celery.schedules import crontab

import threading
import time

# from general_tasks.tasks import run_dbbackup

# os.environ.setdefault("DJANGO_SETTINGS_MODULE",
#                       "elternsprechtag.settings.development")  # ! Always needs to be changed befor build

app = Celery("elternsprechtag")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

print(os.environ.get("DJANGO_SETTINGS_MODULE"))


def thread_start_celery(app):
    time.sleep(2)
    argv = [
        "worker",
        "--loglevel=DEBUG",
    ]
    app.worker_main(argv)
    print("Celery started")


if os.environ.get("DJANGO_SETTINGS_MODULE") == "elternsprechtag.settings.development":
    threading.Thread(target=thread_start_celery, args=(app,)).start()


# @app.on_after_configure.connect
# def register_periodic_tasks(sender: Celery, **kwargs):
#     sender.add_periodic_task(10.0, run_dbbackup.s())
