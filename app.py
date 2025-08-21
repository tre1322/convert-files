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

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure temp root exists
Path(TMP_ROOT).mkdir(parents=True, exist_ok=True)


# ---------- UI ----------
@app.get("/", response_class=HTMLResponse)
def index():
    return Path("templates/index.html").read_text(encoding="utf-8")


# ---------- Helpers ----------
def _job_dir() -> Path:
    """Create and return a unique working directory for this job."""
    d = Path(TMP_ROOT) / f"job-{uuid.uuid4().hex}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _enforce_size_cap(file_path: Path):
    """Raise 413 if file exceeds MAX_FILE_MB."""
    try:
        size_mb = file_path.stat().st_size / (1024 * 1024)
    except FileNotFoundError:
        raise HTTPException(400, "Uploaded file missing or unreadable.")
    if size_mb > MAX_FILE_MB:
        # Best effort cleanup of the uploaded file before raising
        try:
            file_path.unlink(missing_ok=True)
        finally:
            raise HTTPException(
                413,
                f"File too large ({size_mb:.1f} MB). Max is {MAX_FILE_MB} MB.",
            )


# ---------- API ----------
@app.post("/convert")
async def convert(
    from_type: str = Form(...),
    to_type: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Convert an uploaded file from one type to another.
    - Validates the requested pair (normalized to handle tif/tiff, jpeg/jpg, etc.)
    - Writes work to a per-job temp dir
    - Returns the resulting file (or ZIP) as a download
    """
    # Normalize the selection so 'tif' behaves like 'tiff', 'jpeg' like 'jpg', etc.
    norm_from = normalize(from_type)
    norm_to = normalize(to_type)

    if (norm_from, norm_to) not in ALLOWED:
        raise HTTPException(
            400, f"Conversion {from_type} → {to_type} not supported."
        )

    jobdir = _job_dir()
    in_path = jobdir / (file.filename or f"upload.{norm_from}")
    try:
        with open(in_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    finally:
        # FastAPI's UploadFile uses a SpooledTemporaryFile; close it to flush/cleanup
        try:
            file.file.close()
        except Exception:
            pass

    _enforce_size_cap(in_path)

    # Choose output extension.
    # EXT_MAP only remaps when a format forces a different extension (e.g., word->docx).
    # If the user selected 'tif', we keep 'tif' (no remap).
    desired_to = (to_type or "").lower().strip()
    out_ext = EXT_MAP.get(desired_to, desired_to)
    out_path = jobdir / f"output.{out_ext}"

    converter = get_converter((norm_from, norm_to))

    try:
        # Some converters (e.g., pdf->images) return a ZIP path; if they return None,
        # we serve out_path.
        result_path = converter(in_path, out_path)
    except HTTPException:
        # Pass through deliberate HTTP errors (rare)
        raise
    except Exception as e:
        raise HTTPException(500, f"Conversion failed: {e}")

    serve_path = Path(result_path) if result_path else out_path
    media_type = (
        "application/zip"
        if serve_path.suffix.lower() == ".zip"
        else "application/octet-stream"
    )

    return FileResponse(
        path=serve_path,
        filename=serve_path.name,
        media_type=media_type,
    )


# ---------- Janitor (30‑minute retention) ----------
def delete_old_jobs():
    cutoff = time.time() - (RETENTION_MINUTES * 60)
    for job in Path(TMP_ROOT).glob("job-*"):
        try:
            if job.is_dir() and job.stat().st_mtime < cutoff:
                shutil.rmtree(job, ignore_errors=True)
        except Exception:
            # Ignore and try again on the next sweep
            pass


scheduler = BackgroundScheduler(daemon=True)
# Sweep every 5 minutes
scheduler.add_job(delete_old_jobs, IntervalTrigger(minutes=5))
scheduler.start()


@app.on_event("shutdown")
def _shutdown():
    try:
        scheduler.shutdown(wait=False)
    except Exception:
        pass
