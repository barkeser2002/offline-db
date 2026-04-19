from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from core.validators import validate_image_mimetype, validate_subtitle_mimetype

class ValidatorTests(TestCase):

    def test_validate_image_mimetype_valid(self):
        # Create a valid image file mock with actual image signatures
        valid_files = [
            SimpleUploadedFile("test.jpg", b"\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xFF\xDB\x00\x43\x00", content_type="image/jpeg"),
            SimpleUploadedFile("test.png", b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A\x00\x00\x00\x0D\x49\x48\x44\x52\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1F\x15\xC4\x89\x00\x00\x00\x0B\x49\x44\x41\x54\x08\xD7\x63\x60\x00\x02\x00\x00\x05\x00\x01\x0D\x0A\x2D\xB4\x00\x00\x00\x00\x49\x45\x4E\x44\xAE\x42\x60\x82", content_type="image/png"),
            SimpleUploadedFile("test.webp", b"RIFF\x14\x00\x00\x00WEBPVP8 \x08\x00\x00\x00\x90\x00\x00\x00\x00\x00\x00\x00", content_type="image/webp"),
            SimpleUploadedFile("test.gif", b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B", content_type="image/gif"),
        ]

        for valid_file in valid_files:
            try:
                validate_image_mimetype(valid_file)
            except ValidationError:
                self.fail(f"validate_image_mimetype raised ValidationError unexpectedly for {valid_file.name}!")

    def test_validate_image_mimetype_invalid_extension(self):
        # Create an invalid file mock (e.g. .txt)
        invalid_file = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")

        with self.assertRaises(ValidationError):
            validate_image_mimetype(invalid_file)

    def test_validate_image_mimetype_mismatch(self):
        # Create a file mock where the extension is not an image but content_type is fake
        # In reality mimetypes.guess_type relies on the filename mostly
        invalid_file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")

        with self.assertRaises(ValidationError):
            validate_image_mimetype(invalid_file)
