from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.db.models import Sum
from decimal import Decimal
from .models import ShopierPayment, SubscriptionPlan
from users.models import User, Wallet, WatchLog
from content.models import Episode, VideoFile, FansubGroup, Anime, Season
from .tasks import calculate_revenue
import hmac
import hashlib
import base64
import os

class BillingCallbackTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.payment = ShopierPayment.objects.create(
            user=self.user,
            amount=10.00,
            transaction_id='ORD-12345',
            status='pending'
        )
        self.url = reverse('shopier_callback')
        self.secret = 'test_secret_key'

    def generate_signature(self, transaction_id, status, secret):
        payload = f"{transaction_id}{status}"
        return base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')

    @override_settings(SHOPIER_SECRET='test_secret_key', DEBUG=False, SECURE_SSL_REDIRECT=False)
    def test_callback_success_valid_signature(self):
        signature = self.generate_signature('ORD-12345', 'success', self.secret)
        data = {
            'platform_order_id': 'ORD-12345',
            'status': 'success',
            'signature': signature
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)

        self.payment.refresh_from_db()
        self.user.refresh_from_db()

        self.assertEqual(self.payment.status, 'success')
        self.assertTrue(self.user.is_premium)

    @override_settings(SHOPIER_SECRET='test_secret_key', DEBUG=False, SECURE_SSL_REDIRECT=False)
    def test_callback_failed_valid_signature(self):
        signature = self.generate_signature('ORD-12345', 'failed', self.secret)
        data = {
            'platform_order_id': 'ORD-12345',
            'status': 'failed',
            'signature': signature
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'failed')

    @override_settings(SHOPIER_SECRET='test_secret_key', DEBUG=False, SECURE_SSL_REDIRECT=False)
    def test_callback_invalid_signature(self):
        data = {
            'platform_order_id': 'ORD-12345',
            'status': 'success',
            'signature': 'invalid_signature'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Invalid signature")

    @override_settings(SHOPIER_SECRET='test_secret_key', DEBUG=False, SECURE_SSL_REDIRECT=False)
    def test_callback_missing_signature(self):
        data = {
            'platform_order_id': 'ORD-12345',
            'status': 'success',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Invalid signature")

    @override_settings(SHOPIER_SECRET=None, DEBUG=True, SECURE_SSL_REDIRECT=False)
    def test_callback_no_secret_debug_mode(self):
        # Should fail verification even in DEBUG mode if secret is missing
        data = {
            'platform_order_id': 'ORD-12345',
            'status': 'success',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)

    @override_settings(SHOPIER_SECRET=None, DEBUG=False, SECURE_SSL_REDIRECT=False)
    def test_callback_no_secret_production_mode(self):
        # Should fail verification in Production mode if secret is missing
        data = {
            'platform_order_id': 'ORD-12345',
            'status': 'success',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)


class RevenueCalculationTests(TestCase):
    def setUp(self):
        # Setup data
        self.user = User.objects.create_user(username='testuser_rev', password='password')

        # Fansub Group Owner
        self.fansub_owner = User.objects.create_user(username='fansub_owner', password='password')
        self.group = FansubGroup.objects.create(name='Test Group', owner=self.fansub_owner)

        # Uploader
        self.uploader = User.objects.create_user(username='uploader', password='password')

        # Content
        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1, title="Ep 1")

        # Video Files
        # 1 video by fansub group, 1 video by uploader
        self.v1 = VideoFile.objects.create(
            episode=self.episode,
            fansub_group=self.group,
            quality='1080p',
            hls_path='test.m3u8',
            encryption_key='test'
        )
        self.v2 = VideoFile.objects.create(
            episode=self.episode,
            uploader=self.uploader,
            quality='720p',
            hls_path='test.m3u8',
            encryption_key='test'
        )

        # Revenue
        self.plan = SubscriptionPlan.objects.create(name="Pro", price=100.00)
        self.payment = ShopierPayment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=Decimal('100.00'),
            transaction_id='TEST-REV',
            status='success',
            is_distributed=False
        )

    def test_calculate_revenue(self):
        # Create WatchLog
        # User watched 100 seconds
        WatchLog.objects.create(
            user=self.user,
            episode=self.episode,
            duration=100
        )

        # Expected calculation:
        # Total Revenue: 100.00
        # Encoder Pool: 35.00 (35%)
        # Fansub Pool: 20.00 (20%)

        # Total duration for Episode 1: 100s
        # Number of videos: 2
        # Unit share: 100 / 2 = 50 units per video

        # Fansub Group (v1): 50 units
        # Uploader (v2): 50 units

        # Total Fansub Units: 50
        # Total Encoder Units: 50

        # Fansub Share: (50 / 50) * 20.00 = 20.00
        # Encoder Share: (50 / 50) * 35.00 = 35.00

        result = calculate_revenue()

        # Check wallets
        fansub_wallet = Wallet.objects.get(user=self.fansub_owner)
        self.assertEqual(fansub_wallet.balance, Decimal('20.00'))

        uploader_wallet = Wallet.objects.get(user=self.uploader)
        self.assertEqual(uploader_wallet.balance, Decimal('35.00'))

        # Check payment updated
        self.payment.refresh_from_db()
        self.assertTrue(self.payment.is_distributed)

        self.assertIn("Distributed 100", result)

    def test_multiple_logs_aggregation(self):
        # 2 logs for same episode
        WatchLog.objects.create(user=self.user, episode=self.episode, duration=60)
        WatchLog.objects.create(user=self.user, episode=self.episode, duration=40)

        # Total duration: 100s. Same as above.

        calculate_revenue()

        fansub_wallet = Wallet.objects.get(user=self.fansub_owner)
        self.assertEqual(fansub_wallet.balance, Decimal('20.00'))

        uploader_wallet = Wallet.objects.get(user=self.uploader)
        self.assertEqual(uploader_wallet.balance, Decimal('35.00'))

    def test_no_revenue(self):
        self.payment.is_distributed = True
        self.payment.save()

        result = calculate_revenue()
        self.assertEqual(result, "No revenue to distribute.")
