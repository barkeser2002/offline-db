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
            message='Hello World',
            is_read=False
        )

        self.anime = Anime.objects.create(title='Test Anime API')

    def test_list_notifications(self):
        response = self.client.get('/api/v1/notifications/', secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # With pagination, results are in 'results'
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Notification')

    def test_list_notifications_filtering(self):
        # Create a read notification
        Notification.objects.create(
            user=self.user,
            title='Read Notification',
            message='Already read',
            is_read=True
        )

        # Test filter is_read=true
        response = self.client.get('/api/v1/notifications/?is_read=true', secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Read Notification')

        # Test filter is_read=false
        response = self.client.get('/api/v1/notifications/?is_read=false', secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Notification')

    def test_unread_count(self):
        # Initial count should be 1
        response = self.client.get('/api/v1/notifications/unread_count/', secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Add another unread
        Notification.objects.create(user=self.user, title='New', is_read=False)
        response = self.client.get('/api/v1/notifications/unread_count/', secure=True)
        self.assertEqual(response.data['count'], 2)

        # Add a read one
        Notification.objects.create(user=self.user, title='Read', is_read=True)
        response = self.client.get('/api/v1/notifications/unread_count/', secure=True)
        self.assertEqual(response.data['count'], 2)

    def test_mark_read(self):
        url = f'/api/v1/notifications/{self.notification.id}/mark_read/'
        response = self.client.post(url, secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_all_read(self):
        Notification.objects.create(user=self.user, title='Another one', message='Hi', is_read=False)
        url = '/api/v1/notifications/mark_all_read/'
        response = self.client.post(url, secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)

    def test_subscribe_anime(self):
        url = f'/api/v1/anime/{self.anime.id}/subscribe/'

        # Subscribe
        response = self.client.post(url, secure=True)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'subscribed')
        self.assertTrue(Subscription.objects.filter(user=self.user, anime=self.anime).exists())

        # Unsubscribe
        response = self.client.post(url, secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'unsubscribed')
        self.assertFalse(Subscription.objects.filter(user=self.user, anime=self.anime).exists())

    def test_bulk_update_status(self):
        n1 = Notification.objects.create(user=self.user, title='N1', is_read=False)
        n2 = Notification.objects.create(user=self.user, title='N2', is_read=False)
        n3 = Notification.objects.create(user=self.user, title='N3', is_read=False)

        # Test valid request
        url = '/api/v1/notifications/bulk-update/'
        data = {
            'notification_ids': [n1.id, n2.id],
            'is_read': True
        }
        response = self.client.post(url, data, format='json', secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated_count'], 2)

        n1.refresh_from_db()
        n2.refresh_from_db()
        n3.refresh_from_db()
        self.assertTrue(n1.is_read)
        self.assertTrue(n2.is_read)
        self.assertFalse(n3.is_read)

        # Test invalid payload
        data_invalid = {
            'notification_ids': 'not-a-list',
            'is_read': True
        }
        response_invalid = self.client.post(url, data_invalid, format='json', secure=True)
        self.assertEqual(response_invalid.status_code, status.HTTP_400_BAD_REQUEST)
