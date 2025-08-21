from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid, shutil, os, time, zipfile

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import MAX_FILE_MB, RETENTION_MINUTES, TMP_ROOT
from converters.registry import get_converter, ALLOWED, EXT_MAP

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

Path(TMP_ROOT).mkdir(parents=True, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
def index():
    return Path("templates/index.html").read_text(encoding="utf-8")

def _enforce_size_cap(file_path: Path):
    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_MB:
        try:
            file_path.unlink(missing_ok=True)
        finally:
            raise HTTPException(413, f"File too large ({size_mb:.1f} MB). Max is {MAX_FILE_MB} MB.")

def _job_dir() -> Path:
    d = Path(TMP_ROOT) / f"job-{uuid.uuid4().hex}"
    d.mkdir(parents=True, exist_ok=True)
    return d

@app.post("/convert")
async def convert(
    from_type: str = Form(...),
    to_type: str = Form(...),
    file: UploadFile = File(...)
):
    key = (from_type.lower(), to_type.lower())
    if key not in ALLOWED:
        raise HTTPException(400, f"Conversion {from_type} → {to_type} not supported.")

    jobdir = _job_dir()
    in_path = jobdir / file.filename
    with open(in_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    _enforce_size_cap(in_path)

    out_ext = EXT_MAP.get(to_type.lower(), to_type.lower())
    # primary output path; for multi-file outputs we'll return a .zip
    out_path = jobdir / f"output.{out_ext}"

    converter = get_converter(key)

    try:
        result = converter(in_path, out_path)
    except Exception as e:
        raise HTTPException(500, f"Conversion failed: {e}")

    # If converter returned a path (e.g., created a zip), honor it
    serve_path = Path(result) if result else out_path
    media = "application/zip" if serve_path.suffix.lower() == ".zip" else "application/octet-stream"
    return FileResponse(path=serve_path, filename=serve_path.name, media_type=media)

# --- Janitor: delete job dirs older than RETENTION_MINUTES ---
def delete_old_jobs():
    cutoff = time.time() - (RETENTION_MINUTES * 60)
    for child in Path(TMP_ROOT).glob("job-*"):
        try:
            if child.is_dir() and child.stat().st_mtime < cutoff:
                shutil.rmtree(child, ignore_errors=True)
        except Exception:
            pass  # stay quiet; next run will try again

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(delete_old_jobs, IntervalTrigger(minutes=5))
scheduler.start()

@app.on_event("shutdown")
def _shutdown():
    scheduler.shutdown(wait=False)
