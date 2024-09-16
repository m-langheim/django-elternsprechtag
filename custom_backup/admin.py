from django.contrib import admin
from .models import *

import logging

from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from .apps import CustomBackupConfig

from pathlib import Path
import os


logger = logging.getLogger(__name__)


# Register your models here.
class BackupAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "backup_file",
        "size_mb",
        "created_at",
        "backup_directories",
        # "dump_version",
        # "consistent_migrations",
        "backup_type",
        "external",
        "restore_link",
        # "system_migrations_migrated",
        # "dump_migration_files",
        # "custom_backup_version",
    )

    readonly_fields = (
        "backup_file",
        "size_bytes",
        "backup_type",
        "created_at",
        "backup_directories",
        "external",
        # "dump_version",
        # "consistent_migrations",
        # "system_migrations_migrated",
        # "dump_migration_files",
        # "params",
        # "custom_backup_version",
        "validation_hash",
    )
    list_display_links = (
        "pk",
        "restore_link",
    )

    change_list_template = "custom_backup/changelist.html"
    ordering = ("-created_at",)

    def changelist_view(self, request, extra_context=None):

        extra_context = {
            "backup_dirs": settings.BACKUP_DIRS,
            "custom_backup_version": CustomBackupConfig.CUSTOM_BACKUP_VERSION,
        }
        return super(BackupAdmin, self).changelist_view(request, extra_context)

    def has_add_permission(self, request, obj=None):
        return False

    def restore_link(self, obj):
        return mark_safe(
            f'<a href="{reverse_lazy("restore_backup", kwargs={"pk": obj.pk})}">restore</a> <a href="{reverse_lazy("download_backup", kwargs={"pk": obj.pk})}">download</a>'
        )

    def size_mb(self, obj):
        if obj.size_bytes:
            return f"{round(float(obj.size_bytes / 1000 / 1000), 4)} MB"
        return ""

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            backup = Path(obj.backup_file)
            if backup.is_file():
                os.remove(backup)
                logger.info(f"-> deleted file {backup}")
                BackupLog.objects.create(
                    message="deleted backup",
                    module="admin:backup_delete",
                    output=f"deleted {backup}",
                    size_bytes=obj.size_bytes,
                    success=True,
                )
                messages.success(request, f"deleted {obj.backup_file}")
            else:
                BackupLog.objects.create(
                    message="deleted backup object",
                    module="admin:backup_delete",
                    output=f"backup file was not found",
                )
                messages.info(
                    request,
                    f"deleted only object {obj}; ({obj.backup_file} was not found)",
                )
            obj.delete()


admin.site.register(Backup, BackupAdmin)
admin.site.register(BackupLog)
