from django.shortcuts import render


def home(request):
    return render(request, 'pincorder_desktop/templates/home.html')


def login(request):
    return render(request, 'pincorder_desktop/templates/security/login.html')
