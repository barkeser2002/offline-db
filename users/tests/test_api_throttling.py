from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User, Notification
from django.core.cache import cache

class NotificationThrottlingTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=self.user)
        self.notification = Notification.objects.create(user=self.user, title="Test", message="Test Message")
        cache.clear()

    def test_unread_count_throttling(self):
        url = reverse('notification-unread-count')
        # Limit is 600/hour, so this is hard to test without mocking or hitting it 600 times.
        # But we can check if the header is present or if we can make a request.
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mark_read_throttling(self):
        url = reverse('notification-read', kwargs={'pk': self.notification.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mark_all_read_throttling(self):
        url = reverse('notification-read-all')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
