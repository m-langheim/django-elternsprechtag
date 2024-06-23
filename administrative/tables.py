import django_tables2 as tables
from django_tables2.utils import Accessor
from authentication.models import Student, StudentChange, CustomUser
from dashboard.models import Event, EventChangeFormula


class StudentTable(tables.Table):
    class Meta:
        model = Student
        # template_name = "administrative/student_list_view.html"
        fields = (
            "first_name",
            "last_name",
            "child_email",
            "class_name",
        )

    child_email = tables.EmailColumn(orderable=False)
    parent = tables.Column(accessor="parent", orderable=False)
    details = tables.LinkColumn(
        "student_details_view",
        args=[Accessor("pk")],
        orderable=False,
        text="View",
        attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    )
    edit = tables.LinkColumn(
        "student_edit_view",
        args=[Accessor("pk")],
        orderable=False,
        text="Edit",
        attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    )


class StudentChangeTable(tables.Table):
    class Meta:
        model = StudentChange
        # template_name = "administrative/student_list_view.html"
        fields = (
            "pk",
            "student.first_name",
        )

    apply = tables.LinkColumn(
        "student_import_apply_change",
        args=[Accessor("pk")],
        orderable=False,
        text="Apply",
        attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    )


class EventFormularActionTable(tables.Table):
    class Meta:
        model = EventChangeFormula
        fields = (
            "type",
            "teacher",
            "date",
        )

    approve = tables.LinkColumn(
        "administrative_event_formular_approve_view",
        args=[Accessor("pk")],
        orderable=False,
        text="Approve",
        attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    )
    disapprove = tables.LinkColumn(
        "administrative_event_formular_disapprove_view",
        args=[Accessor("pk")],
        orderable=False,
        text="Disapprove",
        attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    )


class EventFormularUpcommingTable(tables.Table):
    class Meta:
        model = EventChangeFormula
        fields = (
            "type",
            "teacher",
            "date",
        )


class EventFormularOldTable(tables.Table):
    class Meta:
        model = EventChangeFormula
        fields = (
            "type",
            "teacher",
            "date",
            "status",
        )

    result = tables.BooleanColumn(null=True)


class ParentsTable(tables.Table):
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "students")


class TeachersTable(tables.Table):
    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "teacherextradata.acronym",
            "teacherextradata.tags",
        )


class Eventstable(tables.Table):
    class Meta:
        model = Event
        fields = ("teacher.teacherextradata.acronym", "start", "status")

    block = tables.LinkColumn(
        "administrative_event_block_view",
        args=[Accessor("pk")],
        orderable=False,
        text="Block",
        attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    )
