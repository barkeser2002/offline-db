from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from content.models import Anime

User = get_user_model()

class ReviewXSSProtectionTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.anime = Anime.objects.create(title='Test Anime', synopsis='Test Description')
        self.client.force_authenticate(user=self.user)

    def test_review_xss_protection(self):
        url = reverse('review-list')
        data = {
            'anime': self.anime.id,
            'rating': 8,
            'text': '<script>alert("XSS")</script>This is a <b>great</b> show!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify HTML tags are stripped
        self.assertEqual(response.data['text'], 'alert("XSS")This is a great show!')
