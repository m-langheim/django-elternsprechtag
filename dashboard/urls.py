from django.urls import path
from .views import *

urlpatterns = [
    path('', public_dashboard, name='home'),
    path('search/', search, name='search'),
    path('events/teacher/<teacher_id>',
         bookEventTeacherList, name='event_teacher_list'),
#     path('event/<event_id>/book',
#          bookEvent, name='book_event_per_id'),
    path('event/<event_id>/',
         eventView, name='event_per_id'),
    path('inquiry/<inquiry_id>', inquiryView, name="inquiry_detail_view")
]
