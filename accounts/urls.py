from django.urls import include, path
from . import views

urlpatterns = [
    # path('/clips/', include('clips.urls')),
    path('login/', views.sign_in, name='sign_in'),
    path('logout/', views.sign_out, name='sign_out'),
    path('auth-receiver/', views.auth_receiver, name='auth_receiver'),
]