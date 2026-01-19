from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import Wallet

User = get_user_model()

class UserTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(username='testuser', password='password123')
        self.assertEqual(user.username, 'testuser')
        self.assertFalse(user.is_premium)
        self.assertTrue(user.check_password('password123'))

    def test_wallet_creation(self):
        user = User.objects.create_user(username='walletuser', password='password123')
        wallet = Wallet.objects.create(user=user, balance=100.00)
        self.assertEqual(wallet.user, user)
        self.assertEqual(wallet.balance, 100.00)
        self.assertEqual(str(wallet), "walletuser's Wallet: 100.00")
