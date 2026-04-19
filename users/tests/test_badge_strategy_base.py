from django.test import TestCase
from users.badge_system import BadgeStrategy

class BadgeStrategyTests(TestCase):
    def test_check_not_implemented(self):
        strategy = BadgeStrategy()
        with self.assertRaises(NotImplementedError):
            strategy.check(None, None, None, None)
