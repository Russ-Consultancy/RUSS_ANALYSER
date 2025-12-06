# backend/app.py
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, UploadFile, Form, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse
from pathlib import Path
from typing import List, Optional
from passlib.context import CryptContext
from datetime import datetime, timedelta
from backend.history_utils import load_history, load_user_history, HISTORY_DIR
from fastapi import Query
from typing import Optional
import sqlite3
import hmac, hashlib, base64
import shutil
import subprocess
import zipfile
import json
import os
import io

# ---------------------------------------------------------------------
# ⚙️ Initialize FastAPI app
# ---------------------------------------------------------------------
app = FastAPI(title="RUSS Consultancy Migration Tool")

# ---------------------------------------------------------------------
# 🧩 Include Routers (after app created)
# ---------------------------------------------------------------------
try:
    from backend.profile_admin import router as profile_admin_router
    app.include_router(profile_admin_router)
except Exception as e:
    # If router import fails, log but continue (so devs can still use upload/analyze)
    print("⚠️ Failed to include profile_admin router:", e)

# ---------------------------------------------------------------------
# 📁 PATH SETUP
# ---------------------------------------------------------------------
BASE = Path(__file__).resolve().parent
# NOTE: in your original layout BASE was parent.parent; adjust if your project layout differs.
# If your project root is backend/ and frontend is sibling, use parent:
PROJECT_ROOT = BASE.parent
FRONTEND = PROJECT_ROOT / "frontend"
UPLOADS = PROJECT_ROOT / "uploads"
OUTPUTS = PROJECT_ROOT / "outputs"
WORKER = PROJECT_ROOT / "worker"
RUN_MULTI = WORKER / "multi_analyze.py"

# Ensure directories exist
UPLOADS.mkdir(parents=True, exist_ok=True)
(UPLOADS / "profiles").mkdir(parents=True, exist_ok=True)  # ensure profiles folder exists
OUTPUTS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------
# 🧭 Serve static files (frontend + outputs)
# ---------------------------------------------------------------------
if FRONTEND.exists():
    app.mount("/frontend", StaticFiles(directory=FRONTEND), name="frontend")
app.mount("/outputs", StaticFiles(directory=OUTPUTS), name="outputs")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS)), name="uploads")

# ---------------------------------------------------------------------
# 🏠 HOME ROUTE
# ---------------------------------------------------------------------
@app.get("/")
def home():
    return RedirectResponse(url="/frontend/login.html")

# ---------------------------------------------------------------------
# 📊 DASHBOARD ROUTE
# ---------------------------------------------------------------------
@app.get("/dashboard.html")
def dashboard():
    html_path = FRONTEND / "dashboard.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(), status_code=200)
    return HTMLResponse("<h3>dashboard.html not found</h3>", status_code=404)

