from .images import img_to_img, img_to_pdf
from .pdf_raster import pdf_to_images_zip
from .pdf_text import pdf_to_text
from .office import doc_to_pdf, pdf_to_docx
from .tables import pdf_to_excel
from .pptx import pdf_to_pptx
from .vector import eps_to_pdf

# Map UI "types" to real file extensions
EXT_MAP = {
    "word": "docx",
    "excel": "xlsx",
    "powerpoint": "pptx",
    "jpg": "jpeg",  # Pillow format name
    "text": "txt",
}

ALLOWED = {
    # Image → PDF
    ("jpg", "pdf"): img_to_pdf, ("png", "pdf"): img_to_pdf, ("gif", "pdf"): img_to_pdf,
    ("webp", "pdf"): img_to_pdf, ("tiff", "pdf"): img_to_pdf, ("heic", "pdf"): img_to_pdf,
    # Image → Image
    ("jpg", "png"): img_to_img, ("png", "jpg"): img_to_img,
    ("tiff", "jpg"): img_to_img, ("tiff", "png"): img_to_img,
    ("webp", "jpg"): img_to_img, ("webp", "png"): img_to_img,
    ("heic", "jpg"): img_to_img, ("heic", "png"): img_to_img,

    # PDF → images (returns ZIP path)
    ("pdf", "jpg"): pdf_to_images_zip,
    ("pdf", "png"): pdf_to_images_zip,
    ("pdf", "tiff"): pdf_to_images_zip,

    # PDF → text
    ("pdf", "text"): pdf_to_text,

    # EPS → PDF
    ("eps", "pdf"): eps_to_pdf,

    # CSV → Excel
    ("csv", "excel"): pdf_to_excel,  # function name is legacy—it's fine

    # Office ↔ PDF (Stage 2 ready)
    ("word", "pdf"): doc_to_pdf, ("pdf", "word"): pdf_to_docx,
    ("pdf", "excel"): pdf_to_excel, ("pdf", "powerpoint"): pdf_to_pptx,
}

def get_converter(key):
    fn = ALLOWED.get(key)
    if not fn:
        raise ValueError(f"Converter not implemented for {key}")
    return fn
