from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required
def public_dashboard(request):
    return render(request, 'dashboard/public_dashboard.html')
