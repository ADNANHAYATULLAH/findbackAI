"""
utils/validation.py

Upload validation: size limits, extension allowlist, and a real image
decode+format check so a renamed non-image file can't slip through just
because it has a `.jpg` extension.
"""

from __future__ import annotations

from typing import Any

from PIL import Image

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB

_PIL_FORMAT_FOR_EXT = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
}


def validate_image(file: Any) -> None:
    """Validate a Streamlit UploadedFile as a safe, correctly-typed image.

    Raises ValueError with a user-facing message on any failure. Leaves the
    file pointer reset to 0 so the caller can still read it afterwards.
    """
    if file.size > MAX_SIZE:
        raise ValueError("File too large - max 5MB")

    ext = "." + file.name.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        raise ValueError("Unsupported format - use JPG, PNG, or WEBP")

    try:
        img = Image.open(file)
        img.verify()  # cheap structural check; re-open needed to read .format after this
        file.seek(0)
        img = Image.open(file)
        actual_format = img.format
        if img.size[0] * img.size[1] > 4000 * 4000:
            raise ValueError("Image dimensions too large")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Invalid or corrupted image: {exc}")
    finally:
        file.seek(0)

    expected_format = _PIL_FORMAT_FOR_EXT.get(ext)
    if expected_format and actual_format != expected_format:
        raise ValueError(
            f"File extension ({ext}) doesn't match actual image type ({actual_format})"
        )
