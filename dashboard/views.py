from django.shortcuts import render

# Create your views here.


def public_dashboard(request):
    return render(request, 'dashboard/public_dashboard.html')