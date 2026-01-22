from unittest.mock import patch, ANY
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from content.models import Anime, Season, Episode, Subscription
from users.models import Notification

User = get_user_model()

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class NotificationEmailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='subscriber',
            password='password',
            email='subscriber@example.com'
        )
        self.anime = Anime.objects.create(title='Test Anime')
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.subscription = Subscription.objects.create(user=self.user, anime=self.anime)

    @patch('content.tasks.send_mass_mail')
    def test_email_sent_on_new_episode(self, mock_send_mail):
        # Create a new episode
        episode = Episode.objects.create(season=self.season, number=1, title='Pilot')

        # Since CELERY_TASK_ALWAYS_EAGER is True, the task should run synchronously

        # Verify email was sent
        self.assertTrue(mock_send_mail.called)

        # Check arguments
        # send_mass_mail call args: (datatuple, fail_silently=False)
        # datatuple is a list of tuples: (subject, message, from_email, recipient_list)
        args, kwargs = mock_send_mail.call_args
        datatuple = args[0]

        self.assertEqual(len(datatuple), 1)
        subject, message, from_email, recipients = datatuple[0]

        self.assertIn(self.anime.title, subject)
        self.assertIn("Pilot", subject)
        self.assertIn("Watch now:", message)
        self.assertEqual(recipients, ['subscriber@example.com'])

    @patch('content.tasks.send_mass_mail')
    def test_no_email_if_no_email_address(self, mock_send_mail):
        # Create user without email
        user2 = User.objects.create_user(username='noemail', password='password')
        Subscription.objects.create(user=user2, anime=self.anime)

        # Create episode
        Episode.objects.create(season=self.season, number=2, title='Second')

        # Should only send to self.user (who has email)
        args, kwargs = mock_send_mail.call_args
        datatuple = args[0]
        self.assertEqual(len(datatuple), 1)
        self.assertEqual(datatuple[0][3], ['subscriber@example.com'])
