import django_tables2 as tables
from django_tables2.utils import Accessor
from authentication.models import Student, StudentChange, CustomUser
from dashboard.models import Event, EventChangeFormula
from django.utils.html import format_html


class StudentExtrainformaionColumn(tables.Column):
    def render(self, value):
        student = Student.objects.get(pk=value)

        column_text = ""

        if not student.parent():
            if not student.upcomming_user.email_send:
                column_text += (
                    "<i class='fa-solid fa-triangle-exclamation text-danger'></i>"
                )
            else:
                column_text += "<i class='fa-solid fa-user-plus text-warning'></i>"
        else:
            column_text += (
                "<i class='fa-solid fa-person-circle-check text-success'></i>"
            )
        return format_html(column_text)


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
    info = StudentExtrainformaionColumn(accessor="pk", orderable=False)
    details = tables.LinkColumn(
        "student_details_view",
        args=[Accessor("pk")],
        orderable=False,
        text="View",
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
            "start_time",
            "end_time",
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

    # administrative_event_formular_edit_view
    edit = tables.LinkColumn(
        "administrative_event_formular_edit_view",
        args=[Accessor("pk")],
        orderable=False,
        text="Edit",
        attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
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

    # parent_edit_view
    edit = tables.LinkColumn(
        "parent_edit_view",
        args=[Accessor("pk")],
        orderable=False,
        text="Edit",
        attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    )


class TeachersTable(tables.Table):
    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "teacherextradata.acronym",
            "teacherextradata.tags",
        )

    # teachers_edit_view
    edit = tables.LinkColumn(
        "teachers_edit_view",
        args=[Accessor("pk")],
        orderable=False,
        text="Edit",
        attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    )


class EventExtraInformationColumn(tables.Column):
    def render(self, value):
        event = Event.objects.get(pk=value)

        column_text = ""

        if not event.lead_status == 0:
            match event.status:
                case 1:
                    column_text += "<i class='fa-solid fa-circle-xmark'></i>"
                case 2:
                    column_text += "<i class='fa-solid fa-file-contract'></i>"
            match event.lead_status:
                case 1:
                    column_text += "<i class='fa-solid fa-notes-medical'></i>"
                case 2:
                    column_text += "<i class='fa-solid fa-code-pull-request'></i>"
        else:
            column_text += "<i class='fa-solid fa-lock text-danger'></i>"
        return format_html(column_text)


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
    view = tables.LinkColumn(
        "administrative_event_detail_view",
        args=[Accessor("pk")],
        orderable=False,
        text="View",
        attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    )
    info = EventExtraInformationColumn(accessor="pk", orderable=False)
