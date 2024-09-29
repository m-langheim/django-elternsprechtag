from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.utils.translation import gettext as _
from .models import *
from dashboard.models import SiteSettings
from authentication.models import Student, CustomUser, StudentChange
from dashboard.models import (
    EventChangeFormula,
    Event,
    DayEventGroup,
    TeacherEventGroup,
    BaseEventGroup,
)
from authentication.models import (
    CustomUser,
    Student,
    TeacherExtraData,
    Tag,
    generate_new_color,
    Upcomming_User,
)
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import Permission

from crispy_forms.helper import FormHelper

from django.contrib.auth.password_validation import validate_password
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from .forms_helpers import get_students_choices_for_event
from .tasks import *

from django_select2 import forms as s2forms
from django_select2.views import AutoResponseView

from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)

from colorfield.widgets import ColorWidget


class StudentSelect2View(LoginRequiredMixin, PermissionRequiredMixin, AutoResponseView):
    permission_required = "student.can_view_all"


class StudentSelect2WidgetMixin(object):
    def __init__(self, *args, **kwargs):
        kwargs["data_view"] = "student-select2-view"
        super(StudentSelect2WidgetMixin, self).__init__(*args, **kwargs)


class StudentWidget(s2forms.ModelSelect2Widget):
    model = Student
    search_fields = [
        "first_name__icontains",
        "last_name__icontains",
        "child_email__icontains",
    ]


class PermissionWidget(s2forms.ModelSelect2MultipleWidget):
    model = Permission
    search_fields = [
        "codename__icontains",
        "name__icontains",
    ]


class MultiStudentWidget(StudentSelect2WidgetMixin, s2forms.ModelSelect2MultipleWidget):
    model = Student
    search_fields = [
        "first_name__icontains",
        "last_name__icontains",
        "child_email__icontains",
    ]


class StudentDirectSelectForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        widget=StudentWidget(
            attrs={
                "onchange": "this.form.submit()",
                "data-placeholder": "Search for a student",
            }
        ),
        label="",
    )


class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label=_("CSV-File"))


class TeacherImportForm(forms.Form):
    csv_file = forms.FileField(required=False, label=_("CSV-File"))
    teacher_email = forms.EmailField(required=False, label=_("Teacher-Email"))


class AdminStudentEditForm(forms.Form):
    first_name = forms.CharField(label=_("First name"), max_length=48)
    last_name = forms.CharField(label=_("Last name"), max_length=48)
    child_email = forms.EmailField(label=_("Child emails"), max_length=200)
    class_name = forms.CharField(label=_("Name of class"), max_length=4)


class EventChangeFormularForm(forms.Form):
    teacher = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role=1),
        widget=forms.CheckboxSelectMultiple,
        label="",
        required=True,
    )


class EventAddNewDateForm(forms.Form):
    base_event = forms.ModelChoiceField(
        queryset=BaseEventGroup.objects.filter(valid_until__gte=timezone.now().date()),
        empty_label=_("New base event"),
        required=False,
    )
    date = forms.DateField()
    teacher = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role=1),
        widget=forms.CheckboxSelectMultiple(),
        label="",
    )
    lead_start = forms.DateField(
        required=False,
        help_text="This setting is only required if you create a new base event.",
    )
    lead_inquiry_start = forms.DateField(
        required=False,
        help_text="This setting is only required if you create a new base event.",
    )

    def clean_date(self):
        date = self.cleaned_data["date"]

        if not date >= timezone.now().date():
            self.add_error(
                "date", _("The date of the event should be set in the future.")
            )

        return date

    def clean_lead_start(self):
        lead_start = self.cleaned_data["lead_start"]
        date = self.cleaned_data["date"]
        base_event = self.cleaned_data.get("base_event", None)

        if not base_event and not lead_start:
            self.add_error(
                "lead_inquiry_start",
                _("This field must be set if you want to create a new base event."),
            )
        elif not base_event:
            if lead_start >= date:
                self.add_error("lead_start", _("The lead must start before the event."))

        return lead_start

    def clean_lead_inquiry_start(self):
        lead_start = self.cleaned_data["lead_start"]
        lead_inquiry_start = self.cleaned_data["lead_inquiry_start"]
        base_event = self.cleaned_data.get("base_event", None)
        date = self.cleaned_data["date"]

        if not base_event and not lead_inquiry_start:
            self.add_error(
                "lead_inquiry_start",
                _("This field must be set if you want to create a new base event."),
            )
        elif not base_event:
            if lead_inquiry_start >= date:
                self.add_error(
                    "lead_inquiry_start", _("The lead must start before the event.")
                )

            if lead_inquiry_start > lead_start:
                self.add_error(
                    "lead_inquiry_start",
                    _("The lead inquiry must start before the main lead."),
                )
        return lead_inquiry_start


