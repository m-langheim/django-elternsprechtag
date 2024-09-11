from django.test import TestCase
from authentication.factories import *
from dashboard.factories import SettingsFactory
from .utils_backup import *


# Create your tests here.
class BackupTestCase(TestCase):
    def setUp(self) -> None:
        StudentFactory.create_batch(200)
        ParentFactory.create_batch(150)
        SettingsFactory.create()
        TagFactory.create_batch(10)

    def test_student_backup(self):
        backupper = CustomBackup()
        self.assertEqual(
            len(backupper.backup_students()), Student.objects.all().count()
        )
