# backend/jobs.py
import uuid
from pathlib import Path
import json
from enum import Enum
from datetime import datetime
import os

# Prefer /data/jobs if writable, else fallback to ~/migration_tool_jobs
preferred_path = Path("/data/jobs")
if preferred_path.exists() and os.access(preferred_path, os.W_OK):
    JOBS_ROOT = preferred_path
else:
    JOBS_ROOT = Path.home() / "migration_tool_jobs"

JOBS_ROOT.mkdir(parents=True, exist_ok=True)
print(f"Using JOBS_ROOT: {JOBS_ROOT}")

class Status(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

def new_job(client, cloud, filenames):
    job_id = uuid.uuid4().hex[:12]
    job_dir = JOBS_ROOT / job_id
    (job_dir / "uploads").mkdir(parents=True, exist_ok=True)
    (job_dir / "out").mkdir(parents=True, exist_ok=True)
    meta = {
        "job_id": job_id,
        "client": client,
        "cloud": cloud,
        "files": filenames,
        "status": Status.QUEUED.value,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "message": ""
    }
    (job_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    return job_id, job_dir

def update_meta(job_id, **kwargs):
    job_dir = JOBS_ROOT / job_id
    meta_file = job_dir / "meta.json"
    meta = json.loads(meta_file.read_text())
    meta.update(kwargs)
    meta["updated_at"] = datetime.utcnow().isoformat()
    meta_file.write_text(json.dumps(meta, indent=2))
    return meta

def get_meta(job_id):
    job_dir = JOBS_ROOT / job_id
    meta_file = job_dir / "meta.json"
    if not meta_file.exists():
        return None
    return json.loads(meta_file.read_text())