# ---------------------------------------------------------------------
# 📤 UPLOAD ENDPOINT
# ---------------------------------------------------------------------
@app.post("/upload-awrs")
async def upload_awrs(
    cloud: str = Form(...),
    user_email: str = Form("unknown"),
    files: Optional[List[UploadFile]] = File(None),
    job_type: Optional[str] = Form(None),
    # manual fields (optional) — individual fields for manual-only submissions
    vcpu: Optional[str] = Form(None),
    memory: Optional[str] = Form(None),
    iops: Optional[str] = Form(None),
    throughput: Optional[str] = Form(None)
):
    """
    Accept uploaded files (optional) and/or manual inputs.
    - files: list of UploadFile objects (may be empty / None)
    - job_type: optional string 'upload'|'manual'|'mixed' (frontend sends this)
    - vcpu, memory, iops, throughput: optional manual fields (strings or numbers)
    Behavior:
    - Save uploaded files into uploads/
    - Extract zip files into uploads/
    - If manual fields provided, write uploads/manual_inputs.json (single object)
    - Return {"status": "uploaded", "files": [...], "manual": bool}
    """
    try:
        # Normalize job type determination if not provided
        has_files = bool(files and len(files) > 0)
        has_manual = any([vcpu is not None, memory is not None, iops is not None, throughput is not None])

        if job_type is None:
            if has_files and has_manual:
                job_type = "mixed"
            elif has_manual:
                job_type = "manual"
            else:
                job_type = "upload"

        # Create a fresh upload job folder (optional - currently we use uploads/ root)
        # Clear previous uploads but preserve profile images
        for f in UPLOADS.glob("*"):
            try:
                # Skip the 'profiles' folder to preserve profile pictures
                if f.name == "profiles":
                    continue

                if f.is_file():
                    f.unlink()
                elif f.is_dir():
                    shutil.rmtree(f)
            except Exception as e:
                print(f"⚠️ Cleanup skipped for {f}: {e}")

        # Ensure profiles directory still exists after cleanup
        (UPLOADS / "profiles").mkdir(parents=True, exist_ok=True)

        saved_files = []

        # Save uploaded files (if any)
        if has_files:
            for up in files:
                filename = up.filename
                if not filename:
                    continue
                lower = filename.lower()
                safe_name = os.path.basename(filename)
                dest = UPLOADS / safe_name

                # Read bytes for the upload (works for both small and larger files)
                file_bytes = await up.read()

                # If zip: extract members
                if lower.endswith(".zip"):
                    try:
                        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                            for member in z.namelist():
                                # skip directories and macOS metadata
                                if member.endswith("/") or member.startswith("__MACOSX"):
                                    continue
                                member_name = os.path.basename(member)
                                if not member_name:
                                    continue
                                member_dest = UPLOADS / member_name
                                with member_dest.open("wb") as out_f:
                                    out_f.write(z.read(member))
                                saved_files.append(str(member_dest.name))
                    except zipfile.BadZipFile:
                        # Treat it as regular file fallback
                        with dest.open("wb") as out_f:
                            out_f.write(file_bytes)
                        saved_files.append(str(dest.name))
                else:
                    # Regular file
                    with dest.open("wb") as out_f:
                        out_f.write(file_bytes)
                    saved_files.append(str(dest.name))

        # Save manual inputs if provided (explicit fields)
        manual_saved = False
        manual_obj = {}
        if has_manual:
            # convert numeric-looking strings to numbers where possible
            def to_num(v):
                if v is None or v == "":
                    return None
                try:
                    if isinstance(v, (int, float)):
                        return v
                    if "." in str(v):
                        return float(v)
                    else:
                        return int(v)
                except Exception:
                    try:
                        return float(v)
                    except Exception:
                        return v

            if vcpu is not None:
                manual_obj["vcpus"] = to_num(vcpu)
            if memory is not None:
                manual_obj["memory_gb"] = to_num(memory)
            if iops is not None:
                manual_obj["iops"] = to_num(iops)
            if throughput is not None:
                manual_obj["throughput_mb_s"] = to_num(throughput)

            # Add metadata
            manual_obj["_meta"] = {
                "job_type": job_type,
                "cloud": cloud,
                "received_at": datetime.utcnow().isoformat()
            }

            try:
                manual_path = UPLOADS / "manual_inputs.json"
                with manual_path.open("w") as mf:
                    json.dump(manual_obj, mf, indent=2)
                manual_saved = True
            except Exception as e:
                print("❌ Failed to save manual inputs:", e)

        # If no files and no manual inputs -> error
        if not has_files and not manual_saved:
            return JSONResponse({"status": "error", "message": "No files uploaded and no manual data provided."}, status_code=400)

        print(f"✅ Uploaded files: {len(saved_files)} manual_saved={manual_saved} job_type={job_type} for cloud={cloud}")
        return JSONResponse({"status": "uploaded", "files": saved_files, "manual_saved": manual_saved, "job_type": job_type})

    except Exception as e:
        print("❌ Upload failed:", str(e))
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


# ---------------------------------------------------------------------
# 🧠 ANALYZE ENDPOINT (ASYNC, NON-BLOCKING)
# ---------------------------------------------------------------------
progress_status = {"percent": 0, "message": "Idle"}

