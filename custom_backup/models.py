from django.db import models
from django.utils import timezone
from django.conf import settings

# Create your models here.


class MainAttributes(models.Model):
    backup = models.TextField()
    params = models.TextField(null=True, blank=True)
    size_bytes = models.BigIntegerField(null=True, blank=True)

    class Meta:
        abstract = True


class Backup(models.Model):
    backup_file = models.FilePathField(path=settings.BACKUP_ROOT)
    # inconsistent migrations occur if your migration recorder does not match your local migration files
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Backup {self.pk}"

    class Meta:
        permissions = (("can_restore_backup", "Can restore backup"),)


class BackupLog(MainAttributes):
    message = models.CharField(max_length=200)
    output = models.TextField(null=True, blank=True)
    success = models.BooleanField(default=False)
    executed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BackupLog {self.pk}"
