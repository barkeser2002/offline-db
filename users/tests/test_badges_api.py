from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User, Badge, UserBadge

class BadgeAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.badge = Badge.objects.create(
            slug='test-badge',
            name='Test Badge',
            description='A test badge'
        )
        self.url = reverse('user-badge-list')

    def test_get_badges_authenticated(self):
        self.client.force_authenticate(user=self.user)
        # Award badge
        UserBadge.objects.create(user=self.user, badge=self.badge)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['badge']['slug'], 'test-badge')

    def test_get_badges_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