class EventChangeFormulaEditForm(forms.ModelForm):
    class Meta:
        model = EventChangeFormula
        fields = (
            "start_time",
            "end_time",
            "no_events",
        )

    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"class": "timepicker"}),
        label=_("Start"),
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"class": "timepicker"}),
        label=_("End"),
    )

    def save(self, commit=True):
        self.instance.status = 1
        if not self.cleaned_data.get("no_events"):
            self.instance.start_time = self.cleaned_data.get("start_time")
            self.instance.end_time = self.cleaned_data.get("end_time")
        else:
            self.instance.no_events = True
        self.instance.save()
        return super(EventChangeFormulaEditForm, self).save(commit=commit)


class ParentEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "students",
            "email",
            "is_active",
            "user_permissions",
        )

    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.all(), widget=MultiStudentWidget
    )
    custom_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="",
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(), required=False, widget=PermissionWidget
    )

    def __init__(self, *args, **kwargs):
        super(ParentEditForm, self).__init__(*args, **kwargs)

        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["is_active"].label = _("User is active")
        self.fields["user_permissions"].label = _("Specific permissions")
        self.fields["user_permissions"].help_text = ""

        user: CustomUser = self.instance

        PARENT_PERMISSIONS = [
            "condition_prebook_event",
            "book_event",
            "book_double_event",
        ]

        self.parent_permissions = Permission.objects.filter(
            codename__in=PARENT_PERMISSIONS
        )
        user_permissions = user.user_permissions.all()

        self.permission_choices = [
            [permission.pk, permission.name] for permission in self.parent_permissions
        ]

        self.fields["custom_permissions"].choices = self.permission_choices
        self.initial["custom_permissions"] = user_permissions

    def save(self, commit=True):
        instance: CustomUser = self.instance
        custom_permissions = self.cleaned_data["custom_permissions"]
        all_permissions = self.parent_permissions
        initial_permissions = self.initial["custom_permissions"]
        user_permissions = self.cleaned_data["user_permissions"]
        students = self.cleaned_data["students"]

        instance.students.set(students)

        instance.user_permissions.set(user_permissions)

        for permission in all_permissions:
            if permission in custom_permissions:
                instance.user_permissions.add(permission)
            elif permission in initial_permissions:
                instance.user_permissions.remove(permission)

        if commit:
            instance.save()

        return instance


class TagsWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "name__icontains",
        "synonyms__icontains",
    ]


class TeacherEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = (
            "email",
            "first_name",
            "last_name",
            "user_permissions",
            "is_active",
            "is_staff",
        )

    email = forms.EmailField(label=_("Email"))
    first_name = forms.CharField(max_length=48)
    last_name = forms.CharField(max_length=48)
    acronym = forms.CharField(max_length=3, label=_("Acronym"))
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(), required=False, widget=TagsWidget
    )
    image = forms.ImageField(required=False, label=_("Profile image"))

    custom_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="",
    )

    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(), required=False, widget=PermissionWidget
    )

    def __init__(self, *args, **kwargs):
        super(TeacherEditForm, self).__init__(*args, **kwargs)

        self.fields["is_active"].label = _("User is active")
        self.fields["is_staff"].label = _("User is staff")
        self.fields["user_permissions"].label = _("Specific permissions")
        self.fields["user_permissions"].help_text = ""

        user: CustomUser = self.instance

        OTHERS_PERMISSIONS = [
            "apply_changes",
            "approve_disapprove",
            "can_restore_backup",
            "can_add_backup",
        ]

        self.others_permissions = Permission.objects.filter(
            codename__in=OTHERS_PERMISSIONS
        )
        user_permissions = user.user_permissions.all()

        self.permission_choices = [
            [permission.pk, permission.name] for permission in self.others_permissions
        ]

        self.fields["custom_permissions"].choices = self.permission_choices
        self.initial["custom_permissions"] = user_permissions

        self.teacher_extra_data: TeacherExtraData = self.instance.teacherextradata

        self.initial["acronym"] = self.teacher_extra_data.acronym
        self.initial["tags"] = self.teacher_extra_data.tags.all()
        self.initial["image"] = self.teacher_extra_data.image

    def clean_acronym(self):
        instance = self.instance

        data = self.cleaned_data["acronym"]

        if (
            TeacherExtraData.objects.filter(acronym=data)
            .exclude(pk=instance.teacherextradata.pk)
            .exists()
        ):
            raise ValueError(
                _(
                    "Another teacher has the same acronym. Please choose a different one."
                )
            )
        return data

    def save(self, commit=True):
        instance: CustomUser = self.instance
        custom_permissions = self.cleaned_data["custom_permissions"]
        all_permissions = self.others_permissions
        initial_permissions = self.initial["custom_permissions"]
        user_permissions = self.cleaned_data["user_permissions"]

        instance.user_permissions.set(user_permissions)

        for permission in all_permissions:
            if permission in custom_permissions:
                instance.user_permissions.add(permission)
            elif permission in initial_permissions:
                instance.user_permissions.remove(permission)

        self.teacher_extra_data.acronym = self.cleaned_data["acronym"]
        self.teacher_extra_data.save()

        self.teacher_extra_data.tags.set(self.cleaned_data["tags"])

        if commit:
            instance.save()

        return instance


class OthersEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = (
            "email",
            "first_name",
            "last_name",
            "user_permissions",
            "is_active",
            "is_staff",
        )

    email = forms.EmailField(label=_("Email"))
    first_name = forms.CharField(max_length=48, label=_("First name"))
    last_name = forms.CharField(max_length=48, label=_("Last name"))

    custom_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="",
    )

    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(), required=False, widget=PermissionWidget
    )

    def __init__(self, *args, **kwargs):
        super(OthersEditForm, self).__init__(*args, **kwargs)

        self.fields["is_active"].label = _("User is active")
        self.fields["is_staff"].label = _("User is staff")
        self.fields["user_permissions"].label = _("Specific permissions")
        self.fields["user_permissions"].help_text = ""

        user: CustomUser = self.instance

        OTHERS_PERMISSIONS = [
            "apply_changes",
            "approve_disapprove",
            "can_restore_backup",
            "can_add_backup",
        ]

        self.others_permissions = Permission.objects.filter(
            codename__in=OTHERS_PERMISSIONS
        )
        user_permissions = user.user_permissions.all()

        self.permission_choices = [
            [permission.pk, permission.name] for permission in self.others_permissions
        ]

        self.fields["custom_permissions"].choices = self.permission_choices
        self.initial["custom_permissions"] = user_permissions

    def save(self, commit=True):
        instance: CustomUser = self.instance
        custom_permissions = self.cleaned_data["custom_permissions"]
        all_permissions = self.others_permissions
        initial_permissions = self.initial["custom_permissions"]
        user_permissions = self.cleaned_data["user_permissions"]

        instance.user_permissions.set(user_permissions)

        for permission in all_permissions:
            if permission in custom_permissions:
                instance.user_permissions.add(permission)
            elif permission in initial_permissions:
                instance.user_permissions.remove(permission)

        if commit:
            instance.save()

        return instance


class SettingsEditForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        exclude = ("",)


class EventEditForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "lead_status",
            "lead_manual_override",
            "disable_automatic_changes",
        ]

    def save(self, commit=True):
        instance: Event = self.instance

        if "lead_status" in self.changed_data:
            instance.lead_manual_override = True

        if commit:
            instance.save()

        return instance


class EventAddStudentForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = []

    add_student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        required=False,
        widget=StudentWidget(
            attrs={
                "data-dropdown-parent": "#addStudentModal",
                "data-placeholder": "Select an option",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super(EventAddStudentForm, self).__init__(*args, **kwargs)

        if self.instance.parent:
            choices = get_students_choices_for_event(event=self.instance)

            if choices.__len__() == 0:
                self.fields["add_student"].widget = self.fields[
                    "add_student"
                ].hidden_widget()

            self.fields["add_student"].choices = choices

    def clean_add_student(self):
        instance = self.instance

        data = self.cleaned_data["add_student"]

        if instance.parent and data and not data in instance.parent.students.all():
            raise ValidationError(
                "The specified student does not belong to the same parent as an already specified student. Please only choose students linked to the same parent account."
            )

        return data

    def save(self, commit=True):
        instance: Event = self.instance

        if "add_student" in self.changed_data:
            add_student = self.cleaned_data["add_student"]

            instance.student.add(add_student)
            if CustomUser.objects.filter(Q(role=0), Q(students=add_student)).exists():
                instance.parent = CustomUser.objects.get(
                    Q(role=0), Q(students=add_student)
                )

            instance.occupied = True
            instance.status = 1

        if commit:
            instance.save()

        return instance


class ControlParentCreationForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.all(), disabled=True)
    email = forms.EmailField(required=True, label="")
    first_name = forms.CharField(max_length=48, label="")
    last_name = forms.CharField(max_length=48, label="")

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Password"),
                "autocomplete": "off",
            }
        ),
        # validators=[validate_password],
        label="",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Confirm password"),
                "autocomplete": "off",
            }
        ),
        label="",
    )

    def clean_email(self):
        email = self.cleaned_data["email"]

        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(
                _("This email is already taken. Please provide a different one.")
            )

        return email

    # def clean(self):
    #     password = self.cleaned_data["password"]
    #     confirm_password = self.cleaned_data["confirm_password"]

    #     validate_password(password, user=None, password_validators=None)

    #     if password != confirm_password:
    # self.add_error(
    #     "password", _("The password and the confirm password must be equal.")
    # )
    # self.add_error(
    #     "confirm_password",
    #     _("The password and the confirm password must be equal."),
    # )
    # raise ValidationError(":..")

    def clean_confirm_password(self):
        password = self.cleaned_data["password"]
        confirm_password = self.cleaned_data["confirm_password"]

        if password != confirm_password:
            raise forms.ValidationError(
                "The passwords do not match", code="passwords_wrong"
            )
        validate_password(password, user=None, password_validators=None)


