from django.urls import path
from .views import NotificationListAPIView, MarkNotificationReadAPIView, MarkAllNotificationsReadAPIView, UnreadNotificationCountAPIView, UserBadgeListAPIView, WatchLogCreateAPIView

urlpatterns = [
    path('notifications/', NotificationListAPIView.as_view(), name='notification-list'),
    path('history/log/', WatchLogCreateAPIView.as_view(), name='watch-log-create'),
    path('badges/', UserBadgeListAPIView.as_view(), name='user-badge-list'),
    path('notifications/unread-count/', UnreadNotificationCountAPIView.as_view(), name='notification-unread-count'),
    path('notifications/read-all/', MarkAllNotificationsReadAPIView.as_view(), name='notification-read-all'),
    path('notifications/<int:pk>/read/', MarkNotificationReadAPIView.as_view(), name='notification-read'),
]
