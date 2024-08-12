from django.contrib import admin

from django.db.models import Q
from django.http import HttpRequest
from django.http.response import HttpResponse
from authentication.models import CustomUser
from .models import (
    Event,
    Inquiry,
    SiteSettings,
    Announcements,
    EventChangeFormula,
    TeacherEventGroup,
    MainEventGroup,
)
from .forms import AdminEventForm, AdminEventCreationFormulaForm, EventCreationForm

from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from django.urls import path
from django.views import View

from dashboard.tasks import async_create_events_special

from django.utils.html import format_html
from django.urls import reverse

from django.contrib import messages
from django.utils.translation import ngettext

from django.utils import timezone
from django.http import HttpResponseRedirect

# Register your models here.


class EventTeacherGroupAdmin(admin.TabularInline):
    model = TeacherEventGroup


class EventAdmin(admin.ModelAdmin):
    list_display = (
        "teacher",
        "start",
        "end",
        "status",
        "lead_status",
    )
    search_fields = ("teacher__first_name", "teacher__last_name", "teacher__email")
    change_list_template = "dashboard/admin/events.html"
    list_filter = ("occupied", "status", "lead_status")

    #! Hier muss noch die Möglichkeit hinzugefügt werden über das Admin Portal ein Event zu erstellen. Dies ist derzeit nur in mehreren Schritten möglich.
    # def add_view(
    #     self, request: HttpRequest, form_url: str = "", extra_context=None
    # ) -> HttpResponse:
    #     if request.method == "POST":
    #         form = EventCreationForm(request.POST)

    #         if form.is_valid():
    #             form.save()
    #             return HttpResponseRedirect(reverse("admin:dashboard_event_changelist"))
    #     else:
    #         form = EventCreationForm()

    #     return self.render_change_form(
    #         request,
    #         context={
    #             "form": form,
    #             "is_popup": True,
    #             "add": True,
    #             "change": False,
    #         },
    #         add=True,
    #     )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("main_event_group", "teacher_event_group"),
                    (
                        "start",
                        "end",
                    ),
                    "teacher",
                    "status",
                    "occupied",
                ),
            },
        ),
        (
            "Occupation",
            {
                "fields": (
                    "parent",
                    "student",
                )
            },
        ),
        (
            "Booking",
            {
                "fields": (
                    "lead_status",
                    "lead_status_last_change",
                    "lead_manual_override",
                ),
                "classes": ["collapse"],
            },
        ),
    )

    # def get_urls(self):
    #     urls = super().get_urls()
    #     my_urls = [
    #         path("add-events/", self.add_events.as_view()),
    #     ]
    #     return my_urls + urls

    # class add_events(View):
    #     def get(self, request):
    #         return render(
    #             request,
    #             "dashboard/admin/addEvents.html",
    #             context={"form": AdminEventForm},
    #         )

    #     def post(self, request):
    #         form = AdminEventForm(request.POST)
    #         if form.is_valid():
    #             async_create_events_special.delay(
    #                 [teacher.id for teacher in form.cleaned_data["teacher"]],
    #                 form.cleaned_data["date"].strftime("%Y-%m-%d"),
    #                 form.cleaned_data["start_time"].strftime("%H:%M:%S"),
    #                 form.cleaned_data["end_time"].strftime("%H:%M:%S"),
    #             )

    #             return redirect("..")
    #         return render(
    #             request, "dashboard/admin/addEvents.html", context={"form": form}
    #         )


class InquiryAdmin(admin.ModelAdmin):
    list_display = ("requester", "respondent", "type", "processed")


