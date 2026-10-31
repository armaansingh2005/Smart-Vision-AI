import logging
import threading
from pathlib import Path


class ModelUnavailableError(RuntimeError):
    """Raised when the configured pretrained detector cannot be initialized."""


_model = None
_model_key = None
_model_lock = threading.Lock()


def load_model(weights="yolov8n.pt", model_dir=None):
    global _model, _model_key
    model_path = Path(model_dir) / weights if model_dir and not Path(weights).is_absolute() else Path(weights)
    model_key = str(model_path.resolve()) if model_path.exists() else str(weights)
    with _model_lock:
        if _model is not None and _model_key == model_key:
            return _model
        try:
            from ultralytics import YOLO

            logging.getLogger(__name__).info("Loading pretrained COCO model: %s", weights)
            model = YOLO(str(model_path))
        except Exception as exc:
            raise ModelUnavailableError(
                f"Could not load {weights}. Ensure ultralytics is installed and the official model weights can be downloaded: {exc}"
            ) from exc
        _model = model
        _model_key = model_key
        return _model
