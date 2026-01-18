from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from .models import VideoKey, Episode

class KeyServeView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, key_uuid):
        # Anti-IDM / Anti-Piracy Check:
        # Ensure the request comes from a valid user session.
        # Additional checks (User-Agent, Referer) could be added here.

        key_obj = get_object_or_404(VideoKey, id=key_uuid, is_active=True)

        # Return binary key with correct content type
        return HttpResponse(key_obj.key_content, content_type='application/octet-stream')

def home_view(request):
    # Landing page with latest episodes
    latest_episodes = Episode.objects.filter(is_processed=True).order_by('-created_at')[:10]
    return render(request, 'home.html', {'latest_episodes': latest_episodes})

def player_view(request, episode_id):
    episode = get_object_or_404(Episode, id=episode_id)
    return render(request, 'player.html', {'episode': episode})
