# converters/vector.py
import subprocess

def eps_to_pdf(in_path, out_path):
    # Ghostscript: gs -dSAFER ...
    cmd = ["gs", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite",
           f"-sOutputFile={out_path}", str(in_path)]
    subprocess.run(cmd, check=True)
