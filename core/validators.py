import mimetypes
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

# Regex validator for Magnet and HTTPS URLs
magnet_or_https_validator = RegexValidator(
    regex=r'^(https://|magnet:\?)',
    message="URL must start with magnet: or https://"
)

def validate_subtitle_mimetype(file):
    """
    Validates that the uploaded subtitle file has an allowed MIME type.
    """
    allowed_mimetypes = [
        'text/plain',
        'text/vtt',
        'application/x-subrip',
        'application/octet-stream' # sometimes .srt is identified as octet-stream
    ]

    # Check mime type based on file name extension as a fallback/primary method
    mime_type, _ = mimetypes.guess_type(file.name)

    if not mime_type:
        # If mimetypes module can't guess, we might want to check the extension manually
        ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
        if ext in ['srt', 'vtt', 'ass']:
            return # valid by extension
        raise ValidationError("Unsupported file type.")

    if mime_type not in allowed_mimetypes:
        # double check extension since some systems have weird MIME setups
        ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
        if ext in ['srt', 'vtt', 'ass']:
            return # valid by extension
        raise ValidationError(f"Unsupported file type: {mime_type}. Allowed extensions are .srt, .vtt, .ass")

def validate_image_mimetype(value):
    """
    Validates that the provided value (URL string or File object) points to an image
    with an allowed MIME type based on the file extension.
    """
    if not value:
        return

    import urllib.parse

    # Handle FileField/ImageField objects which have a .name attribute
    # or URL string objects
    name = getattr(value, 'name', str(value))

    # Extract path from URL to strip query parameters if it's a URL
    path = urllib.parse.urlparse(name).path

    allowed_mimetypes = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'image/svg+xml'
    ]

    mime_type, _ = mimetypes.guess_type(path)

    if not mime_type:
        ext = path.split('.')[-1].lower() if '.' in path else ''
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']:
            return
        raise ValidationError("Unsupported image format.")

    if mime_type not in allowed_mimetypes:
        ext = path.split('.')[-1].lower() if '.' in path else ''
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']:
            return
        raise ValidationError(f"Unsupported image format: {mime_type}. Allowed formats are JPEG, PNG, GIF, WebP, SVG.")
