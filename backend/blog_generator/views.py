import json
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from googleapiclient.discovery import build
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi  # UPDATED
import os

from .models import BlogPost

load_dotenv() 
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))  # UPDATED

# YouTube API client
youtube = build("youtube", "v3", developerKey=os.environ.get("YOUTUBE_API_KEY"))  # UPDATED

@login_required
def index(request):
    return render(request, 'index.html')


def yt_title(link):
    """Return title using YouTube Data API"""
    try:
        from urllib.parse import urlparse, parse_qs
        url_data = urlparse(link)
        query = parse_qs(url_data.query)
        video_id = query.get("v")
        if not video_id:
            video_id = [url_data.path.split("/")[-1]]
        video_id = video_id[0]

        request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()
        items = response.get("items")
        if not items:
            return None
        return items[0]["snippet"]["title"]
    except Exception as e:
        print("YT TITLE ERROR:", e)
        return None

def download_audio(link):
    """Removed — not used, return None"""
    return None

def get_transcription(link):
    """Fetch YouTube auto-generated transcript correctly"""
    try:
        from urllib.parse import urlparse, parse_qs
        url_data = urlparse(link)
        query = parse_qs(url_data.query)
        video_id = query.get("v")
        if not video_id:
            video_id = [url_data.path.split("/")[-1]]
        video_id = video_id[0]

        # ✅ Correct usage
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        transcript_text = " ".join([t['text'] for t in transcript_list])
        return transcript_text

    except Exception as e:
        print("TRANSCRIPT ERROR:", e)
        return None

def generate_blog_from_transcript(transcription):
    """Generate blog from title + description"""
    prompt = f"""
    Generate a blog post from the YouTube video metadata.
    Make it super readable by using emojis, fonts, spacing, and horizontal lines.
    Be personable, hand-holding, and visual.

    Metadata/Description:
    {transcription}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200
    )
    return response.choices[0].message.content

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent'}, status=400)

        title = yt_title(yt_link)
        if not title:
            return JsonResponse({'error': 'Could not fetch YouTube title'}, status=400)

        transcription = get_transcription(yt_link)
        if not transcription:
            transcription = f"No description available for '{title}'"  # fallback

        blog_content = generate_blog_from_transcript(transcription)
        if not blog_content:
            return JsonResponse({'error': 'Failed to generate blog article'}, status=500)
        
        new_blog = BlogPost(
            user=request.user,
            youtube_title= title,
            youtube_link=yt_link,
            generated_content=blog_content
        )
        new_blog.save()

        return JsonResponse({'content': blog_content})
    else:
        return JsonResponse({'error': 'Invalid method'}, status=405)


# Auth views remain unchanged
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login.html', {'error_message': 'Invalid username or password'})
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
                return render(request, 'signup.html', {'error_message': 'Something went wrong, please try again later...'})
        else:
            return render(request, 'signup.html', {'error_message': 'Passwords do not match...'})
    return render(request, 'signup.html')

def blog_list(request):
    blogs = BlogPost.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'all-blogs.html', {'blogs': blogs})

def blog_details(request, pk):
    blog = BlogPost.objects.get(pk=pk)
    if request.user != blog.user:
        return redirect('/')
    else:
        return render(request, 'blog-details.html', {'blog': blog})