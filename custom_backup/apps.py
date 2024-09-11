from django.apps import AppConfig
from pathlib import Path

import pkg_resources
import logging

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class CustomBackupConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "custom_backup"

    PROJECT_NAME = Path(settings.BASE_DIR).name
    JSON_FILENAME = "django-backup-utils-fullbackup.json"
    DUMPINFO = "django-backup-utils-backup-info.txt"

    try:
        BACKUP_DIRS = settings.BACKUP_DIRS
    except AttributeError:
        BACKUP_DIRS = []

    if BACKUP_DIRS:
        # check for dirs
        for directory in BACKUP_DIRS:
            if not Path.is_dir(Path(directory)):
                logger.warning(
                    f"The configured BACKUP_DIR {Path(directory)} does not exist."
                )
