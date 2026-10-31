import hashlib

import cv2


def _class_color(label):
    digest = hashlib.sha256(label.encode("utf-8")).digest()
    return (70 + digest[0] % 160, 70 + digest[1] % 160, 70 + digest[2] % 160)


def draw_detections(image, detections):
    annotated = image.copy()
    height, width = annotated.shape[:2]
    for detection in detections:
        x1, y1, x2, y2 = detection["box"]
        x1 = max(0, min(width - 1, x1))
        x2 = max(0, min(width - 1, x2))
        y1 = max(0, min(height - 1, y1))
        y2 = max(0, min(height - 1, y2))
        color = _class_color(detection["label"])
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)
        caption = f'{detection["label"]}  {detection["confidence"] * 100:.1f}%'
        (text_width, text_height), baseline = cv2.getTextSize(caption, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        label_top = max(0, y1 - text_height - baseline - 8)
        cv2.rectangle(annotated, (x1, label_top), (min(width - 1, x1 + text_width + 10), y1), color, -1)
        cv2.putText(
            annotated,
            caption,
            (x1 + 5, max(text_height, y1 - baseline - 4)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
    return annotated
