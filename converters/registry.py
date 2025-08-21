# converters/registry.py

from .images import img_to_img, img_to_pdf
from .pdf_raster import pdf_to_images_zip
from .pdf_text import pdf_to_text
from .office import doc_to_pdf, pdf_to_docx
from .tables import pdf_to_excel
from .pptx import pdf_to_pptx
from .vector import eps_to_pdf

# --- Normalization helpers ---
SYNONYMS = {
    "jpeg": "jpg",
    "tif": "tiff",
    "txt": "text",
}

def normalize(fmt: str) -> str:
    """Normalize file type strings so synonyms map to a canonical form."""
    fmt = (fmt or "").lower().strip()
    return SYNONYMS.get(fmt, fmt)

# Map UI terms to actual file extensions for output naming
EXT_MAP = {
    "word": "docx",
    "excel": "xlsx",
    "powerpoint": "pptx",
    "jpg": "jpeg",   # Pillow expects "JPEG"
    "text": "txt",
    # Note: 'tif' and 'tiff' are preserved as user typed
}

# --- Allowed conversions ---
ALLOWED = {
    # Image → PDF
    ("jpg", "pdf"): img_to_pdf,
    ("png", "pdf"): img_to_pdf,
    ("gif", "pdf"): img_to_pdf,
    ("webp", "pdf"): img_to_pdf,
    ("tiff", "pdf"): img_to_pdf,
    ("heic", "pdf"): img_to_pdf,

    # Image → Image
    ("jpg", "png"): img_to_img,
    ("png", "jpg"): img_to_img,
    ("tiff", "jpg"): img_to_img,
    ("tiff", "png"): img_to_img,
    ("webp", "jpg"): img_to_img,
    ("webp", "png"): img_to_img,
    ("heic", "jpg"): img_to_img,
    ("heic", "png"): img_to_img,

    # PDF → Images (returns ZIP)
    ("pdf", "jpg"): pdf_to_images_zip,
    ("pdf", "png"): pdf_to_images_zip,
    ("pdf", "tiff"): pdf_to_images_zip,

    # PDF → Text
    ("pdf", "text"): pdf_to_text,

    # EPS → PDF
    ("eps", "pdf"): eps_to_pdf,

    # CSV → Excel
    ("csv", "excel"): pdf_to_excel,

    # Office ↔ PDF
    ("word", "pdf"): doc_to_pdf,
    ("pdf", "word"): pdf_to_docx,
    ("pdf", "excel"): pdf_to_excel,
    ("pdf", "powerpoint"): pdf_to_pptx,
}

def get_converter(key):
    """Look up a converter function for a (from_type, to_type) pair."""
    from_t, to_t = normalize(key[0]), normalize(key[1])
    fn = ALLOWED.get((from_t, to_t))
    if not fn:
        raise ValueError(f"Converter not implemented for {(from_t, to_t)}")
    return fn
