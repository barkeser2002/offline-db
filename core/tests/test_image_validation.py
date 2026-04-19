from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from core.validators import validate_image_mimetype

class ImageValidationTest(TestCase):
    def test_valid_image(self):
        file = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        validate_image_mimetype(file)  # Should not raise

    def test_invalid_image(self):
        file = SimpleUploadedFile("test.exe", b"file_content", content_type="application/x-msdownload")
        with self.assertRaises(ValidationError):
            validate_image_mimetype(file)

    def test_invalid_image_valid_extension(self):
        # A file with an allowed extension but invalid content type
        file = SimpleUploadedFile("test.jpg", b"file_content", content_type="application/x-msdownload")
        with self.assertRaises(ValidationError):
            validate_image_mimetype(file)
