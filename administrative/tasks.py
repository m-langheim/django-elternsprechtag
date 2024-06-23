from celery import shared_task
from authentication.models import StudentChange, Student
import csv, io, os
from celery_progress.backend import ProgressRecorder
from django.utils import timezone
from django.db.models import Q


@shared_task(bind=True)
def process_studentimport_fileupload(self, csv_file, *args, **kwargs):
    reader = csv.DictReader(io.StringIO(csv_file), delimiter=";")

    reader_list = list(reader)
    progress_recorder = ProgressRecorder(self)
    length = len(reader_list)

    shield_ids = []
    for index, line in enumerate(reader_list):
        shield_ids.append(line["eindeutige Nummer (GUID)"])
        try:
            student = Student.objects.get(shield_id=line["eindeutige Nummer (GUID)"])
        except Student.DoesNotExist:
            change = StudentChange.objects.create(
                shield_id=line["eindeutige Nummer (GUID)"],
                first_name=line["Vorname"],
                last_name=line["Nachname"],
                class_name=line["Klasse"],
                child_email=line["Mailadresse"],
                operation=1,
            )
            change.save()
        else:
            student_change = StudentChange.objects.create(student=student, operation=0)

            if student.first_name != line["Vorname"]:
                student_change.first_name = line["Vorname"]
                student_change.operation = 2
            if student.last_name != line["Nachname"]:
                student_change.last_name = line["Nachname"]
                student_change.operation = 2
            if student.class_name != line["Klasse"]:
                student_change.class_name = line["Klasse"]
                student_change.operation = 2
            if student.child_email != line["Mailadresse"]:
                student_change.child_email = line["Mailadresse"]
                student_change.operation = 2

            student_change.save()
        progress_recorder.set_progress(index, length, description="Processing File")

    unmentioned_students = Student.objects.all().exclude(shield_id__in=shield_ids)
    for index, un_student in enumerate(unmentioned_students):
        StudentChange.objects.create(student=un_student, operation=3)
        progress_recorder.set_progress(
            index,
            len(list(unmentioned_students)),
            description="Adding deletion entries",
        )

    return "Task finished"


@shared_task(bind=True)
def apply_student_changes(self):
    approved_changes = StudentChange.objects.filter(Q(approved=True), Q(applied=False))

    progress_recorder = ProgressRecorder(self)
    progress_recorder.total = len(approved_changes)

    for change in approved_changes:
        if change.operation == 0:
            change.applied = True
            change.applied_time = timezone.now()
            change.save()
        elif change.operation == 1:
            student = Student.objects.create(
                shield_id=change.shield_id,
                first_name=change.first_name,
                last_name=change.last_name,
                class_name=change.class_name,
                child_email=change.child_email,
            )
            student.save()
            change.student = student
            change.applied = True
            change.applied_time = timezone.now()
            change.save()
        elif change.operation == 2:
            student = change.student
            if change.first_name:
                student.first_name = change.first_name
            if change.last_name:
                student.last_name = change.last_name
            if change.class_name:
                student.class_name = change.class_name
            if change.child_email:
                student.child_email = change.child_email
            student.save()
            change.applied = True
            change.applied_time = timezone.now()
            change.save()
        elif change.operation == 3:
            student = change.student
            change.shield_id = student.shield_id
            change.first_name = student.first_name
            change.last_name = student.last_name
            change.child_email = student.child_email
            change.class_name = student.class_name
            change.applied = True
            change.applied_time = timezone.now()
            change.save()
            student.delete()

        progress_recorder.increment_progress()


@shared_task(bind=True)
def apply_and_approve_student_changes(self, changes_list):
    approved_changes = StudentChange.objects.filter(
        Q(approved=False), Q(applied=False), Q(pk__in=changes_list)
    )

    progress_recorder = ProgressRecorder(self)
    progress_recorder.total = len(approved_changes)

    for change in approved_changes:
        if change.operation == 0:
            change.applied = True
            change.approved = True
            change.applied_time = timezone.now()
            change.save()
        elif change.operation == 1:
            student = Student.objects.create(
                shield_id=change.shield_id,
                first_name=change.first_name,
                last_name=change.last_name,
                class_name=change.class_name,
                child_email=change.child_email,
            )
            student.save()
            change.student = student
            change.applied = True
            change.approved = True
            change.applied_time = timezone.now()
            change.save()
        elif change.operation == 2:
            student = change.student
            if change.first_name:
                student.first_name = change.first_name
            if change.last_name:
                student.last_name = change.last_name
            if change.class_name:
                student.class_name = change.class_name
            if change.child_email:
                student.child_email = change.child_email
            student.save()
            change.applied = True
            change.approved = True
            change.applied_time = timezone.now()
            change.save()
        elif change.operation == 3:
            student = change.student
            change.shield_id = student.shield_id
            change.first_name = student.first_name
            change.last_name = student.last_name
            change.child_email = student.child_email
            change.class_name = student.class_name
            change.applied = True
            change.approved = True
            change.applied_time = timezone.now()
            change.save()
            student.delete()

        progress_recorder.increment_progress()

    return "All changes applied"
