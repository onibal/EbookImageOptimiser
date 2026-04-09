"""
Image processing functions for the Ebook Image Optimiser.
"""

from typing import List, Tuple
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from src import params_class
import sys
import os


def get_cascade_path(filename: str) -> str:
    """
    Finds the absolute path to a bundled data file (like a cascade.xml).
    This works for both normal script execution and for a frozen EXE.
    """
    # Check if the script is running in a frozen state (e.g., as a PyInstaller EXE)
    if getattr(sys, 'frozen', False):
        # The application is frozen. The base directory is the temp folder where PyInstaller unpacks.
        base_path = sys._MEIPASS
    else:
        # The application is running in a normal Python environment.
        # The base directory is the directory of the script file.
        base_path = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the cascade file
    return os.path.join(base_path, filename)


def detect_faces_cv(img_rgb: Image.Image) -> List[Tuple[int, int, int, int]]:
    """
    Detect faces in a PIL RGB image using OpenCV Haar cascade.
    Returns a list of (x, y, w, h) in the image coordinate space.
    """
    # Convert PIL -> numpy RGB -> grayscale
    arr = np.array(img_rgb.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Use default frontal face cascade from the installed opencv-python package
    cascade_filename = "haarcascade_frontalface_default.xml"
    cascade_path = get_cascade_path(cascade_filename)
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        # Raise an exception to halt execution immediately
        raise RuntimeError(
            f"CRITICAL ERROR: Failed to load the Haar cascade XML file.\n"
            f"Path was: {cascade_path}\n"
            "Please ensure OpenCV is installed correctly and the file exists."
        )
        return []

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=6,
        minSize=(60, 60),  # tune if needed
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    # faces is an ndarray of shape (N,4) or empty tuple
    if isinstance(faces, np.ndarray):
        return [tuple(map(int, f)) for f in faces.tolist()]
    return []


def smart_cover_crop(img: Image.Image, target_w: int, target_h: int, avoid_face_cropping: bool) -> Image.Image:
    """
    Resizes and crops an image to a target size.
    If debug_draw is True, it draws detection boxes and the crop area instead of cropping.
    """
    # --- Resize to cover ---
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(round(src_w * scale))
    new_h = int(round(src_h * scale))
    resized = img.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)

    # --- Default center crop ---
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2

    # Prepare a mutable image for drawing if in debug mode
    debug_img_cv = None

    debug_draw = False
    if debug_draw:
        # Convert PIL (RGB) to OpenCV (BGR) format for drawing
        debug_img_cv = cv2.cvtColor(np.array(resized.convert("RGB")), cv2.COLOR_RGB2BGR)

    if avoid_face_cropping and 'cv2' in globals():
        faces = detect_faces_cv(resized)

        if faces:
            # --- Calculate the initial union box of all faces ---
            x1 = min(x for x, y, w, h in faces)
            y1 = min(y for x, y, w, h in faces)
            x2 = max(x + w for x, y, w, h in faces)
            y2 = max(y + h for x, y, w, h in faces)

            face_box_w = x2 - x1
            face_box_h = y2 - y1

            # Calculate a margin
            FACE_BOX_MARGIN_PERCENT = 0.4
            margin_x = int(face_box_w * (FACE_BOX_MARGIN_PERCENT / 2))
            margin_y = int(face_box_h * (FACE_BOX_MARGIN_PERCENT / 2))

            # Apply the margins to get the new, expanded box
            expanded_x1 = x1 - margin_x
            expanded_y1 = y1 - margin_y
            expanded_x2 = x2 + margin_x
            expanded_y2 = y2 + margin_y

            # Clamp the expanded box to ensure it stays within the image boundaries
            final_x1 = max(0, expanded_x1)
            final_y1 = max(0, expanded_y1)
            final_x2 = min(new_w, expanded_x2)
            final_y2 = min(new_h, expanded_y2)

            face_box_center_x = (final_x1 + final_x2) // 2
            face_box_center_y = (final_y1 + final_y2) // 2

            left = face_box_center_x - target_w // 2
            top = face_box_center_y - target_h // 2

            left = max(0, min(left, new_w - target_w))
            top = max(0, min(top, new_h - target_h))

            if debug_draw:
                # Draw individual face boxes (GREEN)
                for (x, y, w, h) in faces:
                    cv2.rectangle(debug_img_cv, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Draw the union box (BLUE)
                cv2.rectangle(debug_img_cv, (x1, y1), (x2, y2), (255, 0, 0), 3)

    right = left + target_w
    bottom = top + target_h

    # --- Final Return Logic ---
    if debug_draw:
        # Draw the final crop area (RED)
        cv2.rectangle(debug_img_cv, (left, top), (right, bottom), (0, 0, 255), 4)
        # Convert back to PIL Image for return
        return Image.fromarray(cv2.cvtColor(debug_img_cv, cv2.COLOR_BGR2RGB))
    else:
        # Perform the actual crop
        return resized.crop((left, top, right, bottom))


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
            target_w, target_h = params.crop_width, params.crop_height
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
