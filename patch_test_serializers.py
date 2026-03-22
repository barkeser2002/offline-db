from django.test import TestCase
from content.serializers import ExternalSourceSerializer, SubtitleSerializer, ImageUploadSerializer
from django.core.files.uploadedfile import SimpleUploadedFile
import magic

class SerializerValidationTests(TestCase):
    def test_external_source_url(self):
        # valid magnet
        serializer = ExternalSourceSerializer(data={'source_name': 'test', 'url': 'magnet:?xt=test', 'type': 'test'})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # invalid url
        serializer = ExternalSourceSerializer(data={'source_name': 'test', 'url': 'javascript:alert(1)', 'type': 'test'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('url', serializer.errors)

    def test_subtitle_file_validation(self):
        valid_file = SimpleUploadedFile("test.srt", b"1\n00:00:01,000 --> 00:00:02,000\nHello", content_type="text/plain")
        serializer = SubtitleSerializer(data={'file': valid_file, 'lang': 'en'})
        serializer.is_valid()
        self.assertNotIn('file', serializer.errors)

        invalid_file = SimpleUploadedFile("test.exe", b"MZ\x00\x00\x00", content_type="application/x-msdownload")
        serializer = SubtitleSerializer(data={'file': invalid_file, 'lang': 'en'})
        serializer.is_valid()
        self.assertIn('file', serializer.errors)
        self.assertTrue(
            "Unsupported file type" in serializer.errors['file'][0] or
            "File extension must be vtt, srt, or ass" in serializer.errors['file'][0]
        )
