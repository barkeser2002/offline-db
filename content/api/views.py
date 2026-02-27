from rest_framework import serializers, viewsets, permissions, status
from rest_framework.response import Response
from django.db import IntegrityError
from users.services import check_badges
from ..models import Review, Anime

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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

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
