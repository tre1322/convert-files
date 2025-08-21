# converters/tables.py
import camelot
import pandas as pd

def pdf_to_excel(in_path, out_path):
    tables = camelot.read_pdf(str(in_path), pages="all")
    with pd.ExcelWriter(out_path) as writer:
        for i, t in enumerate(tables):
            t.df.to_excel(writer, index=False, sheet_name=f"table_{i+1}")
