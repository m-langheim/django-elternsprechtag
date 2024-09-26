import django_tables2 as tables
from django_tables2.utils import Accessor
from authentication.models import Student, StudentChange, CustomUser
from dashboard.models import Event, EventChangeFormula
from django.utils.html import format_html
from django.template.loader import render_to_string
from custom_backup.models import *
from django.utils.translation import gettext as _
from django_tables2.utils import A
from django.urls import reverse_lazy


class StudentExtrainformaionColumn(tables.Column):
    def render(self, value):
        student = Student.objects.get(pk=value)

        column_text = ""

        if not student.parent():
            if not student.upcomming_user.email_send:
                column_text += (
                    "<i class='fa-solid fa-triangle-exclamation text-danger fs-5'></i>"
                )
            else:
                column_text += "<i class='fa-regular fa-clock text-warning fs-5'></i>"
        return format_html(column_text)


class StudentParentLinkColumn(tables.Column):
    def render(self, value):
        student = Student.objects.get(pk=value)

        if student.parent():
            column_text = f'<a href={reverse_lazy("parent_edit_view", args=[student.parent().pk])}>{student.parent().first_name} {student.parent().last_name}</a>'
        elif student.upcomming_user.email_send:
            column_text = "Pending"
        else:
            column_text = "None"

        return format_html(column_text)


class StudentParentLinkColumn(tables.Column):
    def render(self, value):
        student = Student.objects.get(pk=value)

        if student.parent():
            column_text = f'<a href={reverse_lazy("parent_edit_view", args=[student.parent().pk])}>{student.parent().first_name} {student.parent().last_name}</a>'
        elif student.upcomming_user.email_send:
            column_text = "Pending"
        else:
            column_text = "None"

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

    first_name = tables.Column(
        verbose_name=_("First name"),
        attrs={"th": {"id": "first_name_id"}},
    )

    last_name = tables.Column(
        verbose_name=_("Last name"),
        attrs={"th": {"id": "last_name_id"}},
    )

    child_email = tables.Column(
        orderable=False,
        verbose_name=_("Child email"),
    )

    class_name = tables.Column(
        verbose_name=_("Class"),
        attrs={"th": {"id": "class_name_id"}},
    )

    parent = StudentParentLinkColumn(accessor="pk", verbose_name=_("Parent"))

    info = StudentExtrainformaionColumn(
        accessor="pk",
        orderable=False,
        verbose_name="",
        attrs={"td": {"align": "right"}},
    )
    details = tables.LinkColumn(
        "student_details_view",
        args=[Accessor("pk")],
        orderable=False,
        text=format_html("<i class='fa-solid fa-pen text-secondary'></i>"),
        verbose_name="",
        attrs={"td": {"align": "right"}},
    )


class StudentChangeActionsColumn(tables.Column):
    def render(self, value):
        # formular = EventChangeFormula.objects.get(pk=value)

        return format_html(
            render_to_string(
                "administrative/tables/student_change_actions.html",
                {"pk": value},
            )
        )


class StudentNameColumn(tables.Column):
    def render(self, value):
        student_change = StudentChange.objects.get(pk=value)

        match student_change.operation:
            case 0:
                name = f"{student_change.student.first_name} {student_change.student.last_name}"
            case 1:
                name = f"{student_change.first_name} {student_change.last_name}"
            case 2:
                name = f"{student_change.student.first_name if student_change.first_name==None else student_change.first_name} {student_change.student.last_name if student_change.last_name==None else student_change.last_name}"
            case 3:
                name = f"{student_change.student.first_name} {student_change.student.last_name}"
        return name


class StudentChangeTable(tables.Table):
    class Meta:
        model = StudentChange
        # template_name = "administrative/student_list_view.html"
        fields = []

    # apply = tables.LinkColumn(
    #     "student_import_apply_change",
    #     args=[Accessor("pk")],
    #     orderable=False,
    #     text="Apply",
    #     attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    # )

    name = StudentNameColumn(accessor="pk", orderable=False)

    actions = StudentChangeActionsColumn(accessor="pk", orderable=False)


