from django.apps import AppConfig


class GeneralTasksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "general_tasks"

    def ready(self) -> None:
        import threading
        from django.conf import settings

        from elternsprechtag.celery import app

        ## Celery is started here in dev mode

        def thread_start_celery(app):
            argv = [
                "worker",
                "--loglevel=DEBUG",
            ]
            app.worker_main(argv)
            print("Celery started")

        print(settings.RUN_CELERY_THREAD)

        if settings.RUN_CELERY_THREAD:
            threading.Thread(target=thread_start_celery, args=(app,)).start()
