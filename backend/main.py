import os
import uuid
import json
import shutil
import subprocess
from pathlib import Path
from threading import Thread
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .style_profiles import STYLE_PROFILES

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
UPLOADS = DATA / "uploads"
OUTPUTS = DATA / "outputs"
UPLOADS.mkdir(parents=True, exist_ok=True)
OUTPUTS.mkdir(parents=True, exist_ok=True)

MAX_BYTES = 1024 * 1024 * 1024
ALLOWED = {".mp4", ".mov", ".webm", ".mkv"}

jobs = {}

app = FastAPI(title="AI Video Editor API", version="1.0.0")

origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ffprobe_duration(path: Path) -> float:
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True
    )
    if p.returncode != 0:
        raise ValueError("Unable to read video metadata.")
    return float(p.stdout.strip())

def build_edit_plan(brief: str, style: str, aspect: str, resolution: str):
    profile = STYLE_PROFILES.get(style, STYLE_PROFILES["reference_fast_storytelling"])
    return {
        "style": style,
        "style_name": profile["name"],
        "brief": brief.strip(),
        "aspect_ratio": aspect,
        "resolution": resolution,
        "rules": profile["rules"],
        "engine": "ffmpeg_starter_pipeline",
    }

def render(job_id: str, source: Path, output: Path, plan: dict):
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 15

        # Deterministic starter render:
        # scale/crop to requested ratio + H.264/AAC browser-compatible MP4.
        aspect = plan["aspect_ratio"]
        res = plan["resolution"]

        if res == "720p":
            height = 720
        elif res == "4K":
            height = 2160
        else:
            height = 1080

        if aspect == "9:16":
            vf = f"scale=-2:{height},crop={height*9//16}:{height}:(iw-{height*9//16})/2:(ih-{height})/2"
        elif aspect == "1:1":
            vf = f"scale=-2:{height},crop={height}:{height}:(iw-{height})/2:(ih-{height})/2"
        else:
            width = int(height * 16 / 9)
            vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"

        # Avoid an invalid crop when the source is smaller than requested by using scale first.
        cmd = [
            "ffmpeg", "-y", "-i", str(source),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart",
            str(output),
        ]
        jobs[job_id]["progress"] = 35
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError(p.stderr[-3000:])

        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["output"] = str(output)
        jobs[job_id]["plan"] = plan
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.get("/health")
def health():
    return {"ok": True, "service": "ai-video-editor-api"}

@app.get("/api/styles")
def styles():
    return {"styles": STYLE_PROFILES}

@app.post("/api/jobs")
async def create_job(
    video: UploadFile = File(...),
    brief: str = Form(""),
    style: str = Form("reference_fast_storytelling"),
    aspect_ratio: str = Form("9:16"),
    resolution: str = Form("1080p"),
):
    ext = Path(video.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(400, "Unsupported video format.")
    if style not in STYLE_PROFILES:
        raise HTTPException(400, "Unknown editing style.")
    if aspect_ratio not in {"9:16", "1:1", "16:9"}:
        raise HTTPException(400, "Invalid aspect ratio.")
    if resolution not in {"720p", "1080p", "4K"}:
        raise HTTPException(400, "Invalid resolution.")

    job_id = uuid.uuid4().hex
    source = UPLOADS / f"{job_id}{ext}"

    size = 0
    with source.open("wb") as f:
        while True:
            chunk = await video.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_BYTES:
                source.unlink(missing_ok=True)
                raise HTTPException(413, "Video is larger than 1 GB.")
            f.write(chunk)

    try:
        duration = ffprobe_duration(source)
    except Exception:
        source.unlink(missing_ok=True)
        raise HTTPException(400, "Invalid or unreadable video.")

    if duration > 300:
        source.unlink(missing_ok=True)
        raise HTTPException(400, "Maximum video duration is 5 minutes.")

    plan = build_edit_plan(brief, style, aspect_ratio, resolution)
    output = OUTPUTS / f"{job_id}.mp4"

    jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "progress": 5,
        "duration": duration,
        "filename": video.filename,
        "output": None,
        "error": None,
        "plan": plan,
    }

    Thread(target=render, args=(job_id, source, output, plan), daemon=True).start()
    return JSONResponse({"job_id": job_id, "status": "queued"})

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    result = dict(job)
    if result.get("output"):
        result["download_url"] = f"/api/jobs/{job_id}/download"
    return result

@app.get("/api/jobs/{job_id}/download")
def download(job_id: str):
    job = jobs.get(job_id)
    if not job or job.get("status") != "completed":
        raise HTTPException(404, "Rendered video is not ready.")
    path = Path(job["output"])
    if not path.exists():
        raise HTTPException(404, "Output file no longer exists.")
    return FileResponse(path, media_type="video/mp4", filename="edited-video.mp4")
