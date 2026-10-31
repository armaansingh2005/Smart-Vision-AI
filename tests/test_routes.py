import io

import pytest
from PIL import Image

from app import create_app


class TestDetector:
    def detect(self, image, confidence):
        return [], 0.001


@pytest.fixture
def client(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "UPLOAD_DIR": tmp_path / "uploads",
            "RESULTS_DIR": tmp_path / "results",
        },
        detector=TestDetector(),
    )
    return app.test_client()


def test_dashboard_and_health(client):
    assert client.get("/").status_code == 200
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json == {"status": "ok", "model": "ready"}


def test_detect_rejects_unsupported_extension(client):
    response = client.post(
        "/detect",
        data={"image": (io.BytesIO(b"arbitrary"), "payload.gif")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


def test_health_reports_missing_model(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "UPLOAD_DIR": tmp_path / "uploads",
            "RESULTS_DIR": tmp_path / "results",
        },
        detector=None,
    )
    response = app.test_client().get("/health")
    assert response.status_code == 503
    assert response.json["model"] == "unavailable"


def test_valid_upload_creates_result_and_downloads(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "UPLOAD_DIR": tmp_path / "uploads",
            "RESULTS_DIR": tmp_path / "results",
        },
        detector=TestDetector(),
    )
    image = io.BytesIO()
    Image.new("RGB", (24, 16), color="white").save(image, format="PNG")
    image.seek(0)
    client = app.test_client()

    response = client.post(
        "/detect",
        data={"image": (image, "sample.png"), "confidence": "35"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    result_response = client.get(response.location)
    assert result_response.status_code == 200
    result_id = response.location.rsplit("/", 1)[-1]
    assert client.get(f"/download/{result_id}/image").status_code == 200
    report = client.get(f"/download/{result_id}/json")
    assert report.status_code == 200
    assert report.json["total_objects"] == 0
