from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from authentication.models import CustomUser

# Create your views here.


@login_required
def public_dashboard(request):
    students = request.user.students.all()
    print(students)
    return render(request, 'dashboard/public_dashboard.html')


@login_required
def search(request):
    teacher = CustomUser.objects.filter(role=1)
    request_search = request.GET.get('q', None)

    print(request_search)
    print(teacher)

    return render(request, 'dashboard/search.html', {'teachers': teacher})
