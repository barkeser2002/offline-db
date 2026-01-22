from django.test import TestCase
from django.utils import timezone
from users.models import User, UserBadge, Badge
from content.models import WatchParty, Episode, Season, Anime
from users.services import check_badges

class TrendsetterBadgeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='host', password='password')
        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1)

        # Ensure the badge exists (it should be created by migration, but for test isolation we can get_or_create)
        Badge.objects.get_or_create(slug='trendsetter', defaults={'name': 'Trendsetter'})

    def test_award_trendsetter_badge(self):
        # Create a WatchParty hosted by user
        party = WatchParty.objects.create(host=self.user, episode=self.episode)

        # Simulate max participants reaching 5
        party.max_participants = 5
        party.save()

        # Check badges
        check_badges(self.user)

        # Assert badge is awarded
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge__slug='trendsetter').exists())

    def test_do_not_award_trendsetter_badge_if_below_threshold(self):
        # Create a WatchParty hosted by user
        party = WatchParty.objects.create(host=self.user, episode=self.episode)

        # Simulate max participants below 5
        party.max_participants = 4
        party.save()

        # Check badges
        check_badges(self.user)

        # Assert badge is NOT awarded
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge__slug='trendsetter').exists())
