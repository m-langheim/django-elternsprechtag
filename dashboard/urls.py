from django.urls import path
from .views import *

urlpatterns = [
    path("", public_dashboard, name="home"),
    path("search/", search, name="search"),
    path(
        "events/teacher/<teacher_id>", bookEventTeacherList, name="event_teacher_list"
    ),
    path("event/<event_id>/book", bookEventView.as_view(), name="book_event_per_id"),
    path("event/<event_id>/", EventView.as_view(), name="event_per_id"),
    path(
        "event/<event_id>/cancel/",
        CancelEventView.as_view(),
        name="event_per_id_cancel",
    ),
    path("inquiry/<inquiry_id>", InquiryView.as_view(), name="inquiry_detail_view"),
    path("impressum/", impressum, name="impressum"),
    path("export/", create_event_PDF, name="parent_generate_pdf"),
    path("announcements/", AnnouncementsAllUsers.as_view(), name="announcements"),
    path(
        "announcements/<announcement_id>/mark_read",
        markAnnouncementRead,
        name="mark_annuncement_read",
    ),
    path(
        "announcements/all_read/",
        markAllAnnouncementsRead,
        name="mark_all_announcements_read",
    ),
]
