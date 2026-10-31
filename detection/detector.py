import time
import threading


class ObjectDetector:
    def __init__(self, model):
        self.model = model
        self._inference_lock = threading.Lock()

    def detect(self, image, confidence):
        with self._inference_lock:
            started = time.perf_counter()
            predictions = self.model.predict(
                source=image,
                conf=confidence,
                iou=0.45,
                verbose=False,
            )
            inference_seconds = time.perf_counter() - started
        detections = []
        if not predictions:
            return detections, inference_seconds

        prediction = predictions[0]
        boxes = prediction.boxes
        if boxes is None:
            return detections, inference_seconds
        coordinates = boxes.xyxy.cpu().numpy()
        scores = boxes.conf.cpu().numpy()
        class_ids = boxes.cls.cpu().numpy()
        names = prediction.names
        for coordinates_item, score, class_id in zip(coordinates, scores, class_ids):
            category_id = int(class_id)
            label = names[category_id] if isinstance(names, dict) else names[category_id]
            x1, y1, x2, y2 = (int(round(value)) for value in coordinates_item)
            detections.append(
                {
                    "class_id": category_id,
                    "label": str(label),
                    "confidence": round(float(score), 4),
                    "box": [x1, y1, x2, y2],
                }
            )
        return detections, inference_seconds
