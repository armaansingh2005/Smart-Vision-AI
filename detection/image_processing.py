from io import BytesIO

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


def decode_image(image_bytes, max_pixels, max_side):
    try:
        with Image.open(BytesIO(image_bytes)) as source:
            source.verify()
        with Image.open(BytesIO(image_bytes)) as source:
            source_format = source.format
            image = ImageOps.exif_transpose(source).convert("RGB")
    except Image.DecompressionBombError as exc:
        raise ValueError("Image dimensions exceed the supported safe limits.") from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("The uploaded file is not a readable image. Try exporting it as JPG, PNG, or WEBP.") from exc

    width, height = image.size
    if width <= 0 or height <= 0:
        raise ValueError("The image has invalid dimensions.")
    if width * height > max_pixels:
        raise ValueError(f"Images may not exceed {max_pixels // 1_000_000} megapixels.")

    rgb = np.asarray(image)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    longest_side = max(width, height)
    if longest_side > max_side:
        scale = max_side / longest_side
        resized_dimensions = (round(width * scale), round(height * scale))
        bgr = cv2.resize(bgr, resized_dimensions, interpolation=cv2.INTER_AREA)
    return bgr, source_format
