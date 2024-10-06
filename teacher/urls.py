from unicodedata import name
from django.urls import path
from .views import *

urlpatterns = [
    path("", dashboard, name="teacher_dashboard"),
    path("students/", studentList, name="teacher_students_list"),
    path(
        "redirect/eventinquiry/<studentID>",
        teacher_redirect_eventinquiry,
        name="teacher_redirect_eventinquiry",
    ),
    path(
        "inquiry/create/<studentID>",
        CreateInquiryView.as_view(),
        name="teacher_create_inquiry_id",
    ),
    path("inquiry/<id>", InquiryView.as_view(), name="teacher_show_inquiry"),
    path(
        "inquiry/<inquiryID>/delete",
        DeleteInquiryView.as_view(),
        name="teaher_delete_inquiry",
    ),
    path(
        "event/<event_id>/cancel/",
        EventCancellationView.as_view(),
        name="teacher_cancel_event_view",
    ),
    path("event/<event>/confirm", confirm_event, name="teacher_confirm_event"),
    path("event/<event_id>", EventDetailView.as_view(), name="teacher_event_view"),
    path(
        "announcement/<announcement_id>/mark_read",
        markAnnouncementRead,
        name="teacher_mark_announcement_read",
    ),
    path("export/", create_event_PDF, name="create_events_pdf"),
    path("events/", viewMyEvents, name="teacher_personal_events"),
    path(
        "events/formulars/<form_id>/edit/",
        EditMyEventsDetail.as_view(),
        name="teacher_personal_events_edit",
    ),
    path(
        "events/break_formulars/<group_pk>/create/",
        EventBreakRequestView.as_view(),
        name="teacher_personal_day_group_add_break_request",
    ),
    path(
        "events/break_formulars/event/<event_pk>/create/",
        EventBreakForEventRequestView.as_view(),
        name="teacher_personal_event_add_break_request",
    ),
    path(
        "event/<event_pk>/reset_lead_status/",
        EventResetLeadStatusToOriginalView.as_view(),
        name="teacher_personal_reset_event_lead_status",
    ),
]
