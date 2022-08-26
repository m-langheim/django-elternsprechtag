import datetime
from os import times_result
from tracemalloc import start
from django.contrib import admin

from authentication.models import CustomUser
from .models import Event, TeacherStudentInquiry, SiteSettings

from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from django.urls import path
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
        teachers = CustomUser.objects.filter(role=1)

        time_start = SiteSettings.objects.all().first().time_start
        time_end = SiteSettings.objects.all().first().time_end
        duration = SiteSettings.objects.all().first().event_duration
        for teacher in teachers:
            start = datetime.datetime.combine(
                datetime.date.today(), time_start)
            while start + duration <= datetime.datetime.combine(datetime.date.today(), time_end):
                try:
                    Event.objects.get(teacher=teacher, start=start)
                except Event.DoesNotExist:
                    Event.objects.create(
                        teacher=teacher, start=start, end=start+duration)
                start = start + duration
        return redirect("..")


admin.site.register(Event, EventAdmin)
admin.site.register(TeacherStudentInquiry)
admin.site.register(SiteSettings)
