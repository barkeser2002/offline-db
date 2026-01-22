import pytest
from django.test import TestCase
from users.models import User, Badge, UserBadge
from content.models import Review, Anime, Genre
from users.services import check_badges

@pytest.mark.django_db
class TestReviewGuruBadge(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reviewer', password='password')
        # Ensure badge exists (seeded by migration)
        self.badge, _ = Badge.objects.get_or_create(slug='review-guru', defaults={'name': 'Review Guru', 'description': 'desc'})

        # Create dummy genre
        self.genre = Genre.objects.create(name='Action', slug='action')

    def test_review_guru_badge_awarded(self):
        # Create 20 reviews
        for i in range(20):
            anime = Anime.objects.create(title=f'Anime {i}', type='TV')
            Review.objects.create(user=self.user, anime=anime, rating=5, text='Good')

        check_badges(self.user)

        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_review_guru_badge_not_awarded(self):
        # Create 19 reviews
        for i in range(19):
            anime = Anime.objects.create(title=f'Anime {i}', type='TV')
            Review.objects.create(user=self.user, anime=anime, rating=5, text='Good')

        check_badges(self.user)

        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
