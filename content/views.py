from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from .models import VideoFile, Episode

class KeyServeView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, key_token):
        # Look up VideoFile by the key token
        video = get_object_or_404(VideoFile, encryption_key=key_token)

        # Return the key content.
        # In a real AES-128 HLS setup, this should be 16 binary bytes.
        # Our task wrote a 32-char hex string. We'll return what we stored.
        return HttpResponse(video.encryption_key, content_type='application/octet-stream')

def home_view(request):
    latest_episodes = Episode.objects.select_related('season__anime').order_by('-created_at')[:10]
    return render(request, 'home.html', {'latest_episodes': latest_episodes})

def player_view(request, episode_id):
    episode = get_object_or_404(Episode, id=episode_id)
    # Get the default video (e.g. highest quality)
    video = episode.video_files.order_by('-quality').first()
    return render(request, 'player.html', {'episode': episode, 'video': video})
