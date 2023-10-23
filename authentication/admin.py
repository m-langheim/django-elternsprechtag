import io
import csv
import os
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib.auth.models import Group
from django.template.loader import render_to_string

from .tasks import async_send_mail
from .models import Upcomming_User, Student, CustomUser, TeacherExtraData, Tag
from .forms import CustomUserCreationForm, CustomUserChangeForm, AdminCsvImportForm

from django.contrib import messages
from django.utils.translation import ngettext

# Register your models here.


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ("email", "is_active", "role")
    list_filter = ("is_active", "role", "is_staff")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                    "first_name",
                    "last_name",
                    "role",
                    "students",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_staff",
                    "is_admin",
                    "is_active",
                    "groups",
                    "user_permissions",
                ),
                "classes": ["collapse"],
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "is_staff",
                    "role",
                ),
            },
        ),
    )
    search_fields = (
        "email",
        "first_name",
        "last_name",
    )
    ordering = ("email",)


class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
    ordering = ("name",)
    search_fields = ("name", "synonyms")


class UpcommingsUserAdmin(admin.ModelAdmin):
    @admin.action(description="Send registration email for selected users")
    def sendRegistrationMails(self, request, queryset):
        successfull_updates = 0
        for up_user in queryset:
            current_site = os.environ.get("PUBLIC_URL")
            email_subject = "Anmeldelink für den Elternsprechtag"
            email_str_body = render_to_string(
                "authentication/email/link.html",
                {
                    "current_site": current_site,
                    "id": up_user.user_token,
                    "key": up_user.access_key,
                    "otp": up_user.otp,
                },
            )
            email_html_body = render_to_string(
                "authentication/email/link_html.html",
                {
                    "current_site": current_site,
                    "id": up_user.user_token,
                    "key": up_user.access_key,
                    "otp": up_user.otp,
                },
            )

            async_send_mail.delay(
                email_subject,
                email_str_body,
                up_user.student.child_email,
                email_html_body=email_html_body,
            )
            up_user.email_send = True
            up_user.save()
            successfull_updates += 1
        self.message_user(
            request,
            ngettext(
                "%d registration email was successfully initiated.",
                "%d registration emails were successfully initiated.",
                successfull_updates,
            )
            % successfull_updates,
            messages.SUCCESS,
        )

    @admin.action(description="Recreate registration link and send email")
    def recreateUpcommingUser(self, request, queryset):
        successfull_updates = 0
        for up_user in queryset:
            student = up_user.student
            up_user.delete()
            new_up_user = Upcomming_User.objects.create(student=student)

            current_site = os.environ.get("PUBLIC_URL")
            email_subject = "Anmeldelink für den Elternsprechtag"
            email_str_body = render_to_string(
                "authentication/email/link.html",
                {
                    "current_site": current_site,
                    "id": new_up_user.user_token,
                    "key": new_up_user.access_key,
                    "otp": new_up_user.otp,
                },
            )
            email_html_body = render_to_string(
                "authentication/email/link_html.html",
                {
                    "current_site": current_site,
                    "id": new_up_user.user_token,
                    "key": new_up_user.access_key,
                    "otp": new_up_user.otp,
                },
            )

            async_send_mail.delay(
                email_subject,
                email_str_body,
                new_up_user.student.child_email,
                email_html_body=email_html_body,
            )
            new_up_user.email_send = True
            new_up_user.save()
            successfull_updates += 1
        self.message_user(
            request,
            ngettext(
                "%d regestration link was successfully recreated and send.",
                "%d registration links were successfully recreates and send.",
                successfull_updates,
            )
            % successfull_updates,
            messages.SUCCESS,
        )

    list_display = ["student", "email_send"]
    list_filter = ["email_send"]
    search_fields = ["student"]
    actions = [sendRegistrationMails, recreateUpcommingUser]
    fieldsets = (
        (None, {"fields": ("student", "email_send", "created")}),
        (
            _("Access details"),
            {
                "fields": (
                    "user_token",
                    "access_key",
                    "otp",
                    "otp_verified",
                    "otp_verified_date",
                )
            },
        ),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Upcomming_User, UpcommingsUserAdmin)
admin.site.register(TeacherExtraData)

# CSV Import


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    change_list_template = "authentication/admin/students_changelist.html"

    list_display = ("last_name", "first_name", "registered")

    search_fields = ["first_name", "last_name"]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("import-csv/", self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            # delete all groups with index class
            for group in Group.objects.filter(name__startswith="class_"):
                group.delete()

            csv_file = request.FILES["csv_file"].read().decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(csv_file), delimiter=";")

            created_students = 0
            for lines in reader:
                student = Student.objects.filter(
                    shield_id=lines["eindeutige Nummer (GUID)"]
                )
                if not student.exists():
                    student = Student.objects.create(
                        shield_id=lines["eindeutige Nummer (GUID)"],
                        first_name=lines["Vorname"],
                        last_name=lines["Nachname"],
                        class_name=lines["Klasse"],
                        child_email=lines["Mailadresse"],
                    )
                else:
                    student = student.first()
                    student.child_email = lines["Mailadresse"]
                    student.first_name = lines["Vorname"]
                    student.last_name = lines["Nachname"]
                    student.class_name = lines["Klasse"]
                    student.save()
                    created_students += 1
            self.message_user(
                request,
                ngettext(
                    "%d student was newely created.",
                    "%d students were newely created.",
                    created_students,
                )
                % created_students,
                messages.SUCCESS,
            )
            return redirect("..")
        form = AdminCsvImportForm()
        payload = {"form": form}
        return render(request, "authentication/admin/csv_form.html", payload)
