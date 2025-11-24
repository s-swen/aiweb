import json
import os
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from pytube import YouTube
import assemblyai as aai


@login_required
def index(request):
    return render(request, 'index.html')

def yt_title(link):
    yt = YouTube(link)
    return yt.title

def download_audio(link):
    yt = YouTube(link)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)
    return new_file

def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key = "ef647f668cc54efba526b8efe70a0486"
    transcriber = aai.transcriber()
    transcript = transcriber.transcribe(audio_file)
    return transcript.text


@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) # why this and not request.POST
            yt_link = data['link']
            return JsonResponse({'content': yt_link})
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invald data sent'}, status=400)
        # get yt title
        title = yt_title(yt_link)

        # get transcript
        # use open ai to generate the nlob
        # save blog article to database
        # return blog article as a response
    else:
        return JsonResponse({'error': 'Invalid method'}, status=405)
    

    

def user_login(request):
    if request.method == 'POST':
        username= request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})

    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('/')


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