def run_analysis_task(cloud: str,user_email: str):
    """
    Background task that executes the worker pipeline.
    The worker (multi_analyze.py) should be able to process:
      - HTML/HTM files found in uploads/
      - CSV/XLSX files in uploads/
      - manual_inputs.json in uploads/
    """
    try:
        progress_status.update({"percent": 5, "message": f"Starting analysis for {cloud.upper()}..."})
        print(f"⚙️ Running analysis for {cloud.upper()}...")

        # Cleanup previous outputs
        progress_status.update({"percent": 10, "message": "Cleaning previous outputs..."})
        for f in OUTPUTS.glob("*"):
            try:
                if f.is_file():
                    f.unlink()
                elif f.is_dir():
                    shutil.rmtree(f)
            except Exception:
                pass

        # Run AWR analyzer (worker script)
        progress_status.update({"percent": 40, "message": "Running AWR parsing pipeline..."})
        # Ensure worker command exists
        if not RUN_MULTI.exists():
            progress_status.update({"percent": 100, "message": "❌ Worker script not found."})
            print("❌ Worker script not found at", RUN_MULTI)
            return

        # Call the worker script (it should read from uploads/ and write to outputs/)
        try:
            cmd = ["python3", str(RUN_MULTI), cloud.lower()]
            subprocess.run(cmd, cwd=str(WORKER), check=True)
        except subprocess.CalledProcessError as e:
            progress_status.update({"percent": 100, "message": f"❌ Pipeline failed: {e}"})
            print("❌ Pipeline failed:", e)
            return

        # Verify summary.json
        summary_json = OUTPUTS / "summary.json"
        if summary_json.exists():
            try:
                data = json.loads(summary_json.read_text())
                progress_status.update({"percent": 100, "message": f"✅ Completed: {len(data)} DBs processed."})
                print(f"✅ Analysis complete: {len(data)} DBs processed.")
                # 🟢 Append to report history for admin reporting
                append_to_history(cloud, summary_json, user_email=user_email, job_type="upload")
            except Exception:
                progress_status.update({"percent": 100, "message": "✅ Completed (summary read error)."})
        else:
            progress_status.update({"percent": 100, "message": "❌ summary.json not found."})

    except Exception as e:
        progress_status.update({"percent": 100, "message": f"❌ Error: {str(e)}"})
        print("❌ run_analysis_task error:", e)


@app.post("/analyze")
async def analyze(background_tasks: BackgroundTasks, cloud: str = Form("azure"), user_email: str = Form("unknown")):
    progress_status.update({"percent": 0, "message": "Queued..."})
    background_tasks.add_task(run_analysis_task, cloud, user_email)
    return JSONResponse({"status": "started", "message": "Analysis started in background."})



@app.get("/progress")
def get_progress():
    """Check progress of current background task."""
    return JSONResponse(progress_status)


# ---------------------------------------------------------------------
# 📥 DOWNLOAD ENDPOINTS
# ---------------------------------------------------------------------
@app.get("/download/xlsx")
def download_xlsx():
    path = OUTPUTS / "summary.xlsx"
    if path.exists():
        return FileResponse(path, filename="summary.xlsx")
    return JSONResponse({"status": "error", "message": "summary.xlsx not found"})


@app.get("/download/ppt")
def download_ppt():
    path = OUTPUTS / "summary.pptx"
    if path.exists():
        return FileResponse(path, filename="summary.pptx")
    return JSONResponse({"status": "error", "message": "summary.pptx not found"})


@app.get("/download/zip")
def download_zip():
    zip_path = OUTPUTS / "final_excels.zip"
    # create zip on demand (overwrite if exists)
    try:
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w") as z:
            for file in OUTPUTS.glob("final_analysis_*.xlsx"):
                z.write(file, file.name)
        return FileResponse(zip_path, filename="final_excels.zip")
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


