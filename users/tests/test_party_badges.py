from django.test import TestCase
from users.models import User, Badge, UserBadge
from content.models import Anime, Season, Episode, WatchParty
from core.models import ChatMessage
from users.services import check_badges, check_chat_badges

class PartyBadgesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

        self.host_badge, _ = Badge.objects.get_or_create(
            slug='party-host',
            defaults={'name': 'Party Host', 'description': 'Hosted 5 Watch Parties'}
        )
        self.animal_badge, _ = Badge.objects.get_or_create(
            slug='party-animal',
            defaults={'name': 'Party Animal', 'description': 'Participated in 5 Watch Parties'}
        )

        self.anime = Anime.objects.create(title='Test Anime')
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1, title="Ep 1")

    def test_party_host_badge(self):
        # Create 4 parties, should not have badge
        for _ in range(4):
            WatchParty.objects.create(host=self.user, episode=self.episode)

        # Signals should trigger check_badges, but let's call it manually to be sure logic works
        check_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.host_badge).exists())

        # Create 5th party
        WatchParty.objects.create(host=self.user, episode=self.episode)
        check_badges(self.user)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.host_badge).exists())

    def test_party_animal_badge(self):
        # Create chat messages in 4 DIFFERENT rooms starting with party_
        for i in range(4):
            ChatMessage.objects.create(
                user=self.user,
                room_name=f"party_room_{i}",
                message="Hello"
            )

        check_chat_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.animal_badge).exists())

        # Create message in 5th room
        ChatMessage.objects.create(
            user=self.user,
            room_name="party_room_5",
            message="Hello"
        )
        check_chat_badges(self.user)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.animal_badge).exists())

    def test_party_animal_distinct_rooms(self):
        # Create 10 messages in SAME room
        for _ in range(10):
            ChatMessage.objects.create(
                user=self.user,
                room_name="party_room_1",
                message="Hello"
            )

        check_chat_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.animal_badge).exists())
