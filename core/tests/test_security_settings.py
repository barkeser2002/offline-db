from django.test import SimpleTestCase
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import os

class SecuritySettingsTests(SimpleTestCase):
    def test_default_auto_field_is_configured(self):
        """
        Verify that DEFAULT_AUTO_FIELD is set to BigAutoField to prevent warnings and future-proof the DB.
        """
        self.assertEqual(settings.DEFAULT_AUTO_FIELD, 'django.db.models.BigAutoField')

    def test_secret_key_presence(self):
        """
        Verify SECRET_KEY is set.
        """
        self.assertTrue(hasattr(settings, 'SECRET_KEY'))
        self.assertTrue(len(settings.SECRET_KEY) > 0)

    def test_cors_allow_all_origins_default(self):
        """
        Verify CORS_ALLOW_ALL_ORIGINS defaults to False (safe).
        """
        # Safely check for the attribute, defaulting to False if missing (though it should be in settings.py now)
        cors_allowed = getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)

        # We need to simulate the absence of the env var if it's not set
        if 'CORS_ALLOW_ALL_ORIGINS' not in os.environ:
             self.assertFalse(cors_allowed)

    def test_secure_referrer_policy(self):
        """
        Verify SECURE_REFERRER_POLICY is set to 'same-origin' to prevent referer leakage.
        """
        self.assertEqual(getattr(settings, 'SECURE_REFERRER_POLICY', None), 'same-origin')
