from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Notification

User = get_user_model()

class NotificationDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.other_user = User.objects.create_user(username='other', password='password')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Hello World',
            is_read=False
        )

        self.other_notification = Notification.objects.create(
            user=self.other_user,
            title='Other',
            message='Hello',
            is_read=False
        )

    def test_delete_own_notification(self):
        url = f'/api/v1/notifications/{self.notification.id}/'
        response = self.client.delete(url, secure=True)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Notification.objects.filter(id=self.notification.id).exists())

    def test_delete_other_notification(self):
        url = f'/api/v1/notifications/{self.other_notification.id}/'
        response = self.client.delete(url, secure=True)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Notification.objects.filter(id=self.other_notification.id).exists())
