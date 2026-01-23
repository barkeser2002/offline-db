from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import ScopedRateThrottle
from .models import Notification, UserBadge, WatchLog, Badge
from .serializers import NotificationSerializer, UserBadgeSerializer, WatchLogSerializer
from .services import check_badges

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        is_read_param = self.request.query_params.get('is_read')

        if is_read_param is not None:
            if is_read_param.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_read=True)
            elif is_read_param.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_read=False)

        return queryset

class UnreadNotificationCountAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'notifications'

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'count': count})

class MarkNotificationReadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'notifications'

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({'status': 'marked as read'})
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

class MarkAllNotificationsReadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'notifications'

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'all marked as read'})

class UserBadgeListAPIView(generics.ListAPIView):
    serializer_class = UserBadgeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserBadge.objects.filter(user=self.request.user).select_related('badge')

class WatchLogCreateAPIView(generics.CreateAPIView):
    serializer_class = WatchLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        check_badges(self.request.user)

@login_required
def profile_view(request):
    user = request.user
    badges = UserBadge.objects.filter(user=user).select_related('badge')
    history = WatchLog.objects.filter(user=user).select_related('episode', 'episode__season__anime').order_by('-watched_at')[:10]

    context = {
        'user': user,
        'badges': badges,
        'history': history,
    }
    return render(request, 'profile.html', context)

def badges_list_view(request):
    all_badges = Badge.objects.all().order_by('name')
    earned_slugs = set()

    if request.user.is_authenticated:
        earned_slugs = set(UserBadge.objects.filter(user=request.user).values_list('badge__slug', flat=True))

    context = {
        'all_badges': all_badges,
        'earned_slugs': earned_slugs,
    }
    return render(request, 'badges_list.html', context)
