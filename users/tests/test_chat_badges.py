from django.test import TestCase
from users.models import User, Badge, UserBadge
from core.models import ChatMessage
from users.badge_system import ChatBadgeStrategy

class ChatBadgeStrategyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='chatuser', password='pw')
        badges_info = {
            'commentator': 'Commentator',
            'social-butterfly': 'Social Butterfly',
            'party-animal': 'Party Animal',
        }
        self.all_badges = {}
        for slug, name in badges_info.items():
            badge, _ = Badge.objects.get_or_create(slug=slug, defaults={'name': name, 'description': ''})
            self.all_badges[slug] = badge

    def test_commentator_badge(self):
        strategy = ChatBadgeStrategy()
        for i in range(50):
            ChatMessage.objects.create(user=self.user, room_name='general', message='hi')
        new_badges = []
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)
        self.assertTrue(any(b.badge.slug == 'commentator' for b in new_badges))

    def test_social_butterfly_badge(self):
        strategy = ChatBadgeStrategy()
        for i in range(5):
            ChatMessage.objects.create(user=self.user, room_name=f'room{i}', message='hi')
        new_badges = []
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)
        self.assertTrue(any(b.badge.slug == 'social-butterfly' for b in new_badges))

    def test_party_animal_badge(self):
        strategy = ChatBadgeStrategy()
        for i in range(5):
            ChatMessage.objects.create(user=self.user, room_name=f'party_{i}', message='hi')
        new_badges = []
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)
        self.assertTrue(any(b.badge.slug == 'party-animal' for b in new_badges))

    def test_cache_miss(self):
        strategy = ChatBadgeStrategy()
        new_badges = []
        cache = {}
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)
        self.assertIn('chat_stats', cache)
