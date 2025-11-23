from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate

def index(request):
    return render(request, 'index.html')

def user_login(request):
    pass

def user_logout(request):
    pass

def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        repeatPassword = request.POST['repeatPassword']
        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Something went wrong, please try again later...'
                return render(request, 'signup.html', {'error_message': error_message})
        else:
            error_message = 'Passwords do not match...'
            return render(request, 'signup.html', {'error_message': error_message})
    return render(request, 'signup.html')
