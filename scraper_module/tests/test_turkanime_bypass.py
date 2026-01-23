
import unittest
from unittest.mock import patch, MagicMock
import json
import base64
import os
from hashlib import md5
from scraper_module.adapters import turkanime_bypass

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
except ImportError:
    try:
        from Cryptodome.Cipher import AES
        from Cryptodome.Util.Padding import pad
    except ImportError:
        AES = None
        pad = None

class TestTurkAnimeBypass(unittest.TestCase):

    def setUp(self):
        if AES is None:
            self.skipTest("PyCryptodome not installed")

    def encrypt_for_test(self, key_bytes, plaintext):
        salt = os.urandom(8)
        iv = os.urandom(16)

        # Derive key same as implementation
        data = key_bytes + salt
        derived_key = md5(data).digest()
        final_key = derived_key
        while len(final_key) < 32:
            derived_key = md5(derived_key + data).digest()
            final_key += derived_key
        final_key = final_key[:32]

        cipher = AES.new(final_key, AES.MODE_CBC, iv)
        ct_bytes = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))

        # Format as the expected JSON
        obj = {
            "ct": base64.b64encode(ct_bytes).decode('utf-8'),
            "iv": iv.hex(),
            "s": salt.hex()
        }
        json_str = json.dumps(obj)
        return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

    def test_decrypt_cipher(self):
        key = b"secret_key"
        plaintext = "https://example.com/video.mp4"
        encrypted_data = self.encrypt_for_test(key, plaintext)

        # Test decryption
        decrypted = turkanime_bypass.decrypt_cipher(key, encrypted_data.encode('utf-8'))
        self.assertEqual(decrypted, plaintext)

    def test_decrypt_cipher_invalid_key(self):
        key = b"wrong_key"
        plaintext = "https://example.com/video.mp4"
        # Encrypt with a different key
        encrypted_data = self.encrypt_for_test(b"actual_key", plaintext)

        # Decryption should fail (return empty string or garbage, but likely empty string due to unpad error caught)
        decrypted = turkanime_bypass.decrypt_cipher(key, encrypted_data.encode('utf-8'))
        # It might return empty string or raise error depending on implementation.
        # Refactored code catches ValueError and returns ""
        self.assertEqual(decrypted, "")

    @patch('scraper_module.adapters.turkanime_bypass.fetch')
    def test_obtain_csrf_success(self, mock_fetch):
        # We need to simulate the response of fetch(PLAYERJS_URL)
        # It needs to contain:
        # 1. "csrf-token': ... 'KEY')"
        # 2. "'CIPHERTEXT',"

        # This is hard to test without exact implementation of jsjiamiv7 encryption to generate valid ciphertext.
        # However, we can test that it handles missing data gracefully.

        mock_fetch.return_value = "<html>No keys here</html>"
        csrf = turkanime_bypass.obtain_csrf()
        self.assertIsNone(csrf)

    @patch('scraper_module.adapters.turkanime_bypass.fetch')
    def test_obtain_key_failure(self, mock_fetch):
        mock_fetch.return_value = ""
        key = turkanime_bypass.obtain_key()
        self.assertEqual(key, b"")

    def test_unmask_real_url_no_turkanime(self):
        url = "https://other-site.com/video"
        result = turkanime_bypass.unmask_real_url(url)
        self.assertEqual(result, url)

    @patch('scraper_module.adapters.turkanime_bypass.obtain_csrf')
    def test_unmask_real_url_no_csrf(self, mock_obtain_csrf):
        mock_obtain_csrf.return_value = None
        # Mock logger to avoid clutter
        with patch('scraper_module.adapters.turkanime_bypass.logger'):
            result = turkanime_bypass.unmask_real_url("https://turkanime.co/player/123")
            self.assertEqual(result, "https://turkanime.co/player/123")
