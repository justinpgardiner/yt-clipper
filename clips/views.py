from django.shortcuts import render

def dashboard(request):
    return render(request, 'clips/dashboard.html')

def build(request):
    return render(request, 'clips/build.html')