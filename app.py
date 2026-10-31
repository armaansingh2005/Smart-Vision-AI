import json
import logging
import time
import uuid
from collections import Counter
from pathlib import Path

import cv2
from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config
from detection.detector import ObjectDetector
from detection.image_processing import decode_image
from detection.model_loader import ModelUnavailableError, load_model
from detection.visualization import draw_detections
from utils.helpers import cleanup_old_artifacts, get_image_extension, is_allowed_extension, is_valid_result_id


_AUTO_DETECTOR = object()


def create_app(config_overrides=None, detector=_AUTO_DETECTOR):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)
    app.config["UPLOAD_DIR"] = Path(app.config["UPLOAD_DIR"])
    app.config["RESULTS_DIR"] = Path(app.config["RESULTS_DIR"])
    app.config["UPLOAD_DIR"].mkdir(parents=True, exist_ok=True)
    app.config["RESULTS_DIR"].mkdir(parents=True, exist_ok=True)

    if detector is _AUTO_DETECTOR:
        try:
            detector = ObjectDetector(
                load_model(app.config["YOLO_MODEL"], app.config["MODEL_DIR"])
            )
        except ModelUnavailableError as exc:
            app.logger.error("Object detection model is unavailable: %s", exc)
    if detector is _AUTO_DETECTOR:
        detector = None
    app.extensions["smartvision_detector"] = detector

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            confidence_default=app.config["CONFIDENCE_THRESHOLD"],
            model_ready=app.extensions["smartvision_detector"] is not None,
        )

    @app.post("/detect")
    def detect():
        uploaded = request.files.get("image")
        if uploaded is None or not uploaded.filename:
            return render_template("error.html", message="Choose an image before starting detection.", status_code=400), 400
        if not is_allowed_extension(uploaded.filename):
            return render_template("error.html", message="Use a JPG, JPEG, PNG, or WEBP image.", status_code=400), 400

        detector_instance = app.extensions["smartvision_detector"]
        if detector_instance is None:
            return render_template(
                "error.html",
                message="The detection model is not available. Check the setup instructions and model download connection, then restart the app.",
                status_code=503,
            ), 503

        image_bytes = uploaded.stream.read(app.config["MAX_CONTENT_LENGTH"] + 1)
        if not image_bytes:
            return render_template("error.html", message="The uploaded file is empty.", status_code=400), 400
        if len(image_bytes) > app.config["MAX_CONTENT_LENGTH"]:
            return render_template("error.html", message="The image exceeds the 12 MB upload limit.", status_code=413), 413

        try:
            image, source_format = decode_image(
                image_bytes,
                max_pixels=app.config["MAX_IMAGE_PIXELS"],
                max_side=app.config["MAX_IMAGE_SIDE"],
            )
        except ValueError as exc:
            return render_template("error.html", message=str(exc), status_code=400), 400

        try:
            threshold = float(request.form.get("confidence", app.config["CONFIDENCE_THRESHOLD"]))
        except (TypeError, ValueError):
            return render_template("error.html", message="Confidence must be a number between 0.10 and 0.90.", status_code=400), 400
        if threshold > 0.90:
            threshold /= 100
        if not 0.10 <= threshold <= 0.90:
            return render_template("error.html", message="Confidence must be between 0.10 and 0.90.", status_code=400), 400

        result_id = uuid.uuid4().hex
        cleanup_old_artifacts(
            app.config["UPLOAD_DIR"],
            app.config["RESULTS_DIR"],
            app.config["ARTIFACT_RETENTION_HOURS"],
            logger=app.logger,
        )
        upload_name = f"{result_id}.{get_image_extension(source_format)}"
        processed_name = f"{result_id}_detected.png"
        upload_path = app.config["UPLOAD_DIR"] / upload_name
        processed_path = app.config["RESULTS_DIR"] / processed_name
        summary_path = app.config["RESULTS_DIR"] / f"{result_id}.json"

        try:
            upload_path.write_bytes(image_bytes)
            detections, inference_seconds = detector_instance.detect(image, threshold)
            annotated = draw_detections(image, detections)
            if not cv2.imwrite(str(processed_path), annotated):
                raise OSError("OpenCV could not save the processed image.")

            counts = Counter(item["label"] for item in detections)
            result = {
                "id": result_id,
                "original_image": upload_name,
                "processed_image": processed_name,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "confidence_threshold": threshold,
                "inference_seconds": round(inference_seconds, 4),
                "total_objects": len(detections),
                "categories": [
                    {"name": label, "count": count}
                    for label, count in sorted(counts.items(), key=lambda entry: (-entry[1], entry[0]))
                ],
                "detections": detections,
            }
            summary_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        except Exception:
            app.logger.exception("Detection failed for request %s", result_id)
            upload_path.unlink(missing_ok=True)
            processed_path.unlink(missing_ok=True)
            summary_path.unlink(missing_ok=True)
            return render_template(
                "error.html",
                message="Image analysis failed. The server logged the issue; please try another image.",
                status_code=500,
            ), 500

        session["latest_result_id"] = result_id
        return redirect(url_for("results", result_id=result_id))

    @app.get("/results")
    @app.get("/results/<result_id>")
    def results(result_id=None):
        selected_id = result_id or session.get("latest_result_id")
        if not selected_id:
            return redirect(url_for("index"))
        result = read_result(app.config["RESULTS_DIR"], selected_id)
        if result is None:
            abort(404)
        return render_template("results.html", result=result)

    @app.get("/download/<result_id>/<kind>")
    def download(result_id, kind):
        if not is_valid_result_id(result_id):
            abort(404)
        if kind == "image":
            filename = f"{result_id}_detected.png"
            directory = app.config["RESULTS_DIR"]
        elif kind == "json":
            filename = f"{result_id}.json"
            directory = app.config["RESULTS_DIR"]
        else:
            abort(404)
        if not (directory / filename).is_file():
            abort(404)
        return send_from_directory(directory, filename, as_attachment=True)

    @app.get("/health")
    def health():
        ready = app.extensions["smartvision_detector"] is not None
        return jsonify({"status": "ok" if ready else "degraded", "model": "ready" if ready else "unavailable"}), 200 if ready else 503

    @app.errorhandler(RequestEntityTooLarge)
    def file_too_large(_error):
        return render_template("error.html", message="The image exceeds the 12 MB upload limit.", status_code=413), 413

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", message="That result could not be found. It may have expired or the link may be incorrect.", status_code=404), 404

    return app


def read_result(results_dir, result_id):
    if not is_valid_result_id(result_id):
        return None
    result_path = results_dir / f"{result_id}.json"
    if not result_path.is_file():
        return None
    try:
        return json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logging.getLogger(__name__).exception("Could not read detection result %s", result_id)
        return None


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
