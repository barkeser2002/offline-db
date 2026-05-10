from rest_framework import generics, permissions, status, viewsets, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import ScopedRateThrottle, UserRateThrottle, AnonRateThrottle
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from .models import Notification, UserBadge, WatchLog, Badge, Follow, UserAnimeList, User
from .serializers import NotificationSerializer, UserBadgeSerializer, WatchLogSerializer, UserProfileUpdateSerializer, FollowSerializer, UserAnimeListSerializer, ActivitySerializer
from django.db.models import Q

class LoginThrottle(AnonRateThrottle):
    scope = 'login'

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

class UserBadgeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserBadgeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserBadge.objects.filter(user=self.request.user).select_related('badge')

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
            'bio': getattr(user, 'bio', ''),
            'is_premium': getattr(user, 'is_premium', False),
            'date_joined': user.date_joined,
            'badges': UserBadgeSerializer(badges, many=True).data,
            'recent_history': WatchLogSerializer(history, many=True).data
        })

    def patch(self, request):
        user = request.user
        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # For Follow, owner is the follower
        if hasattr(obj, 'follower'):
            return obj.follower == request.user
        # For UserAnimeList, owner is the user
        return obj.user == request.user

class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        # You can see followers and following if you are the user
        return Follow.objects.filter(Q(follower=user) | Q(following=user))

    def create(self, request, *args, **kwargs):
        following_id = request.data.get('following')
        if not following_id:
            return Response({"error": "following field is required"}, status=status.HTTP_400_BAD_REQUEST)
        if str(following_id) == str(request.user.id):
            return Response({"error": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        # Avoid IntegrityError by using get_or_create
        follow, created = Follow.objects.get_or_create(follower=request.user, following_id=following_id)
        if not created:
            return Response({"error": "You are already following this user."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def unfollow(self, request):
        following_id = request.data.get('following_id')
        if not following_id:
            return Response({"error": "following_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        deleted, _ = Follow.objects.filter(follower=request.user, following_id=following_id).delete()
        if deleted:
            return Response({"status": "unfollowed"}, status=status.HTTP_200_OK)
        return Response({"error": "You are not following this user"}, status=status.HTTP_404_NOT_FOUND)

class UserAnimeListViewSet(viewsets.ModelViewSet):
    serializer_class = UserAnimeListSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        # Default to the logged-in user's list
        user_id = self.request.query_params.get('user_id', user.id)

        if str(user_id) != str(user.id):
            target_user = get_object_or_404(User, id=user_id)
            if not target_user.is_public:
                # If they are not public, you must be following them or it must be you
                is_following = Follow.objects.filter(follower=user, following=target_user).exists()
                if not is_following:
                    return UserAnimeList.objects.none()

        return UserAnimeList.objects.filter(user_id=user_id).order_by('-updated_at')

    def create(self, request, *args, **kwargs):
        anime_id = request.data.get('anime')
        list_status = request.data.get('status', 'watchlist')
        if not anime_id:
            return Response({"error": "anime field is required"}, status=status.HTTP_400_BAD_REQUEST)

        anime_list, created = UserAnimeList.objects.get_or_create(
            user=request.user,
            anime_id=anime_id,
            defaults={'status': list_status}
        )
        if not created:
            # Update status instead of erroring
            anime_list.status = list_status
            anime_list.save()
            status_code = status.HTTP_200_OK
        else:
            status_code = status.HTTP_201_CREATED

        serializer = self.get_serializer(anime_list)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ActivityFeedViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        user = request.user

        following_users = Follow.objects.filter(follower=user).values_list('following', flat=True)

        # Badges awarded to followed users
        badges = UserBadge.objects.filter(user__in=following_users).select_related('user', 'badge').order_by('-awarded_at')[:20]

        # WatchLogs for followed users (only if public or following, well we are following them)
        watches = WatchLog.objects.filter(user__in=following_users).select_related('user', 'episode__season__anime').order_by('-watched_at')[:20]

        activities = []
        for b in badges:
            activities.append({
                'activity_type': 'badge_earned',
                'user': b.user,
                'created_at': b.awarded_at,
                'details': {
                    'badge_name': b.badge.name,
                    'badge_icon': b.badge.icon_url
                }
            })

        for w in watches:
            activities.append({
                'activity_type': 'episode_watched',
                'user': w.user,
                'created_at': w.watched_at,
                'details': {
                    'anime_title': w.episode.season.anime.title,
                    'episode_number': w.episode.number,
                }
            })

        # Sort combined activities by created_at descending
        activities.sort(key=lambda x: x['created_at'], reverse=True)

        # Take the top 20
        activities = activities[:20]

        serializer = ActivitySerializer(activities, many=True)
        return Response(serializer.data)
