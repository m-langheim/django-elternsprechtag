from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext as _

from .models import Upcomming_User, Student, CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

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
admin.site.register(Student)
