"""
Image processing functions for the Ebook Image Optimiser.
"""

from typing import List, Tuple
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps

import params_class


def detect_faces_cv(img_rgb: Image.Image) -> List[Tuple[int, int, int, int]]:
    """
    Detect faces in a PIL RGB image using OpenCV Haar cascade.
    Returns a list of (x, y, w, h) in the image coordinate space.
    """
    # Convert PIL -> numpy RGB -> grayscale
    arr = np.array(img_rgb.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    gray = cv2.equalizeHist(gray)

    # Use default frontal face cascade from the installed opencv-python package
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        return []

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),  # tune if needed
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    # faces is an ndarray of shape (N,4) or empty tuple
    if isinstance(faces, np.ndarray):
        return [tuple(map(int, f)) for f in faces.tolist()]
    return []


def smart_cover_crop(img: Image.Image, target_w: int, target_h: int, avoid_face_cropping: bool) -> Image.Image:
    """
    Resize (cover) then crop to target size.
    If `avoid_face_cropping` is True and OpenCV finds faces,
    shift the crop window to keep faces within (with small margins).
    Fallback: center crop.
    """
    # --- resize to cover ---
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(round(src_w * scale))
    new_h = int(round(src_h * scale))
    resized = img.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)

    # default center crop
    left = max(0, (new_w - target_w) // 2)
    top = max(0, (new_h - target_h) // 2)

    if avoid_face_cropping and cv2 is not None:
        faces = detect_faces_cv(resized)
        if faces:
            # Union box of all faces
            x1 = min(x for x, y, w, h in faces)
            y1 = min(y for x, y, w, h in faces)
            x2 = max(x + w for x, y, w, h in faces)
            y2 = max(y + h for x, y, w, h in faces)

            # Add a small margin around faces (5% of target size)
            margin_x = int(round(0.05 * target_w))
            margin_y = int(round(0.05 * target_h))
            x1 -= margin_x
            y1 -= margin_y
            x2 += margin_x
            y2 += margin_y

            # Compute crop window so union box fits inside, if possible
            max_left = max(0, new_w - target_w)
            max_top = max(0, new_h - target_h)

            # Desired top-left that includes x1/y1
            desired_left = x1
            desired_top = y1

            # Clamp to image bounds
            left = max(0, min(desired_left, max_left))
            top = max(0, min(desired_top, max_top))

            # Ensure right/bottom edges include x2/y2; shift if needed
            if x2 > left + target_w:
                left = min(max_left, max(0, x2 - target_w))
            if y2 > top + target_h:
                top = min(max_top, max(0, y2 - target_h))

            # Note: if union face box is larger than target area, some cropping is inevitable.

    return resized.crop((left, top, left + target_w, top + target_h))


def process_image(params: 'params_class.ProcessingParams') -> None:
    """
    Process a single image according to the settings in `params` and save as JPEG.
    Steps:
    1) Respect EXIF orientation.
    2) Force landscape if requested.
    3) Conditionally apply exposure/brightness, saturation, contrast.
    4) Optionally smart resize+crop to Kobo Libra dimensions (face-aware if enabled).
    5) Save JPEG with specified quality, 4:4:4 chroma subsampling.
    """
    in_path = params.in_path
    out_path = params.out_path

    with Image.open(in_path) as im:
        # Normalize orientation using EXIF (handles rotated images from cameras/phones)
        im = ImageOps.exif_transpose(im)

        # Ensure we are in RGB for enhancements and JPEG saving.
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        elif im.mode == "RGBA":
            # Flatten alpha onto white background to avoid black/transparent areas in JPEG
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[3])
            im = bg

        # Adjustments (only if enabled and not neutral)
        if params.use_exposure and params.exposure_factor != 1.0:
            im = ImageEnhance.Brightness(im).enhance(float(params.exposure_factor))

        sat_factor = max(0.0, float(params.saturation_val) / 100.0)
        if params.use_saturation and sat_factor != 1.0:
            im = ImageEnhance.Color(im).enhance(sat_factor)

        ctr_factor = max(0.0, float(params.contrast_val) / 100.0)
        if params.use_contrast and ctr_factor != 1.0:
            im = ImageEnhance.Contrast(im).enhance(ctr_factor)

        # Crop to Kobo Libra Colour dimensions if requested
        if params.crop_kobo:
            target_w, target_h = 1680, 1264
            im = smart_cover_crop(im, target_w, target_h, params.avoid_face_cropping)

        # Apply rotation if requested (0 means no rotation)
        if params.rotation_angle != 0:
            im = im.rotate(-params.rotation_angle, expand=True)  # Negative because PIL uses counter-clockwise rotation

        # Save as JPEG to output path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        im.save(
            out_path.with_suffix(".jpg"),
            format="JPEG",
            quality=int(params.jpg_quality),
            optimize=True,
            subsampling=0,  # 4:4:4 to avoid color bleeding on fine details
        )
