from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from .views import *

urlpatterns = [
    path("", AdministrativeDashboard.as_view(), name="administrative_dashboard"),
    ## Students ##
    path("students/", StudentListView.as_view(), name="student_list_view"),
    path(
        "students/<pk>/view", StudentDetailView.as_view(), name="student_details_view"
    ),
    path("students/<pk>/edit", StudentEdit.as_view(), name="student_edit_view"),
    path(
        "students/<pk>/send_registration_mail",
        UpcommingUserSendRegistrationMail.as_view(),
        name="administrative_student_send_registration_mail",
    ),
    path(
        "students/import/upload/",
        StudentImportStart.as_view(),
        name="student_import_filepload",
    ),
    path(
        "students/import/cancel/",
        StudentImportCancel.as_view(),
        name="student_import_cancel",
    ),
    path(
        "students/import/view/",
        StudentImportListChanges.as_view(),
        name="student_import_listchanges",
    ),
    path(
        "students/import/apply/all/",
        StudentImportApproveAndApplyAll.as_view(),
        name="student_import_apply_all_changes",
    ),
    path(
        "students/import/apply/<pk>/",
        StudentImportApproveAndApply.as_view(),
        name="student_import_apply_change",
    ),
    path(
        "students/import/apply/operation/<int:operation>/",
        StudentImportApproveAndApplyWithOperation.as_view(),
        name="student_import_apply_with_operation",
    ),
    ## Users ##
    path(
        "users/",
        RedirectView.as_view(pattern_name="parents_table"),
        name="administrative_users_view",
    ),
    path(
        "users/parents/",
        ParentTableView.as_view(),
        name="parents_table",
    ),
    path(
        "users/parents/<parent_id>/edit",
        ParentEditView.as_view(),
        name="parent_edit_view",
    ),
    path(
        "users/teachers/",
        TeacherTableView.as_view(),
        name="teachers_table",
    ),
    ## Events ##
    path(
        "events/",
        EventsListView.as_view(),
        name="administrative_event_list_view",
    ),
    path(
        "events/<event_id>/block",
        EventBlockView.as_view(),
        name="administrative_event_block_view",
    ),
    path(
        "events/formulars/",
        AdministrativeFormulaApprovalView.as_view(),
        name="administrative_event_formular_view",
    ),
    path(
        "events/formulars/add/",
        EventChangeFormularAddView.as_view(),
        name="administrative_event_formular_add_view",
    ),
    path(
        "events/formulars/<int:formular_id>/approve/",
        EventChangeFormularApproveView.as_view(),
        name="administrative_event_formular_approve_view",
    ),
    path(
        "events/formulars/<int:formular_id>/disapprove/",
        EventChangeFormularDisapproveView.as_view(),
        name="administrative_event_formular_disapprove_view",
    ),
]
