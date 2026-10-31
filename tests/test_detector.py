import numpy as np

from detection.detector import ObjectDetector
from detection.image_processing import decode_image
from detection.visualization import draw_detections


class ArrayValues:
    def __init__(self, values):
        self.values = np.asarray(values)

    def cpu(self):
        return self

    def numpy(self):
        return self.values


class FakeBoxes:
    xyxy = ArrayValues([[1.2, 2.4, 9.6, 10.1], [3, 4, 7, 8]])
    conf = ArrayValues([0.91, 0.78])
    cls = ArrayValues([0, 0])


class FakePrediction:
    boxes = FakeBoxes()
    names = {0: "person"}


class FakeModel:
    def __init__(self):
        self.kwargs = None

    def predict(self, **kwargs):
        self.kwargs = kwargs
        return [FakePrediction()]


def test_detector_preserves_multiple_same_class_instances_and_threshold():
    model = FakeModel()
    detections, elapsed = ObjectDetector(model).detect(np.zeros((12, 12, 3), dtype=np.uint8), 0.4)

    assert len(detections) == 2
    assert [item["label"] for item in detections] == ["person", "person"]
    assert detections[0]["box"] == [1, 2, 10, 10]
    assert detections[0]["confidence"] == 0.91
    assert model.kwargs["conf"] == 0.4
    assert model.kwargs["iou"] == 0.45
    assert elapsed >= 0


def test_decode_image_rejects_non_image_bytes():
    try:
        decode_image(b"not an image", max_pixels=100_000, max_side=100)
    except ValueError as exc:
        assert "not a readable image" in str(exc)
    else:
        raise AssertionError("Invalid image bytes should be rejected.")


def test_draw_detections_returns_same_sized_image():
    image = np.zeros((20, 20, 3), dtype=np.uint8)
    output = draw_detections(image, [{"label": "person", "confidence": 0.9, "box": [2, 2, 18, 18]}])
    assert output.shape == image.shape
    assert np.any(output != image)
