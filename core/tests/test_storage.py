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

    def test_delete_path_traversal(self):
        malicious_path = "../malicious_file.txt"
        result = self.storage.delete(malicious_path)
        self.assertFalse(result)

    def test_exists_path_traversal(self):
        malicious_path = "../malicious_file.txt"
        result = self.storage.exists(malicious_path)
        self.assertFalse(result)

    def test_delete_file(self):
        safe_path = "videos/delete_me.txt"
        full_path = os.path.join(self.storage.base_path, safe_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write("test content")

        self.assertTrue(self.storage.exists(safe_path))

        result = self.storage.delete(safe_path)
        self.assertTrue(result)
        self.assertFalse(self.storage.exists(safe_path))
        self.assertFalse(os.path.exists(full_path))

    def test_delete_non_existent_file(self):
        safe_path = "videos/does_not_exist.txt"
        result = self.storage.delete(safe_path)
        self.assertFalse(result)

    def test_exists_file(self):
        safe_path = "videos/exists_file.txt"
        full_path = os.path.join(self.storage.base_path, safe_path)

        self.assertFalse(self.storage.exists(safe_path))

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write("test content")

        self.assertTrue(self.storage.exists(safe_path))
