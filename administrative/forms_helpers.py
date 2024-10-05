from dashboard.models import Student, Event


def get_students_choices_for_event(event: Event):
    if event.parent:
        choices = [
            (student.id, student.first_name + " " + student.last_name)
            for student in event.parent.students.all()
        ]
        for student in event.student.all():
            try:
                choices.remove(
                    (student.id, student.first_name + " " + student.last_name)
                )
            except:
                pass
    else:
        choices = [
            (student.id, student.first_name + " " + student.last_name)
            for student in Student.objects.all()
        ]

    return choices
