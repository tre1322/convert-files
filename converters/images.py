# converters/images.py
from PIL import Image
import pillow_heif
from pathlib import Path

# Enable HEIC/HEIF support for Pillow
pillow_heif.register_heif_opener()

def _open_img(path: Path) -> Image.Image:
    """Open an image and normalize to an RGB base if needed."""
    img = Image.open(path)
    if img.mode in ("P", "RGBA", "LA"):
        img = img.convert("RGB")
    return img

def img_to_img(in_path: Path, out_path: Path):
    """
    Generic image->image conversion with proper format mapping:
    - jpg: Pillow format name is "JPEG"
    - tif/tiff: use "TIFF"
    """
    img = _open_img(in_path)
    ext = out_path.suffix.replace(".", "").upper()  # e.g., TIF, TIFF, JPG, PNG
    if ext == "JPG":
        fmt = "JPEG"
    elif ext in ("TIF", "TIFF"):
        fmt = "TIFF"
    else:
        fmt = ext
    img.save(out_path, fmt)

def img_to_pdf(in_path: Path, out_path: Path):
    """
    Any supported raster image -> single-page PDF.
    For multi-frame GIF/TIFF handling, you can extend to save_all=True later.
    """
    img = _open_img(in_path)
    img.save(out_path, "PDF", resolution=300, save_all=False)
