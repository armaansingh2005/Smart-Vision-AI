# SmartVision AI

An image-analysis web application that uses a **pretrained YOLOv8n model trained on COCO** to detect multiple object instances in one image. Each detection includes a class label, bounding box, and model confidence. The app creates an annotated image and a downloadable JSON report.

> This application runs real pretrained-model inference. It does not substitute sample labels or generated confidence values when model loading or inference fails.

## Project overview

SmartVision provides a small, modular computer-vision service and an accessible browser UI for inspecting its results. A user uploads an image, chooses a confidence threshold, and receives per-instance results, category counts, inference timing, and downloadable artifacts.

### Problem statement and objectives

Single-label image classification cannot tell users where several objects are or distinguish multiple instances of the same class. SmartVision addresses that limitation by:

- Detecting multiple objects and same-class instances with COCO-trained YOLO.
- Showing box coordinates, labels, and per-object confidence.
- Summarizing categories, counts, and inference time in a responsive dashboard.
- Validating image uploads and handling model/network failures explicitly.

## Features

- JPG, JPEG, PNG, and WEBP uploads, drag-and-drop, preview, and a 12 MB server-enforced limit.
- Adjustable confidence threshold (10–90%); YOLO performs class-aware non-maximum suppression.
- Aspect-ratio-preserving resize for inference, EXIF orientation correction, OpenCV visualization, and stable class colors.
- Original and annotated image comparison, per-instance confidence, category counts, JSON and annotated PNG downloads.
- Unique result identifiers, safe server-generated filenames, and health status endpoint.
- Generated uploads and reports older than seven days are safely pruned on new analysis requests.

## Technology

- Python 3.10+
- Flask
- Ultralytics YOLOv8n (COCO pretrained weights; PyTorch inference runtime)
- OpenCV, NumPy, Pillow
- HTML, CSS, and vanilla JavaScript
- pytest

YOLO is the selected multi-object detection option. It is not a TensorFlow/Keras model; Ultralytics uses PyTorch for this model. The project keeps TensorFlow out of the runtime because it is not needed for this supported YOLO option.

## Architecture

```text
Browser (templates + CSS + JavaScript)
       │ multipart upload / result pages / downloads
       ▼
Flask app.py ── config.py
       │
       ├── detection/model_loader.py    Load pretrained model once per process
       ├── detection/image_processing.py Validate, orient, convert, resize input
       ├── detection/detector.py        Inference, threshold, NMS, detections
       ├── detection/visualization.py   Draw class-colored boxes and labels
       └── utils/helpers.py             Upload extension and result-ID checks
       │
       ├── static/uploads/              Validated original images
       └── static/results/              Annotated PNGs and JSON reports
```

### Module guide

| Path | Responsibility |
|---|---|
| `app.py` | Flask app factory, routes, upload validation, result persistence, and health status |
| `config.py` | Upload/model directories, limits, threshold, and environment-based settings |
| `detection/model_loader.py` | Thread-safe, process-wide YOLO initialization and actionable model-load errors |
| `detection/image_processing.py` | Pillow validation/EXIF correction and OpenCV conversion/resizing |
| `detection/detector.py` | YOLO inference and per-instance result serialization |
| `detection/visualization.py` | Class-specific colors and annotated bounding boxes |
| `utils/helpers.py` | Extension mapping and safe result identifier validation |
| `templates/` | Upload dashboard, results dashboard, and user-facing errors |
| `static/css/style.css` | Responsive visual system and dashboard layouts |
| `static/js/script.js` | Drag/drop, preview, validation, threshold display, and submit state |
| `tests/` | Detector, image, visualization, and Flask route tests |

## Setup

Open PowerShell in this project folder.

### 1. Create and activate an environment (recommended)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Python 3.10–3.12 is recommended for the published dependency stack. On Windows, if activation is restricted, run the interpreter directly as `.venv\Scripts\python.exe`.

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

Ultralytics installs its PyTorch runtime. On first startup, it downloads the official COCO `yolov8n.pt` weights from the [Ultralytics assets release](https://github.com/ultralytics/assets/releases/tag/v8.3.0) into `models/detection_model/`. Internet access is needed for this first download; inference then runs locally.

To download the weights manually in PowerShell instead:

```powershell
New-Item -ItemType Directory -Force .\models\detection_model
Invoke-WebRequest `
  -Uri "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt" `
  -OutFile ".\models\detection_model\yolov8n.pt"
```

To use a previously downloaded compatible weight file:

```powershell
$env:SMARTVISION_MODEL = "C:\path\to\yolov8n.pt"
```

To set a stable Flask session secret:

```powershell
$env:SMARTVISION_SECRET_KEY = "replace-with-a-long-random-secret"
```

If dependency installation or model download is unavailable, the dashboard and `/health` endpoint report the detector as unavailable. Detection requests return a clear service error; the application never fabricates results.

## Run

```powershell
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). To check readiness, open [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health). The first startup may take longer while weights are downloaded.

## Routes

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Upload and analysis dashboard |
| `POST` | `/detect` | Validate upload and run object detection |
| `GET` | `/results` | Most recent result for the browser session |
| `GET` | `/results/<result_id>` | Specific detection report |
| `GET` | `/download/<result_id>/image` | Download annotated PNG |
| `GET` | `/download/<result_id>/json` | Download structured JSON |
| `GET` | `/health` | Model readiness status (`200` ready; `503` unavailable) |

## Test

```powershell
python -m pytest -q
```

Tests cover detector result mapping, multiple instances of one class, image validation, visualization, and Flask routes. To verify actual model predictions, start the app and upload images with varied scenes; test results depend on the pretrained model, image quality, and selected confidence threshold.

## Screenshots

The dashboard is available at `/`. After analyzing an image, the result page shows the original image, annotated detections, and object summary.

## Sample result shape

The included `car.jpg` was analyzed locally with a 25% confidence threshold. That run detected one car at 94.2% confidence with box `[66, 80, 285, 165]`. Inference took 5.82 seconds on the setup used for this check; latency varies by hardware and warm-up state.

```json
{
  "total_objects": 1,
  "categories": [{"name": "car", "count": 1}],
  "inference_seconds": 5.8227,
  "detections": [
    {"class_id": 2, "label": "car", "confidence": 0.942, "box": [66, 80, 285, 165]}
  ]
}
```

This result was produced by the actual pretrained model, not stored as a fixture or hardcoded prediction.

## Security and operational notes

- The backend validates both filename extension and decoded image content. File names on disk are generated UUIDs, never user-provided paths.
- Uploads are capped at 12 MB and 20 megapixels. Inference images are resized to a 2048-pixel maximum side without changing aspect ratio.
- Avoid exposing the development server directly to the public internet. For deployment, use a production WSGI server, HTTPS, and a persistent secret and access controls. Generated uploads and reports are pruned after seven days when a new analysis is submitted.
- Uploads and result files are ignored by Git; model weights are downloaded/cached separately and are not committed.

## Future enhancements

- Add authenticated projects and configurable artifact retention.
- Add batch inference, video streams, and an API response mode.
- Add model selection and optional GPU deployment.
- Add exportable evaluation metrics and a model/version metadata panel.

## Project information

**Project:** SmartVision AI — Intelligent Multi-Object Image Classification and Detection System  
**Purpose:** Internship-representative computer vision and full-stack AI demonstration  
**Author:** Project owner
