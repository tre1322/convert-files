# converters/pdf_text.py
from pdfminer.high_level import extract_text

def pdf_to_text(in_path, out_path):
    text = extract_text(str(in_path))
    out_path.write_text(text, encoding="utf-8")
