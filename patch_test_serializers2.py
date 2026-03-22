from django.test import TestCase
from content.serializers import ExternalSourceSerializer, SubtitleSerializer, ImageUploadSerializer
from django.core.files.uploadedfile import SimpleUploadedFile
import magic

class SerializerValidationTests(TestCase):
    def test_subtitle_file_validation(self):
        invalid_file = SimpleUploadedFile("test.exe", b"MZ\x00\x00\x00", content_type="application/x-msdownload")
        serializer = SubtitleSerializer(data={'file': invalid_file, 'lang': 'en'})
        serializer.is_valid()
        print(serializer.errors)
