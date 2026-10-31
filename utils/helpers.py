import logging
import re
import time
import uuid
from pathlib import Path


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
IMAGE_FORMAT_EXTENSIONS = {
    "JPEG": "jpg",
    "PNG": "png",
    "WEBP": "webp",
}
_GENERATED_ARTIFACT = re.compile(r"^[0-9a-f]{32}(?:_detected)?\.(?:jpg|jpeg|png|webp|json)$")


def is_allowed_extension(filename):
    return Path(filename).suffix.lower().lstrip(".") in ALLOWED_EXTENSIONS


def get_image_extension(image_format):
    return IMAGE_FORMAT_EXTENSIONS.get(image_format, "png")


def is_valid_result_id(result_id):
    if not isinstance(result_id, str):
        return False
    try:
        return uuid.UUID(hex=result_id).hex == result_id
    except ValueError:
        return False


def cleanup_old_artifacts(upload_dir, results_dir, retention_hours, logger=None):
    log = logger or logging.getLogger(__name__)
    cutoff = time.time() - retention_hours * 60 * 60
    for directory in (Path(upload_dir), Path(results_dir)):
        try:
            for path in directory.iterdir():
                if not _GENERATED_ARTIFACT.fullmatch(path.name) or not path.is_file():
                    continue
                if path.stat().st_mtime < cutoff:
                    path.unlink()
        except OSError:
            log.warning("Could not inspect SmartVision artifact directory: %s", directory, exc_info=True)
