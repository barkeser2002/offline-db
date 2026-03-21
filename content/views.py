from django.http import HttpResponse, Http404
from rest_framework.views import APIView
from rest_framework import viewsets, filters, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch, Avg
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .models import Anime, Episode, Season, Subscription, VideoFile
from .serializers import (
    AnimeListSerializer, AnimeDetailSerializer, EpisodeSerializer,
    SubscriptionSerializer
)

from rest_framework.throttling import UserRateThrottle

class SubscribeRateThrottle(UserRateThrottle):
    scope = 'subscribe'

@extend_schema_view(
    list=extend_schema(summary="List all animes"),
    retrieve=extend_schema(summary="Retrieve anime details"),
)
class AnimeViewSet(viewsets.ReadOnlyModelViewSet):
    @method_decorator(cache_page(60 * 5, key_prefix='anime_list'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    queryset = Anime.objects.annotate(avg_rating=Avg('reviews__rating')).order_by('-created_at')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'english_title', 'japanese_title']
    filterset_fields = ['status', 'type', 'genres__name']
    ordering_fields = ['score', 'popularity', 'created_at', 'aired_from', 'avg_rating']

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
                # Optimization: Prefetch fansub groups to avoid N+1 queries when accessing video_files.fansub_group
                'seasons__episodes__video_files__fansub_group',
                'seasons__episodes__external_sources'
            )
        # Optimization: Prefetch genres for list action to avoid N+1 queries from AnimeListSerializer
        return queryset.prefetch_related('genres')

    @extend_schema(
        summary="Subscribe/Unsubscribe to an anime",
        responses={201: OpenApiTypes.OBJECT, 200: OpenApiTypes.OBJECT}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], throttle_classes=[SubscribeRateThrottle])
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

@extend_schema_view(
    list=extend_schema(summary="List all episodes"),
    retrieve=extend_schema(summary="Retrieve episode details")
)
class EpisodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Episode.objects.all()
    serializer_class = EpisodeSerializer
    
    def get_queryset(self):
        # Optimization: Removed unnecessary select_related('season__anime')
        # since EpisodeSerializer does not use Season or Anime fields.
        return Episode.objects.prefetch_related(
            'video_files__fansub_group',
            'external_sources'
        )

@extend_schema_view(
    list=extend_schema(summary="Homepage dashboard data")
)
class HomeViewSet(viewsets.ViewSet):
    """
    API endpoint for Homepage data
    """
    @extend_schema(
        summary="Homepage dashboard data",
        responses={
            200: inline_serializer(
                name='HomeResponse',
                fields={
                    'trending': AnimeListSerializer(many=True),
                    'latest_episodes': EpisodeSerializer(many=True),
                    'seasonal': AnimeListSerializer(many=True),
                }
            )
        }
    )
    @method_decorator(cache_page(60 * 10, key_prefix='home_list'))
    def list(self, request):
        # Optimization: Add prefetch_related('genres') to avoid N+1 queries
        trending = Anime.objects.prefetch_related('genres').order_by('-popularity')[:10]

        # Optimization: Removed unnecessary select_related('season__anime')
        # since EpisodeSerializer does not use Season or Anime fields.
        latest_episodes = Episode.objects.prefetch_related(
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

    @extend_schema(
        summary="Serve HLS encryption key",
        responses={200: OpenApiTypes.STR, 403: OpenApiTypes.OBJECT}
    )
    def get(self, request, pk):
        # Lookup by ID (UUID) not encryption_key (Secret)
        # Optimization: Removed `select_related('episode__season__anime')` as we only access `quality` and `encryption_key`.
        video = get_object_or_404(VideoFile, pk=pk)

        # Premium Check: 1080p requires premium
        if video.quality == '1080p' and not getattr(request.user, 'is_premium', False):
            return Response({'detail': 'Premium required for 1080p'}, status=status.HTTP_403_FORBIDDEN)

        # Return key content as text/plain (since it is stored as hex string in file)
        return HttpResponse(video.encryption_key, content_type='text/plain')
