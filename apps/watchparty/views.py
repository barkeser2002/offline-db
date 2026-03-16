from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from .models import Room
from .serializers import RoomSerializer
from .permissions import IsHostOrReadOnly

@extend_schema_view(
    list=extend_schema(summary="List active watch party rooms"),
    create=extend_schema(summary="Create a new watch party room"),
    retrieve=extend_schema(summary="Retrieve watch party room details"),
    update=extend_schema(summary="Update watch party room"),
    partial_update=extend_schema(summary="Partially update watch party room"),
    destroy=extend_schema(summary="Delete watch party room")
)
class RoomViewSet(viewsets.ModelViewSet):
    # Optimization: Added 'episode__season__anime' to select_related to avoid N+1 queries
    # caused by nested __str__ calls or serializers accessing deeper relations.
    queryset = Room.objects.filter(is_active=True).select_related(
        'episode', 'host', 'episode__season__anime'
    ).prefetch_related(
        'episode__video_files__fansub_group',
        'episode__external_sources'
    )
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsHostOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.password and instance.host != request.user:
            password = request.query_params.get('password')
            if not password or password != instance.password:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Incorrect or missing password for this room.")
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)

    def perform_update(self, serializer):
        if self.request.user != serializer.instance.host:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to edit this room.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.host:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to delete this room.")
        instance.delete()

    @extend_schema(summary="List rooms hosted by the current user")
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_rooms(self, request):
        # Optimization: Added 'episode__season__anime' to select_related to avoid N+1 queries
        rooms = Room.objects.filter(host=request.user).select_related(
            'episode', 'host', 'episode__season__anime'
        ).prefetch_related(
            'episode__video_files__fansub_group',
            'episode__external_sources'
        )
        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data)
