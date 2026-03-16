from rest_framework import generics, permissions, status, viewsets, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import ScopedRateThrottle, UserRateThrottle, AnonRateThrottle
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.shortcuts import get_object_or_404
from .models import Notification, UserBadge, WatchLog, Badge
from .serializers import NotificationSerializer, UserBadgeSerializer, WatchLogSerializer

class LoginThrottle(AnonRateThrottle):
    scope = 'login'

@extend_schema_view(
    post=extend_schema(summary="Obtain JWT token pair")
)
class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginThrottle]

class WatchLogCreateThrottle(UserRateThrottle):
    scope = 'watchlog'
    def allow_request(self, request, view):
        if request.method != 'POST':
            return True
        return super().allow_request(request, view)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

@extend_schema_view(
    list=extend_schema(summary="List user notifications"),
    retrieve=extend_schema(summary="Retrieve a notification")
)
class NotificationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
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

    @extend_schema(summary="Get unread notifications count", responses={200: OpenApiTypes.OBJECT})
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'count': count})

    @extend_schema(summary="Mark all notifications as read", responses={200: OpenApiTypes.OBJECT})
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'all marked as read'})

    @extend_schema(summary="Mark a notification as read", responses={200: OpenApiTypes.OBJECT})
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

    @extend_schema(
        summary="Bulk update notification read status",
        request=OpenApiTypes.OBJECT,
        examples=[
            OpenApiExample(
                'Bulk update example',
                value={"notification_ids": [1, 2, 3], "is_read": True}
            )
        ],
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update_status(self, request):
        """
        Bulk update is_read status for a list of notification IDs.
        Expected payload:
        {
            "notification_ids": [1, 2, 3],
            "is_read": true
        }
        """
        notification_ids = request.data.get('notification_ids', [])
        is_read = request.data.get('is_read')

        if not isinstance(notification_ids, list) or is_read is None:
            return Response(
                {"error": "Invalid payload. 'notification_ids' (list) and 'is_read' (boolean) are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not notification_ids:
             return Response({"status": "no notifications updated", "updated_count": 0})

        # Ensure users only update their own notifications
        updated_count = Notification.objects.filter(
            user=request.user,
            id__in=notification_ids
        ).update(is_read=is_read)

        return Response({
            "status": "success",
            "updated_count": updated_count
        })

@extend_schema_view(
    list=extend_schema(summary="List user badges"),
    retrieve=extend_schema(summary="Retrieve user badge details")
)
class UserBadgeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserBadgeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserBadge.objects.filter(user=self.request.user).select_related('badge')

@extend_schema_view(
    list=extend_schema(summary="List user watch history"),
    retrieve=extend_schema(summary="Retrieve a watch history entry"),
    create=extend_schema(summary="Create a new watch history entry")
)
class WatchLogViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = WatchLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WatchLogCreateThrottle]
    
    def get_queryset(self):
        return WatchLog.objects.filter(user=self.request.user).order_by('-watched_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        # Note: Badge checks are handled automatically via post_save signal in users.signals

class UserProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Get current user profile", responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        user = request.user
        badges = UserBadge.objects.filter(user=user).select_related('badge')
        # Optimization: WatchLogSerializer only serializes the 'episode' field (ID representation),
        # so select_related('episode__season__anime') causes an unnecessary DB join
        history = WatchLog.objects.filter(user=user).order_by('-watched_at')[:10]
        
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
