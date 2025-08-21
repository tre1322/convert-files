# app.py
from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid
import shutil
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import MAX_FILE_MB, RETENTION_MINUTES, TMP_ROOT
from converters.registry import get_converter, ALLOWED, EXT_MAP, normalize

# --- extra imports for detection ---
from PIL import Image, UnidentifiedImageError

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
Path(TMP_ROOT).mkdir(parents=True, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
def index():
  return Path("templates/index.html").read_text(encoding="utf-8")

def _job_dir() -> Path:
  d = Path(TMP_ROOT) / f"job-{uuid.uuid4().hex}"
  d.mkdir(parents=True, exist_ok=True)
  return d

def _enforce_size_cap(file_path: Path):
  try:
    size_mb = file_path.stat().st_size / (1024 * 1024)
  except FileNotFoundError:
    raise HTTPException(400, "Uploaded file missing or unreadable.")
  if size_mb > MAX_FILE_MB:
    try:
      file_path.unlink(missing_ok=True)
    finally:
      raise HTTPException(413, f"File too large ({size_mb:.1f} MB). Max is {MAX_FILE_MB} MB.")

# ---- Type inference (when client doesn't pass from_type) ----
KNOWN_BY_EXT = {
  # images
  "jpg": "jpg", "jpeg": "jpg", "png": "png", "gif": "gif", "webp": "webp",
  "tif": "tiff", "tiff": "tiff", "heic": "heic", "bmp": "bmp", "ico": "ico", "avif": "avif",
  "eps": "eps",
  # docs
  "pdf": "pdf", "docx": "word", "doc": "word", "xlsx": "excel", "xls": "excel",
  "pptx": "powerpoint", "ppt": "powerpoint", "csv": "csv", "txt": "text",
}

def infer_from_file(path: Path) -> str:
  # 1) by extension
  ext = path.suffix.lower().lstrip(".")
  if ext in KNOWN_BY_EXT:
    return KNOWN_BY_EXT[ext]
  # 2) quick magic: PDF header
  try:
    with open(path, "rb") as f:
      head = f.read(8)
      if head.startswith(b"%PDF-"):
        return "pdf"
  except Exception:
    pass
  # 3) try Pillow to detect image formats
  try:
    with Image.open(path) as img:
      fmt = (img.format or "").upper()
      mapping = {
        "JPEG": "jpg", "PNG": "png", "GIF": "gif", "TIFF": "tiff",
        "WEBP": "webp", "ICO": "ico", "BMP": "bmp", "AVIF": "avif",
      }
      if fmt in mapping:
        return mapping[fmt]
  except UnidentifiedImageError:
    pass
  except Exception:
    pass
  # fallback
  return ext or "unknown"

# ---------- API ----------
@app.post("/convert")
async def convert(
  to_type: str = Form(...),
  file: UploadFile = File(...),
  # from_type becomes optional; backend will infer if not given
  from_type: str | None = Form(None),
):
  # write input
  jobdir = _job_dir()
  in_path = jobdir / (file.filename or "upload.bin")
  try:
    with open(in_path, "wb") as f:
      shutil.copyfileobj(file.file, f)
  finally:
    try: file.file.close()
    except Exception: pass

  _enforce_size_cap(in_path)

  # determine source type
  src = normalize(from_type) if from_type else normalize(infer_from_file(in_path))
  dst = normalize(to_type)

  if (src, dst) not in ALLOWED:
    raise HTTPException(400, f"Conversion {src} → {dst} not supported.")

  # build output path (keep tif vs tiff choice user made in 'to_type')
  desired_to = (to_type or "").lower().strip()
  out_ext = EXT_MAP.get(desired_to, desired_to)
  out_path = jobdir / f"output.{out_ext}"

  converter = get_converter((src, dst))
  try:
    result_path = converter(in_path, out_path)
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(500, f"Conversion failed: {e}")

  serve_path = Path(result_path) if result_path else out_path
  media_type = "application/zip" if serve_path.suffix.lower()==".zip" else "application/octet-stream"
  return FileResponse(path=serve_path, filename=serve_path.name, media_type=media_type)

# ---------- Janitor ----------
def delete_old_jobs():
  cutoff = time.time() - (RETENTION_MINUTES * 60)
  for job in Path(TMP_ROOT).glob("job-*"):
    try:
      if job.is_dir() and job.stat().st_mtime < cutoff:
        shutil.rmtree(job, ignore_errors=True)
    except Exception:
      pass

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(delete_old_jobs, IntervalTrigger(minutes=5))
scheduler.start()

@app.on_event("shutdown")
def _shutdown():
  try: scheduler.shutdown(wait=False)
  except Exception: pass
