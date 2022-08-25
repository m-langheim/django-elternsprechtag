import io
import csv
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from django.urls import path

from .models import Upcomming_User, Student, CustomUser, TeacherExtraData
from .forms import CustomUserCreationForm, CustomUserChangeForm, AdminCsvImportForm

# Register your models here.


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('email', 'is_active', 'role')
    list_filter = ('email', 'is_active', 'role')
    fieldsets = (
        (None, {'fields': ('email', 'password',
         'first_name', 'last_name', 'role', 'students')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'role')}
         ),
    )
    search_fields = ('email', 'first_name', 'last_name',)
    ordering = ('email',)


admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(Upcomming_User)
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
            csv_file = request.FILES["csv_file"].read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(csv_file), delimiter=';')
            for lines in reader:
                try:
                    student = Student.objects.get(
                        shield_id=lines["eindeutige Nummer (GUID)"])
                except Student.DoesNotExist:
                    student = Student.objects.create(
                        shield_id=lines["eindeutige Nummer (GUID)"], first_name=lines["Vorname"], last_name=lines["Nachname"], class_name=lines["Klasse"], child_email=lines["Mailadresse"])
                else:
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
