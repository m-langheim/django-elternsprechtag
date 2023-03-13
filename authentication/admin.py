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
    list_display = ('email', 'is_active', 'role')
    list_filter = ('is_active', 'role', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password',
         'first_name', 'last_name', 'role', 'students')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'is_staff', 'role')}
         ),
    )
    search_fields = ('email', 'first_name', 'last_name',)
    ordering = ('email',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')


class UpcommingsUserAdmin(admin.ModelAdmin):
    @admin.action(description="Send registration email for selected users")
    def sendRegistrationMails(self, request, queryset):
        for up_user in queryset:
            current_site = os.environ.get("PUBLIC_URL")
            email_subject = "Anmeldelink für den Elternsprechtag"
            email_body = render_to_string(
                'authentication/emails/link.html', {'current_site': current_site, 'id': up_user.user_token, 'key': up_user.access_key, 'otp': up_user.otp})

            async_send_mail.delay(email_subject, email_body,
                                  up_user.student.child_email)
        updated = queryset
        self.message_user(
            request,
            ngettext(
                "%d story was successfully marked as published.",
                "%d stories were successfully marked as published.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    list_display = ["student", "created"]
    actions = [sendRegistrationMails]
    # model = Upcomming_User
    # urls = []


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Upcomming_User, UpcommingsUserAdmin)
admin.site.register(TeacherExtraData)

# CSV Import


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    change_list_template = "authentication/admin/students_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            # delete all groups with index class
            for group in Group.objects.filter(name__startswith="class_"):
                group.delete()

            csv_file = request.FILES["csv_file"].read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(csv_file), delimiter=';')
            for lines in reader:
                student = Student.objects.filter(
                    shield_id=lines["eindeutige Nummer (GUID)"])
                if not student.exists():
                    student = Student.objects.create(
                        shield_id=lines["eindeutige Nummer (GUID)"], first_name=lines["Vorname"], last_name=lines["Nachname"], class_name=lines["Klasse"], child_email=lines["Mailadresse"])
                else:
                    student = student.first()
                    student.child_email = lines["Mailadresse"]
                    student.first_name = lines["Vorname"]
                    student.last_name = lines["Nachname"]
                    student.class_name = lines["Klasse"]
                    student.save()
            self.message_user(request, "Your csv file has been imported")
            return redirect("..")
        form = AdminCsvImportForm()
        payload = {"form": form}
        return render(
            request, "authentication/admin/csv_form.html", payload
        )
