import os
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests

User = get_user_model()

@csrf_exempt
def sign_in(request):
    return render(request, 'accounts/sign_in.html')

@csrf_exempt
def auth_receiver(request):
    """
    Google calls this URL after the user has signed in with their Google account.
    """
    print('Inside')
    token = request.POST['credential']

    try:
        user_data = id_token.verify_oauth2_token(
            token, requests.Request(), os.environ['GOOGLE_OAUTH_CLIENT_ID']
        )
    except ValueError:
        return HttpResponse(status=403)

    email = user_data.get('email')
    name = user_data.get('name')

    if not email:
        return HttpResponse("No email in token", status=400)

    # Get or create the user
    user, created = User.objects.get_or_create(
        username=email,
        defaults={'email': email, 'first_name': name}
    )
    login(request, user)
    return redirect('sign_in')

@login_required
def sign_out(request):
    logout(request)
    return redirect('sign_in')