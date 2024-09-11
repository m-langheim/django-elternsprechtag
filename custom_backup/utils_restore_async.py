from dashboard.models import *
from authentication.models import *
from django.contrib.auth.models import Group, Permission
import logging
from django.contrib.auth.hashers import is_password_usable
from django.contrib.auth.models import Group, Permission
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from .utils_restore import CustomRestore

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


@shared_task(bind=True)
def restore_async(self, data, flush=False, soft=False):
    restorer = CustomRestore

    progress_recorder = ProgressRecorder(self)

    settings_data = data["settings"]
    students_data = data["students"]
    tags_data = data["tags"]
    groups_data = data["groups"]
    upcomming_user_data = data["upcomming_users"]
    custom_user_data = data["custom_user"]

    progress_recorder.set_progress(0, 1, "Restoring settings")
    restorer.restore_settings(settings_data["data"], settings_data["version"])
    progress_recorder.set_progress(1, 1, "Restoring settings")
    for index, student in enumerate(students_data["data"]):
        restorer.restore_individual_student(
            student, version=students_data["version"], soft=soft
        )
        progress_recorder.set_progress(
            index, len(students_data["data"]), "Restoring students"
        )
    for index, tag in tags_data["data"]:
        restorer.restore_individual_tags(tag, tags_data["version"], soft=soft)
        progress_recorder.set_progress(index, len(tags_data["data"]), "Restoring tags")
    for index, group in enumerate(groups_data["data"]):
        restorer.restore_individual_groups(group, groups_data["version"])
        progress_recorder.set_progress(
            index, len(groups_data["data"]), "Restoring groups"
        )
    for index, up_user in enumerate(upcomming_user_data["data"]):
        restorer.restore_individual_upcomming_user(
            up_user, upcomming_user_data["version"], soft
        )
        progress_recorder.set_progress(
            index, len(upcomming_user_data["data"]), "Restoring upcomming users"
        )
    for index, custom_user in enumerate(custom_user_data["data"]):
        restorer.restore_individual_custom_user(custom_user)
        progress_recorder.set_progress(
            index, len(custom_user_data["data"]), "Restoring users"
        )
