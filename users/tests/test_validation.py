from django.test import TestCase
from django.core.exceptions import ValidationError
from users.models import User

class UserValidationTest(TestCase):
    def test_valid_username(self):
        user = User(username='valid_user-123', password='password123')
        user.full_clean()  # Should not raise ValidationError
        self.assertEqual(user.username, 'valid_user-123')

    def test_invalid_username_special_chars(self):
        user = User(username='invalid@user!', password='password123')
        with self.assertRaises(ValidationError) as context:
            user.full_clean()
        self.assertIn('username', context.exception.message_dict)

    def test_invalid_username_spaces(self):
        user = User(username='invalid user', password='password123')
        with self.assertRaises(ValidationError) as context:
            user.full_clean()
        self.assertIn('username', context.exception.message_dict)

    def test_invalid_username_xss(self):
        user = User(username='<script>alert(1)</script>', password='password123')
        with self.assertRaises(ValidationError) as context:
            user.full_clean()
        self.assertIn('username', context.exception.message_dict)
