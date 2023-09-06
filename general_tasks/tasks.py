from celery import shared_task, Celery
from elternsprechtag.celery import app
from django.core import management
import logging

logger = logging.getLogger(__name__)


@shared_task
def run_dbbackup(**kwargs):
    logger.info("Databse Backup initiated...")
    management.call_command("dbbackup")

    logger.info("Media Backup initiated...")
    management.call_command("mediabackup")
