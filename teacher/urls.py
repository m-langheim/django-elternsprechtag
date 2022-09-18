from unicodedata import name
from django.urls import path
from .views import *

urlpatterns = [
    path('', dashboard, name="teacher_dashboard"),
    path('students/', studentList, name="teacher_students_list"),
    path('inquiry/create/<id>', CreateInquiryView.as_view(),
         name="teacher_create_inquiry"),
    path('inquiry/<id>', InquiryView.as_view(), name="teacher_show_inquiry")
]
