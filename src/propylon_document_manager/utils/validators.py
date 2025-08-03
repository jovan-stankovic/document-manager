import os

from django.core.exceptions import ValidationError

from propylon_document_manager.utils.allowed_extensions import ALLOWED_EXTENSIONS


def validate_file_extension(value):
    """Validate file extension. Raise ValidationError if the extension is not allowed."""

    _, extension = os.path.splitext(value.name)
    extension = extension.lstrip(".").lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f'Unsupported file extension: {extension}. Allowed extensions are: {", ".join(ALLOWED_EXTENSIONS)}.'
        )
