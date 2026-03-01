from rest_framework import serializers, viewsets, permissions, status
from rest_framework.response import Response
from django.db import IntegrityError
from users.services import check_badges
from ..models import Review, Anime

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit or delete it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the review.
        return obj.user == request.user

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'anime', 'rating', 'text', 'created_at']
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ReviewViewSet(viewsets.ModelViewSet):
    # Optimization: Use select_related('user') to avoid N+1 queries when serializing the user field
    queryset = Review.objects.select_related('user').all().order_by('-created_at')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {"detail": "You have already reviewed this anime."},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)
        # Check for Critic badge
        check_badges(user)
