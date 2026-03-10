import os
import shutil
import tempfile
from django.test import TestCase, override_settings
from core.storage import LocalStorage, StorageError

class LocalStorageSecurityTest(TestCase):
    def setUp(self):
        self.temp_media_root = tempfile.mkdtemp()
        self.storage = LocalStorage()
        self.storage.base_path = os.path.abspath(self.temp_media_root)

    def tearDown(self):
        shutil.rmtree(self.temp_media_root)

    def test_path_traversal_prevention(self):
        # Create a temp file to upload
        fd, temp_file_path = tempfile.mkstemp()
        os.close(fd)
        with open(temp_file_path, 'w') as f:
            f.write("test content")

        # Attempt to upload to a path traversing out of base_path
        malicious_path = "../malicious_file.txt"

        with self.assertRaises(StorageError):
            self.storage.upload(temp_file_path, malicious_path)

        os.remove(temp_file_path)

    def test_valid_upload(self):
        # Create a temp file to upload
        fd, temp_file_path = tempfile.mkstemp()
        os.close(fd)
        with open(temp_file_path, 'w') as f:
            f.write("test content")

        valid_path = "videos/safe_file.txt"

        result_url = self.storage.upload(temp_file_path, valid_path)

        self.assertTrue(self.storage.exists(valid_path))

        expected_full_path = os.path.join(self.storage.base_path, "videos/safe_file.txt")
        self.assertTrue(os.path.exists(expected_full_path))

        os.remove(temp_file_path)
