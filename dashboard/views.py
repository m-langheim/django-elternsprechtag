from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required
def public_dashboard(request):
    students = request.user.students.all()
    print(students)
    return render(request, 'dashboard/public_dashboard.html')
