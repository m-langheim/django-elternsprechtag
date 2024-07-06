import django_filters
from dashboard.models import Event
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit


class EventFilter(django_filters.FilterSet):

    class Meta:
        model = Event
        fields = ["teacher", "start", "status"]


class EventFilterFormHelper(FormHelper):
    form_method = "GET"
    layout = ("teacher", "start", Submit("submit", "Filter"))
