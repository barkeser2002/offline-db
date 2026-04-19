from django.test import TestCase
from content.serializers import ExternalSourceSerializer, SubtitleSerializer, ImageUploadSerializer
from django.core.files.uploadedfile import SimpleUploadedFile
import magic

class SerializerValidationTests(TestCase):
    def test_subtitle_file_validation(self):
        # valid file
        valid_file = SimpleUploadedFile("test.srt", b"1\n00:00:01,000 --> 00:00:02,000\nHello", content_type="text/plain")
        serializer = SubtitleSerializer(data={'file': valid_file, 'lang': 'en'})
        serializer.is_valid()
        self.assertNotIn('file', serializer.errors)

        # fake MZ executable but passing extension check
        # We need a real zip or something that magic sees as not text
        with open("/bin/ls", "rb") as f:
            exe_content = f.read()

        invalid_file = SimpleUploadedFile("test.srt", exe_content, content_type="application/x-msdownload")
        serializer = SubtitleSerializer(data={'file': invalid_file, 'lang': 'en'})
        serializer.is_valid()
        self.assertIn('file', serializer.errors)
        self.assertTrue("Unsupported file type" in serializer.errors['file'][0])
