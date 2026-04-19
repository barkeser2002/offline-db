import magic
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_mime_type(file):
    valid_mime_types = [
        'video/mp4', 'video/x-matroska', 'video/webm', 'video/x-msvideo',
        'application/x-subrip', 'text/plain', 'text/vtt', 'text/srt',
        'image/jpeg', 'image/png', 'image/webp'
    ]

    file_mime_type = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)

    if file_mime_type not in valid_mime_types:
        raise ValidationError(
            _('Unsupported file type: %(mime_type)s'),
            params={'mime_type': file_mime_type},
        )

def validate_image_mimetype(file):
    valid_mime_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    file_mime_type = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    if file_mime_type not in valid_mime_types:
        raise ValidationError(
            _('Unsupported file type: %(mime_type)s'),
            params={'mime_type': file_mime_type},
        )

def validate_subtitle_mimetype(file):
    valid_mime_types = ['application/x-subrip', 'text/plain', 'text/vtt', 'text/srt']
    file_mime_type = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    if file_mime_type not in valid_mime_types:
        raise ValidationError(
            _('Unsupported file type: %(mime_type)s'),
            params={'mime_type': file_mime_type},
        )
