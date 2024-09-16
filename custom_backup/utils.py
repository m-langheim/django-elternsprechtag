from dashboard.models import *
from authentication.models import *
from django.contrib.auth.models import Group, Permission
import logging
from django.contrib.auth.hashers import is_password_usable
from django.contrib.auth.models import Group, Permission
from celery import shared_task
from celery_progress.backend import ProgressRecorder

import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile
import unittest
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .exceptions import MigrationNotFound, LoadException, UnittestFailed

module = str(__name__).split(".")[-1]
logger = logging.getLogger(__name__)


def flush_db():
    logger.debug("flushing db...")
    command = f"{sys.executable} {settings.BASE_DIR}/manage.py flush --noinput"
    output = subprocess.getoutput(command)
    logger.debug("db has been flushed")


def delete_dir(dir, **kwargs):
    dir = Path(dir)
    if dir.exists():
        shutil.rmtree(dir)
    if dir.exists():
        raise LoadException(
            message=f"directory could not be deleted", output=dir, **kwargs
        )
    else:
        logger.debug(f"deleted directory {dir}")


def open_tar(input_filename):
    if str(input_filename).endswith("tar.gz"):
        tar = tarfile.open(input_filename, "r:gz")
    elif str(input_filename).endswith("tar"):
        tar = tarfile.open(input_filename, "r:")
    return tar


def check_member(input_filename, member_path, strip=0):
    logger.debug(f"check for data in backup... {member_path}")
    tar = open_tar(input_filename)
    for member in tar.getmembers():
        if member.name in member_path:
            return member.name


def delete_dir(dir, **kwargs):
    dir = Path(dir)
    if dir.exists():
        shutil.rmtree(dir)
    if dir.exists():
        raise LoadException(
            message=f"directory could not be deleted", output=dir, **kwargs
        )
    else:
        logger.debug(f"deleted directory {dir}")
