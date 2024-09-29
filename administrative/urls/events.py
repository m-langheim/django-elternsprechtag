from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from ..views.events import *

urlpatterns = [
    ## Events ##
    path(
        "",
        EventsListView.as_view(),
        name="administrative_event_list_view",
    ),
    path(
        "<event_id>/block",
        EventBlockView.as_view(),
        name="administrative_event_block_view",
    ),
    path(
        "formulars/",
        AdministrativeFormulaApprovalView.as_view(),
        name="administrative_event_formular_view",
    ),
    path(
        "formulars/add/new_date",
        EventAddNewDateAndFormularsView.as_view(),
        name="administrative_event_formular_new_date_add_view",
    ),
    path(
        "formulars/add/<event_group_id>",
        EventChangeFormularAddView.as_view(),
        name="administrative_event_formular_add_view",
    ),
    path(
        "formulars/<pk>/edit/",
        EditTimeSlotView.as_view(),
        name="administrative_event_formular_edit_view",
    ),
    path(
        "formulars/<int:formular_id>/approve/",
        EventChangeFormularApproveView.as_view(),
        name="administrative_event_formular_approve_view",
    ),
    path(
        "formulars/<int:formular_id>/disapprove/",
        EventChangeFormularDisapproveView.as_view(),
        name="administrative_event_formular_disapprove_view",
    ),
    path(
        "event/<event_id>/",
        EventDetailView.as_view(),
        name="administrative_event_detail_view",
    ),
    path(
        "event/<event_id>/clear/",
        EventClearView.as_view(),
        name="administrative_event_clear_view",
    ),
    path(
        "event/<event_id>/add_student/",
        EventAddStudentView.as_view(),
        name="administrative_event_add_student_view",
    ),
    path("base_event/", BaseEventsTableView.as_view(), name="base_events_table"),
    path(
        "base_event/<pk>/edit/", BaseEventDetailView.as_view(), name="base_event_edit"
    ),
    path(
        "base_event/<pk>/edit/lead_status/",
        BaseEventEditLeadStatusView.as_view(),
        name="base_event_edit_lead_status",
    ),
    path(
        "base_event/<pk>/edit/lead_dates/",
        BaseEventEditLeadDateView.as_view(),
        name="base_event_edit_lead_dates",
    ),
    path(
        "base_event/<base_event_pk>/teacher_day_groups/",
        TeacherDayEventGroupView.as_view(),
        name="teacher_day_event_group_table",
    ),
    path(
        "base_event/<base_event_pk>/teacher_day_groups/<pk>/",
        TeacherDayGroupDetailView.as_view(),
        name="teacher_day_event_group_detail",
    ),
    path(
        "base_event/<base_event_pk>/teacher_day_groups/<pk>/lead_status/",
        TeacherDayGroupEditLeadStatusView.as_view(),
        name="teacher_day_event_group_edit_lead_status",
    ),
    path(
        "base_event/<base_event_pk>/teacher_day_groups/<pk>/lead_dates/",
        TeacherDayGroupEditLeadDateView.as_view(),
        name="teacher_day_event_group_edit_lead_dates",
    ),
]
