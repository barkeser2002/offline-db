from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from content.models import Anime, Season, Episode, Subscription
from users.models import Notification

User = get_user_model()

class NotificationSignalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='subscriber', password='password')
        self.anime = Anime.objects.create(title='Test Anime')
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.subscription = Subscription.objects.create(user=self.user, anime=self.anime)

    def test_notification_created_on_new_episode(self):
        # Create a new episode
        episode = Episode.objects.create(season=self.season, number=1, title='Pilot')

        # Check if notification is created
        self.assertTrue(Notification.objects.filter(user=self.user).exists())
        notification = Notification.objects.get(user=self.user)
        self.assertEqual(notification.title, f"New Episode: {self.anime.title}")
        self.assertIn("Episode 1", notification.message)
        self.assertFalse(notification.is_read)

class NotificationAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Hello World'
        )

        self.anime = Anime.objects.create(title='Test Anime API')

    def test_list_notifications(self):
        response = self.client.get('/api/users/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Notification')

    def test_mark_read(self):
        url = f'/api/users/notifications/{self.notification.id}/read/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_all_read(self):
        Notification.objects.create(user=self.user, title='Another one', message='Hi')
        url = '/api/users/notifications/read-all/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)

    def test_subscribe_anime(self):
        url = f'/api/anime/{self.anime.id}/subscribe/'

        # Subscribe
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'subscribed')
        self.assertTrue(Subscription.objects.filter(user=self.user, anime=self.anime).exists())

        # Unsubscribe
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'unsubscribed')
        self.assertFalse(Subscription.objects.filter(user=self.user, anime=self.anime).exists())
