from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User, WatchLog, Badge, UserBadge
from content.models import Anime, Season, Episode

class WatchLogAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=self.user)

        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episodes = []
        for i in range(1, 10):
            ep = Episode.objects.create(season=self.season, number=i)
            self.episodes.append(ep)

        self.binge_badge, _ = Badge.objects.get_or_create(
            slug='binge-watcher',
            defaults={
                'name': 'Binge Watcher',
                'description': 'Watched 5 episodes in 24 hours'
            }
        )

        self.url = reverse('watch-log-create')

    def test_create_watch_log(self):
        data = {
            'episode': self.episodes[0].id,
            'duration': 1200
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WatchLog.objects.count(), 1)
        self.assertEqual(WatchLog.objects.first().episode, self.episodes[0])
        self.assertEqual(WatchLog.objects.first().user, self.user)

    def test_create_watch_log_triggers_badge(self):
        # Create 4 watch logs manually
        for i in range(4):
            WatchLog.objects.create(
                user=self.user,
                episode=self.episodes[i],
                duration=1200
            )

        # Verify no badge yet
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.binge_badge).exists())

        # Create 5th watch log via API
        data = {
            'episode': self.episodes[4].id,
            'duration': 1200
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify badge awarded
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.binge_badge).exists())
