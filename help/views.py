from django.shortcuts import render

# Create your views here.

def register_help(request):
    return render(request, 'help/register_help/register_help.html', {'name':request.GET.get('u')})