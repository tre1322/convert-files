from pdf2image import convert_from_path
from pathlib import Path
import zipfile, tempfile

def pdf_to_images_zip(in_path: Path, out_path: Path):
    """
    Convert all pages to images of the requested format and return a ZIP path.
    out_path's suffix tells us the target image type (jpeg/png/tiff).
    """
    fmt = out_path.suffix.replace(".", "").lower()  # "jpeg"|"png"|"tiff"
    pages = convert_from_path(str(in_path), dpi=300)  # requires poppler

    # Create ZIP alongside out_path
    zip_path = out_path.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for idx, img in enumerate(pages, start=1):
            # Always store as .jpg for "jpeg" ext
            ext = "jpg" if fmt in ("jpeg", "jpg") else "png" if fmt == "png" else "tiff"
            name = f"page-{idx:04d}.{ext}"
            with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                # For TIFF, use a reasonable compression to keep size sane
                if ext == "tiff":
                    img.save(tmp.name, "TIFF", compression="tiff_deflate")
                elif ext == "jpg":
                    img.save(tmp.name, "JPEG", quality=92, optimize=True)
                else:
                    img.save(tmp.name, "PNG")
                zf.write(tmp.name, arcname=name)
    # Return the ZIP path explicitly so app.py can prefer it
    return zip_path
