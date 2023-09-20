from django.urls import path
from .views import *

urlpatterns = [
    path("", MyProfileView.as_view(), name="profile_my_profile"),
    path("students/", StudentsListView.as_view(), name="profile_student_list"),
    path("change_password/", ChangePasswordView.as_view(),
         name="profile_change_password"),
    #path("tags/", EditTagsView.as_view(), name="profile_edit_tag_view")
    path("tags/", editTagsView, name="profile_edit_tag_view")
]
