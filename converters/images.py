from PIL import Image
import pillow_heif
from pathlib import Path

pillow_heif.register_heif_opener()

def _open_img(path: Path):
    img = Image.open(path)
    # Normalize weird modes
    if img.mode in ("P", "RGBA", "LA"):
        img = img.convert("RGB")
    return img

def img_to_img(in_path: Path, out_path: Path):
    img = _open_img(in_path)
    fmt = out_path.suffix.replace(".", "").upper()
    if fmt == "JPG": fmt = "JPEG"
    img.save(out_path, fmt)

def img_to_pdf(in_path: Path, out_path: Path):
    img = _open_img(in_path)
    img.save(out_path, "PDF", resolution=300, save_all=False)
