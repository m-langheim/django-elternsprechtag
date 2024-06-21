from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    path(
        "student_import/upload/",
        StudentImportStart.as_view(),
        name="student_import_filepload",
    ),
    path(
        "student_import/view/",
        StudentImportListChanges.as_view(),
        name="student_import_listchanges",
    ),
    path(
        "student_import/apply/all/",
        StudentImportApproveAndApplyAll.as_view(),
        name="student_import_apply_all_changes",
    ),
    path("students/", StudentListView.as_view(), name="student_list_view"),
]