# ---------------------------------------------------------------------
# 🔐 USER AUTHENTICATION & LICENSE MANAGEMENT
# ---------------------------------------------------------------------
DB_PATH = PROJECT_ROOT / "backend" / "licenses.db"
SECRET_KEY = b"russ_secret_key_2025"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password_hash TEXT,
        license_key TEXT,
        expires TEXT
    )
    """)
    conn.commit()
    conn.close()
init_db()

def generate_license(email):
    expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
    token = base64.urlsafe_b64encode(
        hmac.new(SECRET_KEY, f"{email}|{expires}".encode(), hashlib.sha256).digest()
    ).decode().rstrip("=")
    return token, expires


@app.post("/api/register")
def register_user(name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        if cur.fetchone():
            conn.close()
            return JSONResponse({"status": "error", "message": "Email already registered"}, status_code=400)

        pw_hash = pwd_context.hash(password[:72])
        license_key, expires = generate_license(email)
        cur.execute("""
            INSERT INTO users (name, email, password_hash, license_key, expires)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, pw_hash, license_key, expires))
        conn.commit()
        conn.close()

        return JSONResponse({
            "status": "success",
            "message": "Registration successful! Please log in.",
            "license_key": license_key,
            "expires": expires
        }, status_code=200)

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.post("/api/login")
def login_user(email: str = Form(...), password: str = Form(...)):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name, password_hash, license_key, expires FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return JSONResponse({"status": "error", "message": "User not found"}, status_code=400)

        name, db_hash, license_key, expires = row

        if not pwd_context.verify(password[:72], db_hash):
            return JSONResponse({"status": "error", "message": "Incorrect password"}, status_code=400)

        if datetime.utcnow() > datetime.fromisoformat(expires):
            return JSONResponse({"status": "error", "message": "License expired"}, status_code=403)

        return JSONResponse({
            "status": "success",
            "message": "Login successful!",
            "name": name,
            "email": email,
            "license_key": license_key,
            "expires": expires
        }, status_code=200)

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    
# ---------------------------------------------------------------------
# 👑 ADMIN — USER MANAGEMENT API
# ---------------------------------------------------------------------
@app.get("/api/admin/users")
def admin_get_users(email: str = Query(...), password: str = Query(...)):
    """Admin-only: fetch list of all users."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # ✅ Validate admin login
        cur.execute("SELECT password_hash FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=403, detail="Admin not found")

        if not pwd_context.verify(password[:72], row[0]):
            conn.close()
            raise HTTPException(status_code=403, detail="Invalid admin password")

        # ✅ In your system, ALL users with valid credentials are admins  
        # (Since you don't have an is_admin column; no role check required)

        # ✅ Fetch all users
        cur.execute("SELECT id, name, email FROM users")
        users = cur.fetchall()
        conn.close()

        return {"users": [
            {"id": u[0], "name": u[1], "email": u[2], "is_admin": True}
            for u in users
        ]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------
# 📈 REPORTING API (For Admin Reports Tab)
# ---------------------------------------------------------------------
@app.get("/api/reports")
def get_reports(
    email: Optional[str] = None,
    cloud: Optional[str] = None,
    job_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Return flattened historical report entries for admin analytics (auto-detects global + per-user history)."""
    rows = []

    try:
        # -----------------------------
        # 1️⃣ Load global history.json
        # -----------------------------
        global_history = load_history()

        # -----------------------------
        # 2️⃣ Load per-user folder(s) if exist
        # -----------------------------
        if HISTORY_DIR.exists():
            if email:
                # specific user requested
                user_data = load_user_history(email)
                global_history.extend(user_data)
            else:
                # all users
                for user_folder in HISTORY_DIR.glob("*"):
                    if user_folder.is_dir():
                        user_email = user_folder.name.replace("_at_", "@")
                        user_data = load_user_history(user_email)
                        global_history.extend(user_data)

        # -----------------------------
        # 3️⃣ Flatten + filter results
        # -----------------------------
        for record in global_history:
            ts = record.get("timestamp")
            user_email_val = record.get("user_email", "unknown")
            cloud_val = record.get("cloud", "-")
            job_type_val = record.get("job_type", "-")

            # meta-level filters
            if email and user_email_val != email:
                continue
            if cloud and cloud_val.lower() != cloud.lower():
                continue
            if job_type and job_type_val.lower() != job_type.lower():
                continue
            if start_date and ts and ts < start_date:
                continue
            if end_date and ts and ts > end_date:
                continue

            # flatten DB entries
            for e in record.get("entries", []):
                rows.append({
                    "timestamp": ts,
                    "user_email": user_email_val,
                    "cloud": cloud_val,
                    "source": e.get("Source", "-"),
                    "vcpus": e.get("Estimated vCPUs", "-"),
                    "memory": e.get("Memory (GB)", "-"),
                    "iops": e.get("Total IOPS", "-"),
                    "throughput": e.get("Throughput (MB/s)", "-"),
                    "recommended_vm": e.get("Recommended VM", "-"),
                    "vm_vcpus": e.get("VM vCPUs", "-"),
                    "vm_memory": e.get("VM Memory (GB)", "-"),
                    "category": e.get("Category", "-"),
                    "monthly_cost": e.get("Monthly Cost (USD)", "-")
                })

        print(f"📊 get_reports → returning {len(rows)} records (after filters)")
        return JSONResponse({"reports": rows})

    except Exception as e:
        print(f"❌ Error in get_reports: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ---------------------------------------------------------------------
# 🔄 Append reports automatically after analysis completes
# ---------------------------------------------------------------------
def append_to_history(cloud: str, summary_path: Path, user_email: str = "unknown", job_type: str = "upload"):
    """Appends summary data with metadata to history.json."""
    try:
        if not summary_path.exists():
            print("⚠️ summary.json not found — skipping history append")
            return

        data = json.loads(summary_path.read_text())
        history_path = OUTPUTS / "history.json"
        history = []

        if history_path.exists():
            try:
                history = json.loads(history_path.read_text())
            except Exception:
                history = []

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_email": user_email,
            "cloud": cloud,
            "job_type": job_type,
            "entries": data
        }
        history.append(entry)

        with history_path.open("w") as f:
            json.dump(history, f, indent=2)

        print(f"✅ Added {len(data)} entries to history.json")
    except Exception as e:
        print("❌ Failed to append to history.json:", e)


# ---------------------------------------------------------------------
# 🚀 DEV RUNNER
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
