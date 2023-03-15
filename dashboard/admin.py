from django.contrib import admin

from authentication.models import CustomUser
from .models import Event, Inquiry, SiteSettings, Announcements
from .forms import AdminEventForm

from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from django.urls import path
from django.views import View

from dashboard.tasks import async_create_events_special
# Register your models here.


class EventAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'start', 'end', 'occupied')
    change_list_template = "dashboard/admin/events.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('add-events/', self.add_events.as_view()),
        ]
        return my_urls + urls

    class add_events(View):
        def get(self, request):
            return render(request, "dashboard/admin/addEvents.html", context={'form': AdminEventForm})
            # async_create_events.delay()
            # return redirect("..")

        def post(self, request):
            form = AdminEventForm(request.POST)
            if form.is_valid():
                print(type(form.cleaned_data["start_time"]))

                async_create_events_special.delay([teacher.id for teacher in form.cleaned_data["teacher"]],
                                                  form.cleaned_data["date"].strftime("%Y-%m-%d"), form.cleaned_data["start_time"].strftime("%H:%M:%S"), form.cleaned_data["end_time"].strftime("%H:%M:%S"))
                # async_create_events_special([teacher.id for teacher in form.cleaned_data["teacher"]],
                #                             form.cleaned_data["date"], form.cleaned_data["start_time"], form.cleaned_data["end_time"])
                return redirect("..")
            return render(request, "dashboard/admin/addEvents.html", context={'form': form})


class InquiryAdmin(admin.ModelAdmin):
    list_display = ('requester', 'respondent', 'type', 'processed')


admin.site.register(Event, EventAdmin)
admin.site.register(Inquiry, InquiryAdmin)
admin.site.register(SiteSettings)
admin.site.register(Announcements)
