from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileUpdateTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.url = reverse('user-profile')
        self.client.force_authenticate(user=self.user)

    def test_update_bio(self):
        data = {'bio': 'This is my new bio.'}
        response = self.client.patch(self.url, data, format='json', secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'This is my new bio.')

    def test_update_bio_html_strip(self):
        data = {'bio': '<script>alert("xss")</script>This is my <b>new</b> bio.'}
        response = self.client.patch(self.url, data, format='json', secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        # Bleach strip=True removes the tags entirely
        self.assertEqual(self.user.bio, 'alert("xss")This is my new bio.')

    def test_get_profile_includes_bio(self):
        self.user.bio = "My amazing bio"
        self.user.save()
        response = self.client.get(self.url, secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('bio'), "My amazing bio")
