from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from content.models import Anime, Subscription

User = get_user_model()

class SubscriptionUITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.anime = Anime.objects.create(title="Test Anime")
        self.url = reverse('anime_detail', args=[self.anime.id])

    def test_context_contains_is_subscribed_authenticated(self):
        self.client.force_login(self.user)

        # Initial state: Not subscribed
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_subscribed'])

        # Subscribe
        Subscription.objects.create(user=self.user, anime=self.anime)

        # Check again
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_subscribed'])

    def test_context_contains_is_subscribed_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Should be False or key might exist as False
        self.assertFalse(response.context['is_subscribed'])

    def test_subscribe_api_view(self):
        self.client.force_login(self.user)
        api_url = reverse('anime-subscribe', args=[self.anime.id])

        # Test Subscribe
        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'subscribed')
        self.assertTrue(Subscription.objects.filter(user=self.user, anime=self.anime).exists())

        # Test Unsubscribe
        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'unsubscribed')
        self.assertFalse(Subscription.objects.filter(user=self.user, anime=self.anime).exists())
