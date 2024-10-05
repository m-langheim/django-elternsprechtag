from dashboard.models import *
from authentication.models import *
from django.contrib.auth.models import Group, Permission
import logging
from pathlib import Path
from django.conf import settings
import os
from .apps import CustomBackupConfig
import json
from json import JSONEncoder
import tarfile
from .exceptions import MigrationNotFound, CreateException, BackupAlreadyPresent
import socket
from .models import Backup
import hashlib
import inspect
import logging
import os
import socket
import tarfile
from pathlib import Path
from distutils.util import strtobool
from django.conf import settings
from django.db.migrations.recorder import MigrationRecorder
from django.db.models import Count, Max

logger = logging.getLogger(__name__)


def get_validation_hash(json_data: json, created_at: timezone.datetime):
    return hashlib.sha512(
        str(json_data + created_at.isoformat() + settings.SECRET_KEY).encode("utf-8")
    ).hexdigest()


def extract_dumpinfo(tarpath):
    logger.debug(f"extract_dumpinfo({tarpath})")
    dump_info = tarfile.open(str(tarpath), "r")
    dump_info = dump_info.extractfile(f"{CustomBackupConfig.DUMPINFO}").readlines()
    created_at = dump_info[0].decode("UTF-8").strip().split(";")[1]
    logger.debug(f"created_at: {created_at}")
    # dump_version = dump_info[1].decode("UTF-8").strip().split(";")[1]
    # logger.debug(f"dump_version: {dump_version}")
    # system_migrations_migrated = dump_info[2].decode("UTF-8").strip().split(";")[1]
    # logger.debug(f"system_migrations_migrated: {system_migrations_migrated}")
    # dump_migration_files = dump_info[3].decode("UTF-8").strip().split(";")[1]
    # logger.debug(f"dump_migration_files: {dump_migration_files}")
    # consistent_migrations = strtobool(
    #     dump_info[4].decode("UTF-8").strip().split(";")[1]
    # )
    # logger.debug(f"consistent_migrations: {consistent_migrations}")
    # params = dump_info[5].decode("UTF-8").strip().split(";")[1]
    # logger.debug(f"params: {params}")
    backup_directories = dump_info[1].decode("UTF-8").strip().split(";")[1]
    logger.debug(f"backup_directories: {backup_directories}")
    # django_backup_utils_version = dump_info[7].decode("UTF-8").strip().split(";")[1]
    # logger.debug(f"django_backup_utils_version: {django_backup_utils_version}")
    validation_hash = dump_info[2].decode("UTF-8").strip().split(";")[1]

    return {
        "created_at": created_at,
        "backup_directories": backup_directories,
        "validation_hash": validation_hash,
    }


def extract_json_data(tarpath):
    logger.debug(f"extract_json_data({tarpath})")
    tar = tarfile.open(str(tarpath), "r")
    json_file = tar.extractfile(f"{CustomBackupConfig.JSON_FILENAME}").read()
    data = json.loads(json_file)

    return data


def hande_uploaded_file(tarpath):
    try:
        dump_info = extract_dumpinfo(Path(tarpath))
        data = extract_json_data(Path(tarpath))
    except:
        os.remove(Path(tarpath))
        raise FileNotFoundError

    created_at = timezone.datetime.fromisoformat(dump_info["created_at"])
    validation_hash = dump_info["validation_hash"]

    if Backup.objects.filter(validation_hash=validation_hash):
        raise BackupAlreadyPresent("The uploaded backup is already present on the host")
    else:
        Backup.objects.create(
            backup_type=Backup.BackupTypeChoices.UPLOAD,
            backup_file=tarpath,
            backup_directories=dump_info["backup_directories"],
            size_bytes=Path(tarpath).stat().st_size,
            keep_backup=True,
            validation_hash=validation_hash,
            external=get_validation_hash(json.dumps(data), created_at)
            != validation_hash,
            created_at=created_at,
        )
