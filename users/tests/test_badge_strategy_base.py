import pytest
from django.test import TestCase
from users.models import User
from users.badge_system import BadgeStrategy

class BadgeStrategyTests(TestCase):
    def test_check_not_implemented(self):
        user = User.objects.create(username='test')
        strategy = BadgeStrategy()
        with self.assertRaises(NotImplementedError):
            strategy.check(user, set(), {}, [])
