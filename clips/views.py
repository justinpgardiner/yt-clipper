from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def dashboard(request):
    return render(request, 'clips/dashboard.html')

def build(request):
    return render(request, 'clips/build.html')

@login_required
def clip_video(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        units = request.POST.get('units')
    return render(request, 'clips/build.html')