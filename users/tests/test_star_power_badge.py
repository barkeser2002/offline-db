import pytest
from django.test import TestCase
from users.models import User, Badge, UserBadge
from content.models import Review, Anime, Genre
from users.services import check_badges

@pytest.mark.django_db
class TestStarPowerBadge(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='staruser', password='password')
        # Ensure badge exists
        self.badge, _ = Badge.objects.get_or_create(slug='star-power', defaults={'name': 'Star Power', 'description': 'desc'})

        self.genre = Genre.objects.create(name='Drama', slug='drama')

    def test_star_power_badge_awarded(self):
        # Create 5 reviews with 10 rating
        for i in range(5):
            anime = Anime.objects.create(title=f'Anime {i}', type='TV')
            Review.objects.create(user=self.user, anime=anime, rating=10, text='Perfect')

        check_badges(self.user)

        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_star_power_badge_not_awarded_mixed_ratings(self):
        # Create 4 reviews with 10 rating and 1 with 9
        for i in range(4):
            anime = Anime.objects.create(title=f'Anime {i}', type='TV')
            Review.objects.create(user=self.user, anime=anime, rating=10, text='Perfect')

        anime_fail = Anime.objects.create(title='Anime Fail', type='TV')
        Review.objects.create(user=self.user, anime=anime_fail, rating=9, text='Almost')

        check_badges(self.user)

        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_star_power_badge_not_awarded_insufficient_count(self):
        # Create 4 reviews with 10 rating
        for i in range(4):
            anime = Anime.objects.create(title=f'Anime {i}', type='TV')
            Review.objects.create(user=self.user, anime=anime, rating=10, text='Perfect')

        check_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
