from django.urls import path
from .views import NotificationListAPIView, MarkNotificationReadAPIView, MarkAllNotificationsReadAPIView

urlpatterns = [
    path('notifications/', NotificationListAPIView.as_view(), name='notification-list'),
    path('notifications/read-all/', MarkAllNotificationsReadAPIView.as_view(), name='notification-read-all'),
    path('notifications/<int:pk>/read/', MarkNotificationReadAPIView.as_view(), name='notification-read'),
]
