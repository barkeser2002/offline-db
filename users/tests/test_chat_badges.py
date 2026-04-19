from django.test import TestCase
from users.models import User, Badge, UserBadge
from core.models import ChatMessage
from users.badge_system import ChatBadgeStrategy

class ChatBadgeStrategyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.commentator_badge, _ = Badge.objects.get_or_create(slug='commentator', defaults={'name': 'Commentator'})
        self.social_butterfly_badge, _ = Badge.objects.get_or_create(slug='social-butterfly', defaults={'name': 'Social Butterfly'})
        self.party_animal_badge, _ = Badge.objects.get_or_create(slug='party-animal', defaults={'name': 'Party Animal'})

        self.strategy = ChatBadgeStrategy()

    def test_commentator_badge(self):
        # 10 messages
        for i in range(10):
            ChatMessage.objects.create(user=self.user, room_name="room1", content=f"msg {i}")

        awarded_slugs = set()
        all_badges = {'commentator': self.commentator_badge}
        new_badges = []

        self.strategy.check(self.user, awarded_slugs, all_badges, new_badges, cache=None)

        self.assertEqual(len(new_badges), 1)
        self.assertEqual(new_badges[0].badge.slug, 'commentator')

    def test_social_butterfly_badge(self):
        # 5 distinct rooms
        for i in range(5):
            ChatMessage.objects.create(user=self.user, room_name=f"room_{i}", content="hello")

        awarded_slugs = set()
        all_badges = {'social-butterfly': self.social_butterfly_badge}
        new_badges = []

        self.strategy.check(self.user, awarded_slugs, all_badges, new_badges, cache={})

        self.assertEqual(len(new_badges), 1)
        self.assertEqual(new_badges[0].badge.slug, 'social-butterfly')

    def test_party_animal_badge(self):
        # 20 distinct rooms
        for i in range(20):
            ChatMessage.objects.create(user=self.user, room_name=f"room_pa_{i}", content="hello")

        awarded_slugs = set()
        all_badges = {'party-animal': self.party_animal_badge}
        new_badges = []

        self.strategy.check(self.user, awarded_slugs, all_badges, new_badges, cache={'chat_stats': []})

        self.assertEqual(len(new_badges), 1)
        self.assertEqual(new_badges[0].badge.slug, 'party-animal')

    def test_cache_miss(self):
        awarded_slugs = set()
        all_badges = {}
        new_badges = []

        # Test case where cache is passed without 'chat_stats' key
        cache = {}
        self.strategy.check(self.user, awarded_slugs, all_badges, new_badges, cache=cache)
        self.assertIn('chat_stats', cache)
