from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Notification, WatchLog
from content.models import Anime, Season, Episode

User = get_user_model()

class IDORAndAuthTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='testuser2', password='password123')
        self.client = APIClient()

        # Create data for user2
        self.notification_user2 = Notification.objects.create(
            user=self.user2,
            title='Test Notification',
            message='Hello World',
            is_read=False
        )

        anime = Anime.objects.create(title="Test Anime")
        season = Season.objects.create(anime=anime, number=1)
        self.episode = Episode.objects.create(season=season, number=1)

        self.watchlog_user2 = WatchLog.objects.create(
            user=self.user2,
            episode=self.episode,
            duration=100
        )

    def test_notification_mark_read_idor(self):
        # User 1 tries to mark User 2's notification as read
        self.client.force_authenticate(user=self.user1)
        url = f'/api/v1/notifications/{self.notification_user2.id}/mark_read/'
        response = self.client.post(url, secure=True)
        # Should return 404 because get_queryset filters by self.request.user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_notification_bulk_update_idor(self):
        # User 1 tries to bulk update User 2's notification
        self.client.force_authenticate(user=self.user1)
        url = '/api/v1/notifications/bulk-update/'
        data = {
            'notification_ids': [self.notification_user2.id],
            'is_read': True
        }
        response = self.client.post(url, data, format='json', secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # But it shouldn't actually update it
        self.notification_user2.refresh_from_db()
        self.assertFalse(self.notification_user2.is_read)
        self.assertEqual(response.data.get('updated_count'), 0)

    def test_watchlog_retrieve_idor(self):
        # User 1 tries to get User 2's watch log
        self.client.force_authenticate(user=self.user1)
        url = f'/api/v1/watch-history/{self.watchlog_user2.id}/'
        response = self.client.get(url, secure=True)
        # Should return 404 because get_queryset filters by self.request.user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_access(self):
        # Ensure unauthenticated users can't access these endpoints
        endpoints = [
            f'/api/v1/notifications/{self.notification_user2.id}/',
            '/api/v1/notifications/',
            '/api/v1/notifications/unread_count/',
            f'/api/v1/watch-history/{self.watchlog_user2.id}/',
            '/api/v1/watch-history/',
            '/api/v1/profile/'
        ]

        for url in endpoints:
            response = self.client.get(url, secure=True)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
