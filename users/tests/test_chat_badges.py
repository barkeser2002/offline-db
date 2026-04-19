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
        self.all_badges = {b.slug: b for b in Badge.objects.all()}

    def check_badges(self, cache=None):
        awarded_slugs = set(UserBadge.objects.filter(user=self.user).values_list('badge__slug', flat=True))
        new_badges = []
        self.strategy.check(self.user, awarded_slugs, self.all_badges, new_badges, cache=cache)
        UserBadge.objects.bulk_create(new_badges)

    def test_commentator_badge(self):
        # Create 49 messages
        for i in range(49):
            ChatMessage.objects.create(user=self.user, room_name='room1', message=f'Msg {i}')
        self.check_badges()
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.commentator_badge).exists())

        # Create 50th message
        ChatMessage.objects.create(user=self.user, room_name='room1', message='Msg 50')
        self.check_badges()
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.commentator_badge).exists())

    def test_social_butterfly_badge(self):
        for i in range(4):
            ChatMessage.objects.create(user=self.user, room_name=f'room{i}', message='Hello')
        self.check_badges()
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.social_butterfly_badge).exists())

        ChatMessage.objects.create(user=self.user, room_name='room4', message='Hello')
        self.check_badges()
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.social_butterfly_badge).exists())

    def test_party_animal_badge(self):
        for i in range(4):
            ChatMessage.objects.create(user=self.user, room_name=f'party_{i}', message='Hello')
        self.check_badges()
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.party_animal_badge).exists())

        ChatMessage.objects.create(user=self.user, room_name='party_4', message='Hello')
        self.check_badges()
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.party_animal_badge).exists())

    def test_cache_miss(self):
        for i in range(50):
            ChatMessage.objects.create(user=self.user, room_name=f'party_{i%5}', message=f'Msg {i}')
        # call with no cache
        self.check_badges(cache=None)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.commentator_badge).exists())
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.social_butterfly_badge).exists())
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.party_animal_badge).exists())
