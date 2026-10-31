import os
import secrets
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("SMARTVISION_SECRET_KEY", secrets.token_hex(32))
    MAX_CONTENT_LENGTH = 12 * 1024 * 1024
    MAX_IMAGE_PIXELS = 20_000_000
    MAX_IMAGE_SIDE = 2048
    CONFIDENCE_THRESHOLD = 0.35
    ARTIFACT_RETENTION_HOURS = 168
    YOLO_MODEL = os.environ.get("SMARTVISION_MODEL", "yolov8n.pt")
    UPLOAD_DIR = BASE_DIR / "static" / "uploads"
    RESULTS_DIR = BASE_DIR / "static" / "results"
    MODEL_DIR = BASE_DIR / "models" / "detection_model"
