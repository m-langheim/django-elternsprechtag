from asyncio import events
import datetime
from os import times_result
from tracemalloc import start
from django.contrib import admin

from authentication.models import CustomUser
from .models import Event, TeacherStudentInquiry, SiteSettings

from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from django.urls import path

from dashboard.tasks import async_create_events
# Register your models here.


class EventAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'start', 'end', 'occupied')
    change_list_template = "dashboard/admin/events.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('add-events/', self.add_events),
        ]
        return my_urls + urls

    def add_events(self, request):
        async_create_events.delay()
        return redirect("..")


admin.site.register(Event, EventAdmin)
admin.site.register(TeacherStudentInquiry)
admin.site.register(SiteSettings)
