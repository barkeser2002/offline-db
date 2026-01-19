from django.test import TestCase, Client, override_settings
from django.urls import reverse
from .models import ShopierPayment
from users.models import User
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

    @override_settings(SHOPIER_SECRET='test_secret_key', DEBUG=False)
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

    @override_settings(SHOPIER_SECRET='test_secret_key', DEBUG=False)
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

    @override_settings(SHOPIER_SECRET='test_secret_key', DEBUG=False)
    def test_callback_invalid_signature(self):
        data = {
            'platform_order_id': 'ORD-12345',
            'status': 'success',
            'signature': 'invalid_signature'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Invalid signature")

    @override_settings(SHOPIER_SECRET='test_secret_key', DEBUG=False)
    def test_callback_missing_signature(self):
        data = {
            'platform_order_id': 'ORD-12345',
            'status': 'success',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Invalid signature")

    @override_settings(SHOPIER_SECRET=None, DEBUG=True)
    def test_callback_no_secret_debug_mode(self):
        # Should pass verification in DEBUG mode if secret is missing
        data = {
            'platform_order_id': 'ORD-12345',
            'status': 'success',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)

    @override_settings(SHOPIER_SECRET=None, DEBUG=False)
    def test_callback_no_secret_production_mode(self):
        # Should fail verification in Production mode if secret is missing
        data = {
            'platform_order_id': 'ORD-12345',
            'status': 'success',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
