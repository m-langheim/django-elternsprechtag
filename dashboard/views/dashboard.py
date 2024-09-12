from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from authentication.models import CustomUser, TeacherExtraData, Student, Tag
from ..models import Event, Inquiry, SiteSettings, Announcements
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.views import View
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator

from django.shortcuts import get_object_or_404
from django.urls import reverse

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes

from ..forms import BookForm, cancelEventForm, EditEventForm
from ..decorators import lead_started, parent_required
from django.contrib import messages
from django.http import Http404

from django.conf import settings
import pytz

from ..utils import check_inquiry_reopen, check_parent_book_event_allowed

from general_tasks.utils import EventPDFExport
import datetime
from django.http import FileResponse

import logging

from ..helpers import create_event_date_dict, event_date_dict_add_book_information

parent_decorators = [login_required, parent_required]


@login_required
@parent_required
def public_dashboard(request):
    inquiries = Inquiry.objects.filter(Q(type=0), Q(respondent=request.user))
    # create individual link for each inquiry
    custom_inquiries = []
    for inquiry in inquiries:
        custom_inquiries.append(
            {
                "inquiry": inquiry,
                "url": reverse(
                    "inquiry_detail_view",
                    args=[urlsafe_base64_encode(force_bytes(inquiry.id))],
                ),
            }
        )

    # Hier werden alle events anhand ihres Datums aufgeteilt
    events = Event.objects.filter(Q(parent=request.user), Q(occupied=True))
    events_dict = create_event_date_dict(events)

    announcements = Announcements.objects.filter(
        Q(user=request.user), Q(read=False)
    ).order_by("-created")

    return render(
        request,
        "dashboard/public_dashboard.html",
        {
            "inquiries": custom_inquiries,
            "events_dict": events_dict,
            "events": events,
            "announcements": announcements,
        },
    )

# put language of events_dict announcements...


@login_required
@parent_required
def search(request):
    teachers = CustomUser.objects.filter(role=1)
    teacherExtraData = TeacherExtraData.objects.all()
    request_search = request.GET.get("q", None)
    state = 0
    result = []
    page_number = request.GET.get("page")

    if request_search is None:
        # print("Keine Frage")
        result = teachers
    # elif request_search.startswith("#"):
    #     request_search = request_search[1:]
    #     tags = Tag.objects.filter(
    #         Q(name__icontains=request_search) | Q(synonyms__icontains=request_search)
    #     ).order_by(
    #         "name"
    #     )  # get a list of all matching tags

    #     for tag in tags:
    #         extraData = teacherExtraData.filter(tags=tag)

    #         for data in extraData:
    #             teacher = data.teacher
    #             if not teacher in result:
    #                 result.append(teacher)
    # else:
    #     for data in (
    #         teachers.filter(last_name__icontains=request_search)
    #         .order_by("first_name")
    #         .order_by("last_name")
    #     ):
    #         if not data in result:
    #             result.append(data)
    #     # result = teachers.filter(last_name__icontains=request_search)
    #     for data in teacherExtraData.filter(acronym__icontains=request_search):
    #         if not data.teacher in result:
    #             result.append(data.teacher)
    else:
        search_split = str(request_search).split()
        if len(search_split) == 0:
            result = teachers
        else:
            search_teacher_name = CustomUser.objects.none()
            search_extradata_acronym = CustomUser.objects.none()
            search_tags = Tag.objects.none()
            for key in search_split:
                print(key, "Key")
                queryset_name = CustomUser.objects.filter(
                    Q(is_active=True), Q(role=1)
                ).filter(Q(first_name__icontains=key) | Q(last_name__icontains=key))

                queryset_tags = Tag.objects.filter(
                    Q(name__icontains=key) | Q(synonyms__icontains=key)
                )

                search_tags = search_tags.union(search_tags, queryset_tags)

                queryset_acronym = TeacherExtraData.objects.filter(
                    acronym__icontains=key
                )

                search_extradata_acronym = search_extradata_acronym.union(
                    search_extradata_acronym, queryset_acronym
                )

                if search_teacher_name.intersection(
                    search_teacher_name, queryset_name
                ).exists():
                    print("Exists")
                    search_teacher_name = search_teacher_name.intersection(
                        search_teacher_name, queryset_name
                    )
                else:
                    search_teacher_name = search_teacher_name.union(
                        search_teacher_name, queryset_name
                    )

                print(queryset_name, queryset_acronym, queryset_tags)
            # search_teacher = CustomUser.objects.none()
            search_teacher = []
            search_extradata_tags = TeacherExtraData.objects.none()
            search_extradata = TeacherExtraData.objects.none()

            for tag in search_tags:
                new_extradata = TeacherExtraData.objects.filter(tags=tag)
                search_extradata_tags = search_extradata_tags.union(
                    search_extradata_tags, new_extradata
                )

            search_extradata = search_extradata.union(
                search_extradata_acronym, search_extradata_tags
            )

            # TODO: Hier sollte es auch mit Union gemacht werden, um weiterhin ein Queryset zu erhalten, welches sortiert werden kann und damit nur die Übereinstimmungen zwischen mehreren Querysets genommen werden und somit nach möglichkeit eine eindeutige Lehrerwahl entsteht
            for extradata in search_extradata:
                if not extradata.teacher in search_teacher:
                    search_teacher.append(extradata.teacher)
            for teacher in search_teacher_name:
                if not teacher in search_teacher:
                    search_teacher.append(teacher)
            # print(search_teacher)

            # for extradata in search_extradata:
            #     new_teacher = extradata.teacher
            #     search_teacher = search_teacher.union(search_teacher, new_teacher)
            #     print(search_teacher)
            # print(search_extradata_tags, search_extradata_acronym, search_extradata)
            result = search_teacher
    custom_result = []

    for teacher in result:
        teacher_id = urlsafe_base64_encode(force_bytes(teacher.id))
        custom_result.append(
            {
                "first_name": teacher.first_name,
                "last_name": teacher.last_name,
                "email": teacher.email,
                "url": reverse("event_teacher_list", args=[teacher_id]),
            }
        )  # notwendig um den Url parameter zu dem queryset hinzu zu fügen
    # return render(request, 'dashboard/search.html', {'teachers': result, 'search': request_search})

    paginator = Paginator(custom_result, 25)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "dashboard/search.html",
        {"teachers": page_obj, "state": state, "request_search": request_search},
    )


def impressum(request):
    try:
        settings = SiteSettings.objects.first()
    except SiteSettings.DoesNotExist:
        raise Http404("Es wurden keine Einstellungen für diese Seite gefunden.")
    else:
        return redirect(settings.impressum)
