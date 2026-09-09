"""
services/image_service.py

Handles validated, safe persistence of user-uploaded item photos.
"""

from __future__ import annotations

import os
from typing import Any

from utils.security import sanitize_filename
from utils.validation import validate_image


def save_image(uploaded_file: Any, type_folder: str = "lost") -> str:
    """Validate and save an uploaded image, returning its on-disk path.

    Raises ValueError (propagated from `validate_image`) if the file fails
    size, extension, or format checks - callers should catch this and show
    a friendly message rather than letting it crash the report flow.
    """
    validate_image(uploaded_file)
    os.makedirs(f"data/{type_folder}", exist_ok=True)
    fname = sanitize_filename(uploaded_file.name)
    path = f"data/{type_folder}/{fname}"
    with open(path, "wb") as fh:
        fh.write(uploaded_file.getbuffer())
    return path