class ControlParentAddStudent(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(), disabled=True, label=""
    )
    parent = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(Q(role=0)), label=""
    )


class EditStudentChangesForm(forms.ModelForm):
    class Meta:
        model = StudentChange
        exclude = ("applied", "approved", "applied_time")

    shield_id = forms.CharField(required=False)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    child_email = forms.EmailField(required=False)
    created = forms.DateTimeField(disabled=True)
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(), disabled=True, required=False
    )

    apply = forms.BooleanField(required=False)

    def save(self, commit=True):
        instance = self.instance
        apply = self.cleaned_data["apply"]

        if commit:
            instance.save()

        if apply:
            apply_and_approve_student_changes.delay([instance.pk])
        return instance


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name", "synonyms", "color"]
        # widgets = {"color": ColorWidget}


class BaseEventEditLeadStatusForm(forms.ModelForm):
    class Meta:
        model = BaseEventGroup
        fields = ["lead_status", "disable_automatic_changes", "force", "manual_apply"]

    manual_apply = forms.BooleanField(
        initial=True, widget=forms.HiddenInput, required=False
    )

    def clean_manual_apply(self):
        return True


class BaseEventEditLeadDateForm(forms.ModelForm):
    class Meta:
        model = BaseEventGroup
        fields = ["lead_start", "lead_inquiry_start", "force", "manual_apply"]

    manual_apply = forms.BooleanField(
        initial=True, widget=forms.HiddenInput, required=False
    )

    def clean_manual_apply(self):
        return True

    def clean_lead_start(self):
        lead_start = self.cleaned_data["lead_start"]

        if (
            lead_start
            > self.instance.dayeventgroup_set.all().order_by("date").first().date
        ):
            self.add_error(
                "lead_start",
                _("The lead must start before the event."),
            )
        return lead_start

    def clean_lead_inquiry_start(self):
        lead_start = self.cleaned_data["lead_start"]
        lead_inquiry_start = self.cleaned_data["lead_inquiry_start"]

        if lead_inquiry_start > lead_start:
            self.add_error(
                "lead_inquiry_start",
                _("The lead inquiry must start before the main lead."),
            )
        return lead_inquiry_start


class TeacherDayGroupEditLeadStatusForm(forms.ModelForm):
    class Meta:
        model = TeacherEventGroup
        fields = ["lead_status", "disable_automatic_changes", "force", "manual_apply"]

    manual_apply = forms.BooleanField(
        initial=True, widget=forms.HiddenInput, required=False
    )

    def clean_manual_apply(self):
        return True


class TeacherDayGroupEditLeadDateForm(forms.ModelForm):
    class Meta:
        model = TeacherEventGroup
        fields = ["lead_start", "lead_inquiry_start", "force", "manual_apply"]

    manual_apply = forms.BooleanField(
        initial=True, widget=forms.HiddenInput, required=False
    )

    def clean_manual_apply(self):
        return True

    def clean_lead_start(self):
        lead_start = self.cleaned_data["lead_start"]

        if lead_start > self.instance.day_group.date:
            self.add_error(
                "lead_start",
                _("The lead must start before the event."),
            )
        return lead_start

    def clean_lead_inquiry_start(self):
        lead_start = self.cleaned_data["lead_start"]
        lead_inquiry_start = self.cleaned_data["lead_inquiry_start"]

        if lead_inquiry_start > lead_start:
            self.add_error(
                "lead_inquiry_start",
                _("The lead inquiry must start before the main lead."),
            )
        return lead_inquiry_start


class UpcommingUserBatchSendForm(forms.Form):
    exclude_students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.filter(
            pk__in=list(Upcomming_User.objects.all().values_list("student", flat=True))
        ),
        widget=MultiStudentWidget(
            queryset=Student.objects.filter(
                pk__in=list(
                    Upcomming_User.objects.all().values_list("student", flat=True)
                )
            )
        ),
        required=False,
    )

    resend = forms.BooleanField(initial=False, required=False)
