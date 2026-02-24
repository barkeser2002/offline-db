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
                'anime_characters__character'
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
        trending = Anime.objects.order_by('-popularity')[:10]
        latest_episodes = Episode.objects.select_related('season__anime').prefetch_related(
            'video_files__fansub_group',
            'external_sources'
        ).order_by('-created_at')[:12]
        seasonal = Anime.objects.filter(status='Currently Airing').order_by('-score')[:10]
        
        return Response({
            'trending': AnimeListSerializer(trending, many=True).data,
            'latest_episodes': EpisodeSerializer(latest_episodes, many=True).data,
            'seasonal': AnimeListSerializer(seasonal, many=True).data
        })

