import base64
import io
import logging
from typing import Any

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
_face_cascade = cv2.CascadeClassifier(_cascade_path)

if _face_cascade.empty():
    logger.error("Failed to load Haar cascade from: %s", _cascade_path)
    raise RuntimeError(f"Haar cascade not found at {_cascade_path}")


def extract_faces_from_image(
    image: Image.Image,
    page_number: int | None = None,
    padding_ratio: float = 0.35,
    jpeg_quality: int = 85,
) -> list[dict[str, Any]]:
    """Detect faces in a PIL Image and return extracted face crops as base64 JPEG.

    Args:
        image: PIL Image (already resized by the caller if needed).
        page_number: Page number for PDF inputs (1-indexed), None for images.
        padding_ratio: How much to expand the detected face bounding box
                       (0.35 = 35% on each side).
        jpeg_quality: JPEG encoding quality (1-100).

    Returns:
        List of dicts with keys: image_base64, page, bbox, image_width, image_height.
    """
    image_rgb = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)

    faces = _face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )

    if len(faces) == 0:
        return []

    img_height, img_width = image_rgb.shape[:2]
    results = []

    for x, y, w, h in faces:
        pad_w = int(w * padding_ratio)
        pad_h = int(h * padding_ratio)

        x1 = max(0, x - pad_w)
        y1 = max(0, y - pad_h)
        x2 = min(img_width, x + w + pad_w)
        y2 = min(img_height, y + h + pad_h)

        face_crop = image_rgb[y1:y2, x1:x2]

        crop_pil = Image.fromarray(face_crop)
        buffer = io.BytesIO()
        crop_pil.save(buffer, format="JPEG", quality=jpeg_quality)
        b64_str = base64.b64encode(buffer.getvalue()).decode("ascii")

        results.append({
            "image_base64": b64_str,
            "page": page_number,
            "bbox": {
                "x": x1,
                "y": y1,
                "width": x2 - x1,
                "height": y2 - y1,
            },
            "image_width": x2 - x1,
            "image_height": y2 - y1,
        })

    logger.info(
        "Detected %d face(s) on %s",
        len(results),
        f"page {page_number}" if page_number else "image",
    )

    return results
