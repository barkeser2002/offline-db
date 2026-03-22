from django.test import TestCase
from users.serializers import UserProfileUpdateSerializer
from users.models import User

class UserProfileUpdateSerializerTest(TestCase):
    def test_username_xss_validation(self):
        user = User.objects.create(username="testuser")
        serializer = UserProfileUpdateSerializer(user, data={'username': '<script>alert(1)</script>'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_username_xss_validation_spaces(self):
        user = User.objects.create(username="testuser2")
        serializer = UserProfileUpdateSerializer(user, data={'username': 'test user'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_username_xss_validation_valid(self):
        user = User.objects.create(username="testuser3")
        serializer = UserProfileUpdateSerializer(user, data={'username': 'test-user_123'})
        self.assertTrue(serializer.is_valid())