class FormularActionsColumn(tables.Column):
    def render(self, value):
        # formular = EventChangeFormula.objects.get(pk=value)

        return format_html(
            render_to_string(
                "administrative/tables/formular_actions_column.html",
                {"formular_id": value},
            )
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

    # approve = tables.LinkColumn(
    #     "administrative_event_formular_approve_view",
    #     args=[Accessor("pk")],
    #     orderable=False,
    #     text="Approve",
    #     attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    # )
    # disapprove = tables.LinkColumn(
    #     "administrative_event_formular_disapprove_view",
    #     args=[Accessor("pk")],
    #     orderable=False,
    #     text="Disapprove",
    #     attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    # )

    actions = FormularActionsColumn(accessor="pk", orderable=False)


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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_columns["students"].verbose_name = _("Students")

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "students")
        attrs = {"class": "table"}

    first_name = tables.Column(
        verbose_name=_("First name"),
        attrs={"th": {"id": "first_name_id"}},
    )

    last_name = tables.Column(
        verbose_name=_("Last name"),
        attrs={"th": {"id": "last_name_id"}},
    )

    edit = tables.LinkColumn(
        "parent_edit_view",
        args=[Accessor("pk")],
        orderable=False,
        text=format_html("<i class='fa-solid fa-pen text-secondary'></i>"),
        verbose_name="",
        attrs={"td": {"align": "right"}},
    )


class TeachersTable(tables.Table):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_columns["teacherextradata.acronym"] = tables.Column(
            orderable=False, verbose_name=_("Acronym")
        )
        # verbose_name = _("Acronym")
        # self.base_columns['teacherextradata.acronym'].orderable = False
        self.base_columns["teacherextradata.tags"].verbose_name = _("Tags")

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "teacherextradata.acronym",
            "teacherextradata.tags",
        )
        attrs = {"class": "table"}

    first_name = tables.Column(
        verbose_name=_("First name"),
        attrs={"th": {"id": "first_name_id"}},
    )

    last_name = tables.Column(
        verbose_name=_("Last name"),
        attrs={"th": {"id": "last_name_id"}},
    )

    edit = tables.LinkColumn(
        "teachers_edit_view",
        args=[Accessor("pk")],
        orderable=False,
        text=format_html("<i class='fa-solid fa-pen text-secondary'></i>"),
        verbose_name="",
        attrs={"td": {"align": "right"}},
    )


class OthersTable(tables.Table):
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name")
        attrs = {"class": "table"}

    first_name = tables.Column(
        verbose_name=_("First name"),
        attrs={"th": {"id": "first_name_id"}},
    )

    last_name = tables.Column(
        verbose_name=_("Last name"),
        attrs={"th": {"id": "last_name_id"}},
    )

    edit = tables.LinkColumn(
        "others_edit_view",
        args=[Accessor("pk")],
        orderable=False,
        text=format_html("<i class='fa-solid fa-pen text-secondary'></i>"),
        verbose_name="",
        attrs={"td": {"align": "right"}},
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


class FormularActionsColumn(tables.Column):
    def render(self, value):
        # formular = EventChangeFormula.objects.get(pk=value)

        return format_html(
            render_to_string(
                "administrative/tables/event_list_actions_column.html",
                {"event_id": value},
            )
        )


class Eventstable(tables.Table):
    class Meta:
        model = Event
        fields = ("teacher", "start", "day_group.base_event")

    # block = tables.LinkColumn(
    #     "administrative_event_block_view",
    #     args=[Accessor("pk")],
    #     orderable=False,
    #     text="Block",
    #     attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    # )
    # view = tables.LinkColumn(
    #     "administrative_event_detail_view",
    #     args=[Accessor("pk")],
    #     orderable=False,
    #     text="View",
    #     attrs={"a": {"class": "btn btn-outline-danger mt-2"}},
    # )
    actions = FormularActionsColumn(
        accessor="id", orderable=False, verbose_name="Actions"
    )
    info = EventExtraInformationColumn(accessor="pk", orderable=False)


class BackupActionsColumn(tables.Column):
    def render(self, value):
        # formular = EventChangeFormula.objects.get(pk=value)

        return format_html(
            render_to_string(
                "administrative/tables/backup_actions_column.html",
                {"pk": value},
            )
        )


class BackupTable(tables.Table):
    class Meta:
        model = Backup
        fields = (
            "backup_type",
            "backup_directories",
            "size_bytes",
            "created_at",
        )

    actions = BackupActionsColumn(
        accessor="pk", orderable=False, verbose_name="Actions"
    )
