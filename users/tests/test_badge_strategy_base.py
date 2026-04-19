from django.test import TestCase
from users.models import User, Badge, UserBadge
from users.badge_system import BadgeStrategy

class BadgeStrategyBaseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.badge, _ = Badge.objects.get_or_create(slug='test-badge', defaults={'name': 'Test'})
        self.strategy = BadgeStrategy()

    def test_award(self):
        awarded_slugs = set()
        all_badges = {'test-badge': self.badge}
        new_badges = []

        # Test basic _award
        self.strategy._award(self.user, 'test-badge', awarded_slugs, all_badges, new_badges)

        self.assertEqual(len(new_badges), 1)
        self.assertEqual(new_badges[0].badge.slug, 'test-badge')
        self.assertIn('test-badge', awarded_slugs)

    def test_check_raises_not_implemented(self):
        # The abstract check() method must raise NotImplementedError
        with self.assertRaises(NotImplementedError):
            self.strategy.check(self.user, set(), {}, [])
