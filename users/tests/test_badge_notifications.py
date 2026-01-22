from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from users.models import Badge, UserBadge, Notification
from users.services import check_badges

User = get_user_model()

class BadgeNotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='badgeuser', password='password')
        self.badge, created = Badge.objects.get_or_create(
            slug='supporter',
            defaults={
                'name': 'Supporter',
                'description': 'Is Premium'
            }
        )

    @patch('users.services.get_channel_layer')
    @patch('users.services.async_to_sync')
    def test_notification_sent_on_badge_award(self, mock_async_to_sync, mock_get_channel_layer):
        # Mock channel layer
        mock_channel_layer = mock_get_channel_layer.return_value

        # Make user premium to trigger 'supporter' badge
        self.user.is_premium = True
        self.user.save()

        # Run check_badges
        check_badges(self.user)

        # 1. Verify DB Notification
        self.assertTrue(Notification.objects.filter(user=self.user).exists())
        notification = Notification.objects.get(user=self.user)
        self.assertEqual(notification.title, "New Badge Earned!")
        self.assertIn("Supporter", notification.message)

        # 2. Verify WebSocket Message
        # async_to_sync(channel_layer.group_send)(group_name, {...})

        # Check if async_to_sync was called with group_send
        mock_async_to_sync.assert_called_with(mock_channel_layer.group_send)

        # Check if the wrapper was called with correct arguments
        wrapper = mock_async_to_sync.return_value
        wrapper.assert_called()
        args, kwargs = wrapper.call_args
        self.assertEqual(args[0], f"user_{self.user.id}")
        self.assertEqual(args[1]['type'], 'notification_message')
        self.assertEqual(args[1]['title'], "New Badge Earned!")

    def test_no_notification_if_badge_already_owned(self):
        # Award badge first
        UserBadge.objects.create(user=self.user, badge=self.badge)

        # Make user premium (condition met)
        self.user.is_premium = True
        self.user.save()

        # Run check_badges
        check_badges(self.user)

        # Should be no new notifications
        self.assertFalse(Notification.objects.exists())
