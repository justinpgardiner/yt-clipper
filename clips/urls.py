from django.urls import include, path

from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("build/", views.build, name="build"),
    path("clip_video/", views.build, name="clip_video"),
    path("accounts/", include('accounts.urls')),
    path('', include('home.urls')),
]