from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def dashboard(request):
    return render(request, 'clips/dashboard.html')

def build(request):
    return render(request, 'clips/build.html')

@login_required
def clip_video(request):
    clip_url = None
    if request.method == 'POST':
        url = request.POST.get('url')
        number_of_rings = request.POST.get('number_of_rings')
        color_of_rings = request.POST.get('color_of_rings')
        color_of_ball = request.POST.get('color_of_ball')
        color_of_subtitles = request.POST.get('color_of_subtitles')
        font_size = request.POST.get('font_size')
        try:
            font_size = int(font_size) if font_size else None
        except ValueError:
            font_size = None

        # Do your video clipping logic here...
        clip_url = 'videos/cjG0m9QUF340asmr_fixed.mp4'

    return render(request, 'clips/build.html', {'clip_url': clip_url})