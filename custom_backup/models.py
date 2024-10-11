from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from django.conf import settings

# Create your models here.


class MainAttributes(models.Model):
    params = models.TextField(null=True, blank=True)
    size_bytes = models.BigIntegerField(null=True, blank=True)

    class Meta:
        abstract = True


class Backup(models.Model):
    class BackupTypeChoices(models.TextChoices):
        AUTOMATIC = "A", "Automatically created backup"
        MANUAL = "M", "Manually created backup"
        UPLOAD = "U", "User-uploaded backup"

    backup_type = models.CharField(
        max_length=1, choices=BackupTypeChoices, default=BackupTypeChoices.AUTOMATIC
    )
    backup_file = models.FilePathField()
    backup_directories = models.TextField(null=True, blank=True)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    keep_backup = models.BooleanField(default=True)
    validation_hash = models.CharField(max_length=40, unique=True, null=True)
    external = models.BooleanField(
        default=False,
        help_text="Dies ist eine Angabe darüber, ob das Backup von einem Externen Server stammt oder extern modifiziert wurde.",
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Backup {self.pk}"

    class Meta:
        permissions = (
            ("can_restore_backup", _("Can restore backup")),
            ("can_add_backup", _("Can create a backup")),
        )


class BackupLog(MainAttributes):
    message = models.CharField(max_length=200)
    module = models.TextField(null=True)
    output = models.TextField(null=True, blank=True)
    success = models.BooleanField(default=False)
    executed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BackupLog {self.pk}"
