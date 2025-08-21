from pdf2image import convert_from_path
from pathlib import Path
import zipfile, tempfile

def pdf_to_images_zip(in_path: Path, out_path: Path):
    # honor tif vs tiff in the ZIP filenames
    want = out_path.suffix.replace(".", "").lower()   # 'jpg'|'png'|'tif'|'tiff'
    pages = convert_from_path(str(in_path), dpi=300)

    zip_path = out_path.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for idx, img in enumerate(pages, start=1):
            if want in ("tif", "tiff"):
                ext = "tif"   # filename extension inside the zip
                name = f"page-{idx:04d}.{ext}"
                with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
                    img.save(tmp.name, "TIFF", compression="tiff_deflate")
                    zf.write(tmp.name, arcname=name)
            elif want in ("jpg", "jpeg"):
                name = f"page-{idx:04d}.jpg"
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    img.save(tmp.name, "JPEG", quality=92, optimize=True)
                    zf.write(tmp.name, arcname=name)
            else:  # png
                name = f"page-{idx:04d}.png"
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    img.save(tmp.name, "PNG")
                    zf.write(tmp.name, arcname=name)
    return zip_path

