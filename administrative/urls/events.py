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
]
