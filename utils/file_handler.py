"""
File Handler Utility for Issue Image Attachments.
Saves uploaded files safely to the configured uploads folder.
"""

import uuid
from pathlib import Path
from typing import Optional, Tuple
from config import Config
from utils.validators import validate_file_upload


def save_uploaded_attachment(uploaded_file) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Saves an uploaded Streamlit file to the uploads directory.
    Returns (success, saved_file_path_or_error, file_type).
    """
    if uploaded_file is None:
        return False, "No file provided", None

    file_name = uploaded_file.name
    file_bytes = uploaded_file.getvalue()
    file_size = len(file_bytes)

    # Validate
    valid, err = validate_file_upload(file_name, file_size, Config.MAX_UPLOAD_SIZE_MB)
    if not valid:
        return False, err, None

    # Generate safe random filename
    ext = "." + file_name.split(".")[-1].lower()
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    target_path = Config.UPLOAD_DIR / unique_filename

    try:
        with open(target_path, "wb") as f:
            f.write(file_bytes)
        return True, str(target_path.as_posix()), ext.replace(".", "")
    except Exception as e:
        return False, f"Failed to save file: {str(e)}", None
