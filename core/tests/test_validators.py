from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from core.validators import validate_mime_type, validate_mime_type

class ValidatorTests(TestCase):

    def test_validate_mime_type_valid(self):
        # Create a valid image file mock
        valid_files = [
            SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg"),
            SimpleUploadedFile("test.png", b"file_content", content_type="image/png"),
            SimpleUploadedFile("test.webp", b"file_content", content_type="image/webp"),
            SimpleUploadedFile("test.gif", b"file_content", content_type="image/gif"),
        ]

        for valid_file in valid_files:
            try:
                validate_mime_type(valid_file)
            except ValidationError:
                self.fail(f"validate_mime_type raised ValidationError unexpectedly for {valid_file.name}!")

    def test_validate_mime_type_invalid_extension(self):
        # Create an invalid file mock (e.g. .txt)
        invalid_file = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")

        with self.assertRaises(ValidationError):
            validate_mime_type(invalid_file)

    def test_validate_mime_type_mismatch(self):
        # Create a file mock where the extension is not an image but content_type is fake
        # In reality mimetypes.guess_type relies on the filename mostly
        invalid_file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")

        with self.assertRaises(ValidationError):
            validate_mime_type(invalid_file)