class EventChangeFormulaAdmin(admin.ModelAdmin):
    list_filter = ("status",)
    list_display = (
        "teacher",
        "date",
        "start_time",
        "end_time",
        "no_events",
        "status",
        "response_actions",
    )
    search_fields = ("teacher",)
    change_list_template = "dashboard/admin/eventCreationForm.html"
    readonly_fields = ("response_actions",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<formula_id>/approve/",
                self.admin_site.admin_view(self.process_approval),
                name="event_change_formula_approve",
            ),
            path(
                "<formula_id>/disapprove/",
                self.admin_site.admin_view(self.process_disapproval),
                name="event_change_formula_disapprove",
            ),
            path(
                "add_form",
                self.admin_site.admin_view(self.create_event_change_formula.as_view()),
                name="create_event_change_formula",
            ),
        ]
        return custom_urls + urls

    class create_event_change_formula(View):
        def get(self, request, *args, **kwargs):
            return render(
                request,
                "dashboard/admin/addEvents.html",
                context={"form": AdminEventCreationFormulaForm},
            )

        def post(self, request):
            form = AdminEventCreationFormulaForm(request.POST)
            if form.is_valid():
                messages.info(
                    request,
                    "Es werden für {} Formulare erstellt.".format(
                        "\n,".join(
                            [
                                teacher.email
                                for teacher in form.cleaned_data.get("teacher")
                            ]
                        )
                    ),
                )
                successfull = 0
                for teacher in form.cleaned_data.get("teacher"):
                    if not EventChangeFormula.objects.filter(
                        Q(teacher=teacher),
                        Q(date=form.cleaned_data.get("date")),
                    ).exists():
                        successfull += 1
                        EventChangeFormula.objects.create(
                            teacher=teacher, date=form.cleaned_data.get("date")
                        )
                    else:
                        messages.info(
                            request,
                            "Für den Lehrer {} existierte bereits eine Anfrage für diesen Tag.".format(
                                request.user
                            ),
                        )
                messages.success(
                    request,
                    "Es wurden {} Anträge erfolgreich erstellt.".format(successfull),
                )

                return redirect("admin:dashboard_eventchangeformula_changelist")
            return render(
                request, "dashboard/admin/addEvents.html", context={"form": form}
            )

    def process_approval(self, request, formula_id):
        formula = self.get_object(request, formula_id)

        if formula.status != 1:
            messages.warning(
                request,
                "Sie können diesen Antrag nicht ablehnen, da er sich hierzu im falschen Status befindet.",
            )
            return redirect("admin:dashboard_eventchangeformula_changelist")

        if not formula.no_events:
            async_create_events_special.delay(
                [formula.teacher.id],
                formula.date.strftime("%Y-%m-%d"),
                formula.start_time.strftime("%H:%M:%S"),
                formula.end_time.strftime("%H:%M:%S"),
            )

        formula.status = 2
        formula.save()

        messages.success(request, "Die Termine werden nun erstellt.")

        return redirect("admin:dashboard_eventchangeformula_changelist")

    def process_disapproval(self, request, formula_id):
        formula = self.get_object(request, formula_id)

        if formula.status != 1:
            messages.warning(
                request,
                "Sie können diesen Antrag nicht ablehnen, da er sich hierzu im falschen Status befindet.",
            )
            return redirect("admin:dashboard_eventchangeformula_changelist")

        formula.status = 3
        formula.save()
        return redirect("admin:dashboard_eventchangeformula_changelist")

    @admin.display(description=_("Response actions"))
    def response_actions(self, obj):
        if obj.status == 1:
            return format_html(
                '<a class="button" href="{}">{}</a>&nbsp;'
                '<a class="button" href="{}">{}</a>',
                reverse("admin:event_change_formula_approve", args=[obj.pk]),
                _("Approve"),
                reverse("admin:event_change_formula_disapprove", args=[obj.pk]),
                _("Disapprove"),
            )
        else:
            return format_html("<p>{}</p>", _("No actions available"))

    @admin.action(description="Approve the event change formulas")
    def approveEventChangForm(self, request, queryset):
        successfull_approvals = 0
        unsuccessfull_approvals = 0
        for form in queryset:
            if form.status == 1:
                if not form.no_events:
                    async_create_events_special.delay(
                        [form.teacher.id],
                        form.date.strftime("%Y-%m-%d"),
                        form.start_time.strftime("%H:%M:%S"),
                        form.end_time.strftime("%H:%M:%S"),
                    )
                form.status = 2
                form.save()
                successfull_approvals += 1
            else:
                unsuccessfull_approvals += 1

        if successfull_approvals > 0:
            self.message_user(
                request,
                ngettext(
                    "%d form was successfully approved and events changed.",
                    "%d forms were successfully approved and changed.",
                    successfull_approvals,
                )
                % successfull_approvals,
                messages.SUCCESS,
            )
        if unsuccessfull_approvals > 0:
            self.message_user(
                request,
                ngettext(
                    "%d form was not successfully approved. Please try them individually.",
                    "%d forms were not successfully approved. Please try them individually.",
                    unsuccessfull_approvals,
                )
                % unsuccessfull_approvals,
                messages.WARNING,
            )

    @admin.action(description="Disapprove the event change formulas")
    def disapproveEventChangForm(self, request, queryset):
        successfull_approvals = 0
        unsuccessfull_approvals = 0
        for form in queryset:
            if form.status == 1:
                form.status = 3
                form.save()
                successfull_approvals += 1
            else:
                unsuccessfull_approvals += 1

        if successfull_approvals > 0:
            self.message_user(
                request,
                ngettext(
                    "%d form was successfully disapproved.",
                    "%d forms were successfully disapproved.",
                    successfull_approvals,
                )
                % successfull_approvals,
                messages.SUCCESS,
            )
        if unsuccessfull_approvals > 0:
            self.message_user(
                request,
                ngettext(
                    "%d form was not successfully disapproved. Please try them individually.",
                    "%d forms were not successfully disapproved. Please try them individually.",
                    unsuccessfull_approvals,
                )
                % unsuccessfull_approvals,
                messages.WARNING,
            )

    actions = [approveEventChangForm, disapproveEventChangForm]


admin.site.register(Event, EventAdmin)
admin.site.register(Inquiry, InquiryAdmin)
admin.site.register(SiteSettings)
admin.site.register(Announcements)
admin.site.register(EventChangeFormula, EventChangeFormulaAdmin)
admin.site.register(TeacherEventGroup)
admin.site.register(MainEventGroup)
