from django.urls import path
from django.views.generic.base import RedirectView
from .views import register_help

urlpatterns = [
    # Der hier muss noch komplett raus (wir machen glaube ich keine Help mehr über eigene Seiten):
    path('register/', register_help, name="help_register"),

    path('redirect/wiki', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/'), name='wiki_mainpage'),
    path('redirect/wiki/public_dashboard', RedirectView.as_view(url='https://wiki.jhg-elternsprechtag.de/books/startseite'), name='wiki_public_dashboard')
]