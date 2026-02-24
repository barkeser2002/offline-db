from rest_framework import generics, permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Notification, UserBadge, WatchLog, Badge
from .serializers import NotificationSerializer, UserBadgeSerializer, WatchLogSerializer
from .services import check_badges

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'notifications'

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user).order_by('-created_at')
        is_read_param = self.request.query_params.get('is_read')

        if is_read_param is not None:
            if is_read_param.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_read=True)
            elif is_read_param.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_read=False)
        return queryset

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'count': count})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'all marked as read'})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

class UserBadgeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserBadgeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserBadge.objects.filter(user=self.request.user).select_related('badge')

class WatchLogViewSet(viewsets.ModelViewSet):
    serializer_class = WatchLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WatchLog.objects.filter(user=self.request.user).order_by('-watched_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        check_badges(self.request.user)

class UserProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        badges = UserBadge.objects.filter(user=user).select_related('badge')
        history = WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at')[:10]
        
        # Note: In a real app, create a ProfileSerializer.
        # Here constructing ad-hoc response for speed as per migration plan.
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_premium': getattr(user, 'is_premium', False),
            'date_joined': user.date_joined,
            'badges': UserBadgeSerializer(badges, many=True).data,
            'recent_history': WatchLogSerializer(history, many=True).data
        })
