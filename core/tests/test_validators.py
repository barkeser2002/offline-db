import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from core.validators import validate_image_mimetype, validate_video_mimetype

def test_validate_image_mimetype():
    # Valid types
    valid_file = SimpleUploadedFile("test.png", b"file_content")
    validate_image_mimetype(valid_file)  # Should not raise

    valid_file2 = SimpleUploadedFile("test.jpg", b"file_content")
    validate_image_mimetype(valid_file2)  # Should not raise

    # Invalid extension
    invalid_file = SimpleUploadedFile("test.txt", b"file_content")
    with pytest.raises(ValidationError):
        validate_image_mimetype(invalid_file)

    # Invalid extension but valid mimetype is mocked by python depending on os,
    # but the guess_type relies on the filename strictly in most default setups.

def test_validate_video_mimetype():
    # Valid types
    valid_file = SimpleUploadedFile("test.mp4", b"file_content")
    validate_video_mimetype(valid_file)  # Should not raise

    valid_file2 = SimpleUploadedFile("test.mkv", b"file_content")
    validate_video_mimetype(valid_file2)  # Should not raise

    # Invalid type
    invalid_file = SimpleUploadedFile("test.txt", b"file_content")
    with pytest.raises(ValidationError):
        validate_video_mimetype(invalid_file)
