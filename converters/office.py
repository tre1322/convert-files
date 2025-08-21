# converters/office.py
import subprocess, shutil, os
from pdf2docx import parse

def doc_to_pdf(in_path, out_path):
    # Requires LibreOffice installed in PATH
    cmd = ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(out_path.parent), str(in_path)]
    subprocess.run(cmd, check=True)
    # LibreOffice writes filename.pdf next to outdir; ensure final name matches out_path
    produced = out_path.parent / (in_path.stem + ".pdf")
    if produced != out_path:
        produced.rename(out_path)

def pdf_to_docx(in_path, out_path):
    parse(str(in_path), str(out_path))
