from dashboard.models import *
from authentication.models import *
from django.contrib.auth.models import Group, Permission
import logging
from django.contrib.auth.hashers import is_password_usable
from django.contrib.auth.models import Group, Permission
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from pathlib import Path

from django.conf import settings

import os

from .apps import CustomBackupConfig


class CustomRestore:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        self.json_path = Path(
            os.path.join(settings.BASE_DIR, CustomBackupConfig.JSON_FILENAME)
        )
        self.dumpinfo_path = Path(
            os.path.join(settings.BASE_DIR, CustomBackupConfig.DUMPINFO)
        )

    def restore_individual_student(self, data, version=1, soft=False):
        if soft:
            try:
                student = Student.objects.get(shield_id=data["shield_id"])
            except Student.DoesNotExist:
                change = StudentChange.objects.create(
                    shield_id=data["shield_id"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    class_name=data["class_name"],
                    child_email=data["student_email"],
                    operation=1,
                )
                change.save()
            else:
                student_change = StudentChange.objects.create(
                    student=student, operation=0
                )

                if student.first_name != data["first_name"]:
                    student_change.first_name = data["first_name"]
                    student_change.operation = 2
                if student.last_name != data["last_name"]:
                    student_change.last_name = data["last_name"]
                    student_change.operation = 2
                if student.class_name != data["class_name"]:
                    student_change.class_name = data["class_name"]
                    student_change.operation = 2
                if student.child_email != data["student_email"]:
                    student_change.child_email = data["student_email"]
                    student_change.operation = 2

                student_change.save()
        else:
            student, created = Student.objects.get_or_create(
                shield_id=data["shield_id"]
            )

            student.first_name = data["first_name"]
            student.last_name = data["last_name"]
            student.child_email = data["student_email"]
            student.class_name = data["class_name"]

            student.save()

    def restore_individual_upcomming_user(self, data, version=1, soft=False):
        if not soft:
            try:
                student = Student.objects.get(shield_id=data["student_shield_id"])
            except Student.DoesNotExist:
                self.logger.error(
                    "Restore error: Student with shield_id %s could not be found.",
                    data["student_shield_id"],
                )
            else:
                up_user, created = Upcomming_User.objects.get_or_create(student=student)

                if data["email_send"] and not created:
                    up_user.access_key = data["access_key"]
                    up_user.otp = data["otp"]
                    up_user.created = data["created"]
                    up_user.email_send = True
                    up_user.parent_email = data["parent_email"]
                    up_user.parent_registration_email_send = data[
                        "parent_registration_email_send"
                    ]
                    up_user.save()

    def restore_individual_tags(self, data, version=1, soft=False):
        tag, created = Tag.objects.get_or_create(
            name=data["name"],
            defaults={"synonyms": data["synonyms"], "color": data["color"]},
        )

        if not soft and not created:
            tag.synonyms = data["synonyms"]
            tag.color = data["color"]

    def restore_settings(self, data, version=1):
        try:
            settings = SiteSettings.objects.get(pk=1)
        except SiteSettings.DoesNotExist:
            settings = SiteSettings.objects.create(
                event_duration=timezone.timedelta(
                    seconds=float(data["event_duration"])
                ),
                impressum=data["impressum"],
                keep_events=timezone.timedelta(seconds=float(data["keep_events_for"])),
                delete_events=data["delete_events"],
                keep_student_changes=timezone.timedelta(
                    seconds=data["keep_student_changes_for"]
                ),
                delete_student_changes=data["delete_student_changes"],
                keep_announcements=timezone.timedelta(
                    seconds=float(data["keep_announcements_for"])
                ),
                delete_announcements=data["delete_announcements"],
                keep_event_change_formulas=timezone.timedelta(
                    float(seconds=data["keep_formulars_for"])
                ),
                delete_event_change_formulas=data["delete_formulars"],
                iquiry_bahvior=data["inquiry_behaviour"],
            )
        else:
            settings.event_duration = timezone.timedelta(
                seconds=float(data["event_duration"])
            )
            settings.impressum = data["impressum"]
            settings.keep_events = timezone.timedelta(
                seconds=float(data["keep_events_for"])
            )
            settings.delete_events = data["delete_events"]
            settings.keep_student_changes = timezone.timedelta(
                seconds=data["keep_student_changes_for"]
            )
            settings.delete_student_changes = data["delete_student_changes"]
            settings.keep_announcements = timezone.timedelta(
                seconds=float(data["keep_announcements_for"])
            )
            settings.delete_announcements = data["delete_announcements"]
            settings.keep_event_change_formulas = timezone.timedelta(
                seconds=float(data["keep_formulars_for"])
            )
            settings.delete_event_change_formulas = data["delete_formulars"]
            settings.iquiry_bahvior = data["inquiry_behaviour"]
            settings.save()

    def restore_individual_groups(self, data, version=1):
        group, created = Group.objects.get_or_create(name=data["group_name"])
        group_permissions = Permission.objects.filter(pk__in=data["group_permissions"])
        group.permissions.set(group_permissions)

    def restore_individual_custom_user(self, data: dict, force=False):
        user, created = CustomUser.objects.get_or_create(
            email=data["email"], defaults={"role": data["role"]}
        )
        if user.role != data["role"] and not force:
            self.logger.warning("The role of %s was changed. Breaking backup restore")
        else:
            user.role = data["role"]
            user.first_name = data["first_name"]
            user.last_name = data["last_name"]
            user.is_active = data["is_active"]
            user.is_staff = data["is_staff"]
            user.is_superuser = data["is_superuser"]
            user.save()

            if is_password_usable(data["password"]):
                user.password = data["password"]
                user.save()
            else:
                user.set_unusable_password()  # TODO: Hier sollte automatisch eine Reset Email an den Nutzer gesendet werden.
                print("An unusable password was set")

            user.groups.set(Group.objects.filter(pk__in=data["groups"]).all())
            user.user_permissions.set(
                Permission.objects.filter(pk__in=data["permissions"])
            )
        match user.role:
            case 0:
                user.students.set(
                    Student.objects.filter(shield_id__in=data["students"])
                )
            case 1:
                extra_data, created = TeacherExtraData.objects.get_or_create(
                    teacher=user
                )

                extra_data.acronym = data.get("acronym", "")
                extra_data.save()
                extra_data.tags.set(Tag.objects.filter(name__in=data.get("tags", [])))

    def restore(self, data, flush=False, soft=False):
        settings_data = data["settings"]
        students_data = data["students"]
        tags_data = data["tags"]
        groups_data = data["groups"]
        upcomming_user_data = data["upcomming_users"]
        custom_user_data = data["custom_user"]

        self.restore_settings(settings_data["data"], settings_data["version"])
        for student in students_data["data"]:
            self.restore_individual_student(
                student, version=students_data["version"], soft=soft
            )
        for tag in tags_data["data"]:
            self.restore_individual_tags(tag, tags_data["version"], soft=soft)
        for group in groups_data["data"]:
            self.restore_individual_groups(group, groups_data["version"])
        for up_user in upcomming_user_data["data"]:
            self.restore_individual_upcomming_user(
                up_user, upcomming_user_data["version"], soft
            )
        for custom_user in custom_user_data["data"]:
            self.restore_individual_custom_user(custom_user)

    def create_tar_file(self):
        pass

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
            progress_recorder.set_progress(
                index, len(tags_data["data"]), "Restoring tags"
            )
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
