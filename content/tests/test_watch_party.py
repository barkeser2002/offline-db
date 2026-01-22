from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from users.models import User
from content.models import Anime, Season, Episode, WatchParty

class WatchPartyTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1)

    def test_create_watch_party(self):
        self.client.login(username='testuser', password='password')
        url = reverse('create_watch_party', args=[self.episode.id])
        response = self.client.get(url)
        # Should redirect
        self.assertEqual(response.status_code, 302)

        party = WatchParty.objects.first()
        self.assertIsNotNone(party)
        self.assertEqual(party.episode, self.episode)
        self.assertEqual(party.host, self.user)

        expected_url = reverse('watch_party_detail', args=[party.uuid])
        self.assertRedirects(response, expected_url)

    def test_watch_party_detail(self):
        party = WatchParty.objects.create(episode=self.episode, host=self.user)
        url = reverse('watch_party_detail', args=[party.uuid])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"party_{party.uuid}")
        self.assertContains(response, "Watch Party")
