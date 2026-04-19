import mimetypes

import magic
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_mime_type(file):
    valid_mime_types = [
        'video/mp4',
        'video/x-matroska',
        'video/webm',
        'video/x-msvideo',
        'application/x-subrip',
        'text/plain',
        'text/vtt',
        'text/srt',
        'image/jpeg',
        'image/png',
        'image/webp',
    ]

    file_mime_type = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)

    if file_mime_type not in valid_mime_types:
        raise ValidationError(
            _('Unsupported file type: %(mime_type)s'),
            params={'mime_type': file_mime_type},
        )


def validate_image_mimetype(file):
    allowed_mimetypes = [
        'image/jpeg',
        'image/png',
        'image/webp',
        'image/gif',
    ]

    mime_type = getattr(file, 'content_type', None)

    if not mime_type:
        mime_type, _ = mimetypes.guess_type(file.name)

    if not mime_type or mime_type not in allowed_mimetypes:
        raise ValidationError(
            f"Unsupported file type: {mime_type}. Allowed MIME types are {', '.join(allowed_mimetypes)}"
        )


def validate_subtitle_mimetype(file):
    allowed_mimetypes = [
        'text/plain',
        'text/vtt',
        'application/x-subrip',
        'application/octet-stream',
    ]

    mime_type, _ = mimetypes.guess_type(file.name)

    if not mime_type:
        ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
        if ext in ['srt', 'vtt', 'ass']:
            return
        raise ValidationError('Unsupported file type.')

    if mime_type not in allowed_mimetypes:
        ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
        if ext in ['srt', 'vtt', 'ass']:
            return
        raise ValidationError(
            f'Unsupported file type: {mime_type}. Allowed extensions are .srt, .vtt, .ass'
        )
