from django.test import TestCase
from users.models import User, Badge, UserBadge
from content.models import Review, Anime

class OpinionatedBadgeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        # Ensure badge exists
        self.badge, _ = Badge.objects.get_or_create(
            slug='opinionated',
            defaults={
                'name': 'Opinionated',
                'description': 'Wrote 5 reviews.',
                'icon_url': '/static/badges/opinionated.png',
            }
        )

        self.animes = [Anime.objects.create(title=f"Anime {i}") for i in range(5)]

    def test_opinionated_badge_awarded(self):
        # Write 4 reviews
        for i in range(4):
            Review.objects.create(
                user=self.user,
                anime=self.animes[i],
                rating=5,
                text="Good"
            )

        # Check badge not awarded
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

        # Write 5th review
        Review.objects.create(
            user=self.user,
            anime=self.animes[4],
            rating=5,
            text="Good"
        )

        # Check badge awarded
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
