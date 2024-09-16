from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from ..views.users import *

urlpatterns = [
    ## Users ##
    path(
        "",
        RedirectView.as_view(pattern_name="parents_table"),
        name="administrative_users_view",
    ),
    path(
        "parents/",
        ParentTableView.as_view(),
        name="parents_table",
    ),
    path(
        "parents/<parent_id>/edit",
        ParentEditView.as_view(),
        name="parent_edit_view",
    ),
    path(
        "teachers/",
        TeacherTableView.as_view(),
        name="teachers_table",
    ),
    path(
        "teachers/import/",
        TeacherImportView.as_view(),
        name="teachers_import",
    ),
    path(
        "teachers/<pk>/edit",
        TeacherEditView.as_view(),
        name="teachers_edit_view",
    ),
]
