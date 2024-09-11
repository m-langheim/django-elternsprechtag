from dashboard.models import *
from authentication.models import *
from django.contrib.auth.models import Group, Permission
import logging
from pathlib import Path
from django.conf import settings
import os
from .apps import CustomBackupConfig
import json
import tarfile
from .exceptions import MigrationNotFound, CreateException
import socket
from .models import Backup


class CustomBackup:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        self.json_path = Path(
            os.path.join(settings.BACKUP_ROOT, CustomBackupConfig.JSON_FILENAME)
        )
        self.dumpinfo_path = Path(
            os.path.join(settings.BACKUP_ROOT, CustomBackupConfig.DUMPINFO)
        )
        self.created_at = timezone.now()

    def backup_upcomming_users(self):
        upcomming_user_dict = []
        for up_user in Upcomming_User.objects.all():
            if up_user.email_send:
                upcomming_user_dict.append(
                    {
                        "access_key": up_user.access_key,
                        "otp": up_user.otp,
                        "created": up_user.created,
                        "student_shield_id": up_user.student.shield_id,
                        "email_send": True,
                        "parent_email": up_user.parent_email,
                        "parent_registration_email_send": up_user.parent_registration_email_send,
                    }
                )
            else:
                upcomming_user_dict.append(
                    {
                        "student_shield_id": up_user.student.shield_id,
                        "email_send": False,
                    }
                )
        return upcomming_user_dict

    def backup_students(self):
        student_dict = []
        for student in Student.objects.all():
            student_dict.append(
                {
                    "shield_id": student.shield_id,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "student_email": student.child_email,
                    "class_name": student.class_name,
                    "parent_registered": student.registered,
                }
            )
        return student_dict

    def backup_tags(self):
        tag_dict = []
        for tag in Tag.objects.all():
            tag_dict.append(
                {"name": tag.name, "synonyms": tag.synonyms, "color": tag.color}
            )
        return tag_dict

    def backup_custom_user(self):
        user_dict = []
        for user in CustomUser.objects.all():
            match user.role:
                case 0:
                    user_dict.append(
                        {
                            "email": user.email,
                            "role": 0,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "students": [
                                student.shield_id for student in user.students.all()
                            ],
                            "is_active": user.is_active,
                            "permissions": [
                                permission.pk
                                for permission in user.user_permissions.all()
                            ],
                            "is_staff": False,
                            "is_superuser": user.is_superuser,
                            "password": user.password,
                            "groups": [group.name for group in user.groups.all()],
                        }
                    )
                case 1:
                    try:
                        extra_data = user.teacherextradata.first()
                    except:
                        user_dict.append(
                            {
                                "email": user.email,
                                "role": 1,
                                "first_name": user.first_name,
                                "last_name": user.last_name,
                                "is_active": user.is_active,
                                "permissions": [
                                    permission.pk
                                    for permission in user.user_permissions.all()
                                ],
                                "is_staff": True,
                                "is_superuser": user.is_superuser,
                                "password": user.password,
                                "groups": [group.name for group in user.groups.all()],
                            }
                        )
                    else:
                        user_dict.append(
                            {
                                "email": user.email,
                                "role": 1,
                                "first_name": user.first_name,
                                "last_name": user.last_name,
                                "acronym": extra_data.acronym,
                                "tags": [tag.name for tag in extra_data.tags.all()],
                                "is_active": user.is_active,
                                "permissions": [
                                    permission.pk
                                    for permission in user.user_permissions.all()
                                ],
                                "is_staff": True,
                                "is_superuser": user.is_superuser,
                                "password": user.password,
                                "groups": [group.name for group in user.groups.all()],
                            }
                        )
                case 2:
                    user_dict.append(
                        {
                            "email": user.email,
                            "role": 2,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "is_active": user.is_active,
                            "permissions": [
                                permission.pk
                                for permission in user.user_permissions.all()
                            ],
                            "is_staff": user.is_staff,
                            "is_superuser": user.is_superuser,
                            "password": user.password,
                            "groups": [group.name for group in user.groups.all()],
                        }
                    )
        return user_dict

    def backup_groups(self):
        group_dict = []
        for group in Group.objects.all():
            group_dict.append(
                {
                    "group_name": group.name,
                    "group_permissions": [
                        permission.pk for permission in group.permissions.all()
                    ],
                }
            )
        return group_dict

    def backup_settings(self):
        settings = SiteSettings.objects.first()
        settings_dict = {
            "event_duration": settings.event_duration.total_seconds(),
            "impressum": settings.impressum,
            "keep_events_for": settings.keep_events.total_seconds(),
            "delete_events": settings.delete_events,
            "keep_student_changes_for": settings.keep_student_changes.total_seconds(),
            "delete_student_changes": settings.delete_student_changes,
            "keep_announcements_for": settings.keep_announcements.total_seconds(),
            "delete_announcements": settings.delete_announcements,
            "keep_formulars_for": settings.keep_event_change_formulas.total_seconds(),
            "delete_formulars": settings.delete_event_change_formulas,
            "inquiry_behaviour": settings.iquiry_bahvior,
        }
        return settings_dict

    def get_backup_data(self):
        backup = {
            "upcomming_users": {
                "version": 1,
                "data": self.backup_upcomming_users(),
            },
            "students": {
                "version": 1,
                "data": self.backup_students(),
            },
            "tags": {
                "version": 1,
                "data": self.backup_tags(),
            },
            "groups": {
                "version": 1,
                "data": self.backup_groups(),
            },
            "custom_user": {
                "version": 1,
                "data": self.backup_custom_user(),
            },
            "settings": {
                "version": 1,
                "data": self.backup_settings(),
            },
        }

        return backup

    def create_backup_json_file(self):
        self.logger.debug(f"creating database dump: {self.json_path}")
        with open(self.dumpinfo_path, "w") as f:
            f.write(f"created_at;{timezone.now()}\n")
            f.write(f"backup_directories;{CustomBackupConfig.BACKUP_DIRS}\n")

        with open(self.json_path, "w") as f:
            f.write(json.dumps(self.get_backup_data()))

        if Path(self.json_path).is_file() and Path(self.dumpinfo_path).is_file():
            return Path(self.json_path), Path(self.dumpinfo_path)
        else:
            raise Exception("Error could not create database dump")

    def create_tar_file(
        self,
        output_path: Path,
        compress: bool,
        source_dirs: list,
        source_files: list,
        **kwargs,
    ):
        if compress:
            mode = "w:gz"
            suffix = ".tar.gz"
        else:
            mode = "w"
            suffix = ".tar"
        output_path = str(output_path) + suffix
        with tarfile.open(output_path, mode) as tar:
            for source_dir in source_dirs:
                if not Path(source_dir).is_absolute():
                    self.logger.debug(
                        f"add directory {source_dir} to tar: {output_path}"
                    )
                    tar.add(source_dir, arcname=Path(os.path.basename(source_dir)))
                else:
                    tar.add(source_dir, arcname=source_dir)
            for source_file in source_files:
                self.logger.debug(f"add file {source_file} to tar: {output_path}")
                tar.add(source_file, arcname=os.path.basename(source_file))
            # for migration in migrations:
            #     if Path(migration).exists():
            #         self.logger.debug(f"add file {migration} to tar: {output_path}")
            #         arcname = (
            #             f"_migration_backup/{migration.relative_to(settings.BASE_DIR)}"
            #         )
            #         tar.add(migration, arcname=arcname)
            #         self.dump_migration_files += 1
        if not Path(output_path).is_file():
            raise Exception("tarfile has not been created")

        Backup.objects.create(backup_file=Path(output_path))

        return output_path

    def create_backup_file(self, compress=False, silent=False, *args, **options):
        OUTPUT_DIR = Path(settings.BACKUP_ROOT)

        if not silent:
            print(f"create new backup in {settings.BACKUP_ROOT}, compress = {compress}")
        if not OUTPUT_DIR.is_dir():
            self.logger.debug(f"creating output_dir {OUTPUT_DIR}")
            os.makedirs(OUTPUT_DIR, exist_ok=True)

        for path in CustomBackupConfig.BACKUP_DIRS:
            posix = os.path.join(settings.BASE_DIR, path)
            posix = Path(posix)
            if not posix.is_dir():
                self.context["backup"] = "failed to create"
                raise CreateException(
                    f"directory does not exist", output=str(posix), **self.context
                )

        if self.json_path.exists():
            self.logger.debug(f"clean up remaining {self.json_path}")
            os.remove(self.json_path)

        if self.dumpinfo_path.exists():
            self.logger.debug(f"clean up remaining {self.dumpinfo_path}")
            os.remove(self.dumpinfo_path)

        JSON_FILE, DUMPINFO_FILE = self.create_backup_json_file()
        TAR_PREFIX = (
            str(socket.gethostname())
            + "_"
            + CustomBackupConfig.PROJECT_NAME
            + "_"
            + str(self.created_at.strftime("%Y-%m-%d_%H-%M-%S"))
        )
        OUTPUT_TAR = Path(f"{OUTPUT_DIR}/{TAR_PREFIX}")
        OUTPUT_TAR = self.create_tar_file(
            output_path=OUTPUT_TAR,
            source_dirs=CustomBackupConfig.BACKUP_DIRS,
            source_files=[JSON_FILE, DUMPINFO_FILE],
            compress=compress,
        )

        os.remove(Path(JSON_FILE).absolute())
        os.remove(Path(DUMPINFO_FILE).absolute())
