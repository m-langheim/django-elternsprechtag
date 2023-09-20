# import os
# from celery import Celery
# from celery.schedules import crontab

# # from general_tasks.tasks import run_dbbackup

# os.environ.setdefault("DJANGO_SETTINGS_MODULE",
#                       "elternsprechtag.settings.development")  # ! Always needs to be changed befor build

# app = Celery("elternsprechtag")
# app.config_from_object("django.conf:settings", namespace="CELERY")

# app.autodiscover_tasks()


# # @app.on_after_configure.connect
# # def register_periodic_tasks(sender: Celery, **kwargs):
# #     sender.add_periodic_task(10.0, run_dbbackup.s())
