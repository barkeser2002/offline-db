from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from content.models import Anime, Review

User = get_user_model()

class ReviewDeleteIDORTest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        self.anime = Anime.objects.create(title='Test Anime')
        self.review = Review.objects.create(user=self.user1, anime=self.anime, rating=9, text='Great show!')

    def test_user_cannot_delete_other_user_review(self):
        # Authenticate as user2
        self.client.force_authenticate(user=self.user2)

        # Try to delete user1's review
        url = reverse('review-detail', args=[self.review.id])
        response = self.client.delete(url)

        # This should fail if IDOR is patched
        self.assertNotEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
