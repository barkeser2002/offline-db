from django.http import HttpResponse, Http404
from rest_framework.views import APIView
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

from .models import Anime, Episode, Season, Subscription, VideoFile
from .serializers import (
    AnimeListSerializer, AnimeDetailSerializer, EpisodeSerializer,
    SubscriptionSerializer
)

class AnimeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Anime.objects.all().order_by('-created_at')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'english_title', 'japanese_title']
    filterset_fields = ['status', 'type', 'genres__name']
    ordering_fields = ['score', 'popularity', 'created_at', 'aired_from']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AnimeDetailSerializer
        return AnimeListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            return queryset.prefetch_related(
                'genres', 
                'seasons__episodes',
                'anime_characters__character',
                'seasons__episodes__video_files',
                'seasons__episodes__external_sources'
            )
        return queryset.prefetch_related('genres')

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        anime = self.get_object()
        subscription, created = Subscription.objects.get_or_create(
            user=request.user, 
            anime=anime
        )
        
        if not created:
            subscription.delete()
            return Response({'status': 'unsubscribed'})
            
        return Response({'status': 'subscribed'}, status=status.HTTP_201_CREATED)

class EpisodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Episode.objects.all()
    serializer_class = EpisodeSerializer
    
    def get_queryset(self):
        return Episode.objects.select_related('season__anime').prefetch_related(
            'video_files__fansub_group',
            'external_sources'
        )

class HomeViewSet(viewsets.ViewSet):
    """
    API endpoint for Homepage data
    """
    def list(self, request):
        # Optimization: Add prefetch_related('genres') to avoid N+1 queries
        trending = Anime.objects.prefetch_related('genres').order_by('-popularity')[:10]
        latest_episodes = Episode.objects.select_related('season__anime').prefetch_related(
            'video_files__fansub_group',
            'external_sources'
        ).order_by('-created_at')[:12]
        # Optimization: Add prefetch_related('genres') to avoid N+1 queries
        seasonal = Anime.objects.filter(status='Currently Airing').prefetch_related('genres').order_by('-score')[:10]
        
        return Response({
            'trending': AnimeListSerializer(trending, many=True).data,
            'latest_episodes': EpisodeSerializer(latest_episodes, many=True).data,
            'seasonal': AnimeListSerializer(seasonal, many=True).data
        })


class KeyServeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Lookup by ID (UUID) not encryption_key (Secret)
        video = get_object_or_404(VideoFile.objects.select_related('episode__season__anime'), pk=pk)

        # Premium Check: 1080p requires premium
        if video.quality == '1080p' and not getattr(request.user, 'is_premium', False):
            return Response({'detail': 'Premium required for 1080p'}, status=status.HTTP_403_FORBIDDEN)

        # Return key content as text/plain (since it is stored as hex string in file)
        return HttpResponse(video.encryption_key, content_type='text/plain')
