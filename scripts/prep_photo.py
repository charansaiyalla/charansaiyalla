"""
prep_photo.py
Preprocesses a source photograph for ASCII portrait conversion.

Pipeline:
  1. Load image (JPG/JPEG/PNG/WebP)
  2. Remove background using rembg
  3. Composite person onto white background
  4. Convert to grayscale
  5. Apply contrast enhancement (CLAHE-style via Pillow)
  6. Resize/crop for ASCII conversion
  7. Save to data/source-prepped.png

Usage:
    python scripts/prep_photo.py <path-to-photo>

Example:
    python scripts/prep_photo.py source-photo.jpg

Output:
    data/source-prepped.png
"""

import sys
import os
from pathlib import Path

# Check dependencies before import
missing = []
try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
except ImportError:
    missing.append("Pillow")

try:
    import numpy as np
except ImportError:
    missing.append("numpy")

try:
    import cv2
except ImportError:
    missing.append("opencv-python")

try:
    from rembg import remove as rembg_remove
except ImportError:
    missing.append("rembg")

if missing:
    print("[ERROR] Missing dependencies:")
    for pkg in missing:
        print(f"        - {pkg}")
    print("\nInstall with:")
    print("    pip install -r scripts/requirements-local.txt")
    sys.exit(1)

SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp"}
TARGET_WIDTH = 800   # px — target width for ASCII conversion
TARGET_HEIGHT = 1000  # px — target height (portrait aspect ratio)
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "source-prepped.png"


def load_image(path):
    if not path.exists():
        print(f"[ERROR] Input image not found: {path}")
        print("        Please provide a valid photo path.")
        sys.exit(1)

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        print(f"[ERROR] Unsupported image format: {suffix}")
        print(f"        Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        sys.exit(1)

    print(f"[INFO]  Loading image: {path}")
    img = Image.open(path)

    # Convert to RGBA for background removal
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    print(f"[INFO]  Original size: {img.size[0]}x{img.size[1]}")
    return img


def remove_background(img):
    print("[INFO]  Removing background (this may take a moment) ...")
    try:
        result = rembg_remove(img)
        print("[OK]    Background removed.")
        return result
    except Exception as e:
        print(f"[WARNING] Background removal failed: {e}")
        print("[INFO]    Continuing without background removal.")
        return img


def composite_white(img):
    """Composite the RGBA image onto a white background."""
    print("[INFO]  Compositing onto white background ...")
    white_bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white_bg.paste(img, mask=img.split()[3])  # use alpha as mask
    return white_bg.convert("RGB")


def smart_crop(img):
    """
    Crop to the bounding box of non-white pixels, with padding.
    This removes excess white space and centers the subject.
    """
    img_array = np.array(img)
    # Find non-white pixels (threshold: < 240 in any channel)
    mask = np.any(img_array < 240, axis=2)
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]

    if len(rows) == 0 or len(cols) == 0:
        print("[WARNING] Could not detect subject bounds — using full image.")
        return img

    top, bottom = rows[0], rows[-1]
    left, right = cols[0], cols[-1]

    # Add padding
    pad = 30
    top = max(0, top - pad)
    bottom = min(img.height - 1, bottom + pad)
    left = max(0, left - pad)
    right = min(img.width - 1, right + pad)

    cropped = img.crop((left, top, right + 1, bottom + 1))
    print(f"[OK]    Smart-cropped to {cropped.size[0]}x{cropped.size[1]}")
    return cropped


def enhance_contrast(img):
    """
    Apply CLAHE-equivalent contrast enhancement via OpenCV,
    then fall back to Pillow autocontrast.
    """
    print("[INFO]  Enhancing contrast ...")

    # Convert to numpy for OpenCV
    img_array = np.array(img.convert("L"))  # grayscale

    # CLAHE: adaptive histogram equalization
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(img_array)

    # Back to PIL grayscale
    result = Image.fromarray(enhanced, mode="L")

    # Additional slight sharpening
    result = result.filter(ImageFilter.SHARPEN)

    print("[OK]    Contrast enhanced via CLAHE.")
    return result


def resize_for_ascii(img):
    """
    Resize so width and height are appropriate for 80-120 column ASCII output.
    ASCII characters are ~2x taller than wide, so compensate.
    We target a width that, when reduced to ~100 ASCII chars, gives a good result.
    """
    target_w = TARGET_WIDTH
    # Maintain aspect ratio
    aspect = img.height / img.width
    target_h = int(target_w * aspect)
    # Apply character aspect ratio compensation (chars are ~2:1 H:W)
    target_h = int(target_h * 0.45)
    target_h = max(target_h, 200)

    resized = img.resize((target_w, target_h), Image.LANCZOS)
    print(f"[OK]    Resized to {resized.size[0]}x{resized.size[1]} for ASCII conversion.")
    return resized


def main():
    if len(sys.argv) < 2:
        print("[ERROR] No input image provided.")
        print("Usage:  python scripts/prep_photo.py <photo-path>")
        print("Example: python scripts/prep_photo.py source-photo.jpg")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    # Step 1: Load
    img = load_image(input_path)

    # Step 2: Remove background
    img = remove_background(img)

    # Step 3: Composite onto white
    img = composite_white(img)

    # Step 4: Smart crop
    img = smart_crop(img)

    # Step 5: Enhance contrast (converts to grayscale internally)
    img = enhance_contrast(img)

    # Step 6: Resize for ASCII
    img = resize_for_ascii(img)

    # Step 7: Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT_PATH, "PNG", optimize=True)
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"[OK]    Saved preprocessed image → {OUTPUT_PATH} ({size_kb:.1f} KB)")
    print("[DONE]  prep_photo.py complete.")
    print()
    print("Next step:")
    print("    python scripts/make_ascii_svg.py")


if __name__ == "__main__":
    main()
