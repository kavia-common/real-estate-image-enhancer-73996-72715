import os
import re
import uuid
from typing import Tuple
from ..settings import settings

SAFE_CHARS_RE = re.compile(r"[^A-Za-z0-9._-]")


def safe_filename(original: str) -> str:
    name = os.path.basename(original)
    name = SAFE_CHARS_RE.sub("_", name)
    return name[:100]


def generate_upload_path(filename: str) -> Tuple[str, str]:
    """Return (abs_path, rel_path) for upload storage."""
    safe = safe_filename(filename)
    unique = f"{uuid.uuid4()}_{safe}"
    rel = os.path.join(settings.UPLOAD_DIR, unique)
    abs_path = rel  # already relative path under project; FastAPI runs from root
    return abs_path, rel


def generate_result_path(basename_hint: str) -> Tuple[str, str]:
    """Return (abs_path, rel_path) for result file."""
    safe = safe_filename(basename_hint)
    unique = f"{uuid.uuid4()}_{safe}"
    rel = os.path.join(settings.RESULTS_DIR, unique)
    abs_path = rel
    return abs_path, rel
