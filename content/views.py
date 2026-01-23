from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.throttling import UserRateThrottle, ScopedRateThrottle
from .models import VideoFile, Episode, Anime, Subscription, Genre, WatchParty
from core.utils import rate_limit_ip

@rate_limit_ip(limit=20, period=60)
def search_view(request):
    query = request.GET.get('q')
    genre_name = request.GET.get('genre')

    results = Anime.objects.all()

    if query:
        results = results.filter(title__icontains=query)

    if genre_name:
        results = results.filter(genres__name__iexact=genre_name)

    results = results.order_by('-created_at')

    context = {
        'results': results,
        'query': query,
        'selected_genre': genre_name,
        'genres': Genre.objects.all(),
    }

    return render(request, 'search_results.html', context)

class KeyServeView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get(self, request, key_token):
        # Look up VideoFile by the key token
        video = get_object_or_404(VideoFile, encryption_key=key_token)

        # Return the key content.
        # In a real AES-128 HLS setup, this should be 16 binary bytes.
        # Our task wrote a 32-char hex string. We'll return what we stored.
        return HttpResponse(video.encryption_key, content_type='application/octet-stream')

def home_view(request):
    latest_episodes = cache.get('home_latest_episodes')
    if not latest_episodes:
        # Evaluate QuerySet to list to ensure data is fetched and cached
        latest_episodes = list(Episode.objects.select_related('season__anime').order_by('-created_at')[:10])
        cache.set('home_latest_episodes', latest_episodes, 900) # 15 minutes

    return render(request, 'home.html', {'latest_episodes': latest_episodes})

def player_view(request, episode_id):
    episode = get_object_or_404(Episode, id=episode_id)
    # Get the default video (e.g. highest quality)
    video = episode.video_files.order_by('-quality').first()
    return render(request, 'player.html', {'episode': episode, 'video': video})

def anime_detail(request, pk):
    anime = get_object_or_404(Anime, pk=pk)
    # Prefetch seasons and episodes for efficient rendering
    seasons = anime.seasons.prefetch_related('episodes').order_by('number')

    is_subscribed = False
    if request.user.is_authenticated:
        is_subscribed = Subscription.objects.filter(user=request.user, anime=anime).exists()

    context = {
        'anime': anime,
        'seasons': seasons,
        'is_subscribed': is_subscribed,
    }
    return render(request, 'anime_detail.html', context)

class SubscribeAnimeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'subscribe'

    def post(self, request, pk):
        anime = get_object_or_404(Anime, pk=pk)
        subscription, created = Subscription.objects.get_or_create(user=request.user, anime=anime)

        if not created:
            subscription.delete()
            return Response({'status': 'unsubscribed'})

        return Response({'status': 'subscribed'})

@rate_limit_ip(limit=5, period=300)
@login_required
def create_watch_party(request, episode_id):
    episode = get_object_or_404(Episode, id=episode_id)
    party = WatchParty.objects.create(episode=episode, host=request.user)
    return redirect('watch_party_detail', uuid=party.uuid)

def watch_party_detail(request, uuid):
    party = get_object_or_404(WatchParty, uuid=uuid)
    episode = party.episode
    video = episode.video_files.order_by('-quality').first()

    room_name = f"party_{party.uuid}"

    context = {
        'episode': episode,
        'video': video,
        'party': party,
        'room_name': room_name,
    }
    return render(request, 'watch_party.html', context)
