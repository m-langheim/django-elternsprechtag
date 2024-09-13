from celery import shared_task
from .utils_backup import CustomBackup


@shared_task
def automatic_backup():
    backup = CustomBackup(manual=False)
    backup.create_backup_file()
