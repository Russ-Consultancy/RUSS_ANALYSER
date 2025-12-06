from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from pathlib import Path
from typing import List
import shutil
import subprocess
import zipfile
import json
import os

# ---------------------------------------------------------------------
# ⚙️ Initialize FastAPI app
# ---------------------------------------------------------------------
app = FastAPI(title="RUSS Consultancy Migration Tool")

# ---------------------------------------------------------------------
# 📁 PATH SETUP
# ---------------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
FRONTEND = BASE / "frontend"
UPLOADS = BASE / "uploads"
OUTPUTS = BASE / "outputs"
WORKER = BASE / "worker"
RUN_MULTI = WORKER / "multi_analyze.py"

UPLOADS.mkdir(exist_ok=True)
OUTPUTS.mkdir(exist_ok=True)

# ---------------------------------------------------------------------
# 🧭 Serve static files (CSS, JS, logo, etc.)
# ---------------------------------------------------------------------
app.mount("/static", StaticFiles(directory=FRONTEND), name="frontend")
app.mount("/outputs", StaticFiles(directory=OUTPUTS), name="outputs")

# ---------------------------------------------------------------------
# 🏠 HOME ROUTE
# ---------------------------------------------------------------------
@app.get("/")
def home():
    """Serve upload page (index.html)."""
    html_path = FRONTEND / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(), status_code=200)
    return HTMLResponse("<h3>index.html not found in frontend folder</h3>", status_code=404)

# ---------------------------------------------------------------------
# 📊 DASHBOARD ROUTE
# ---------------------------------------------------------------------
@app.get("/dashboard.html")
def dashboard():
    """Serve dashboard page."""
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
    files: List[UploadFile] = File(...)
):
    """Upload AWR HTML reports to /uploads."""
    try:
        # Clear old uploads
        for f in UPLOADS.glob("*"):
            if f.is_file():
                f.unlink()

        # Save new files
        for file in files:
            dest = UPLOADS / file.filename
            with dest.open("wb") as f:
                shutil.copyfileobj(file.file, f)

        print(f"✅ Uploaded {len(files)} AWR files for {cloud}")
        return {"status": "uploaded", "count": len(files), "cloud": cloud}

    except Exception as e:
        print("❌ Upload failed:", str(e))
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------
# 🧠 ANALYZE ENDPOINT
# ---------------------------------------------------------------------
@app.post("/analyze")
def analyze(cloud: str = Form("azure")):
    """
    Run the AWR analysis pipeline (multi_analyze.py) for AWS or Azure.
    """
    try:
        print(f"⚙️ Running analysis for {cloud.upper()}...")

        # Cleanup old outputs
        for f in OUTPUTS.glob("*"):
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                shutil.rmtree(f)

        cmd = ["python3", str(RUN_MULTI), cloud.lower()]
        subprocess.run(cmd, cwd=str(WORKER), check=True)

        summary_json = OUTPUTS / "summary.json"
        if summary_json.exists():
            data = json.loads(summary_json.read_text())
            print(f"✅ Analysis complete: {len(data)} DBs processed.")
            return JSONResponse({"status": "ok", "cloud": cloud, "summary": data})
        else:
            return JSONResponse({"status": "error", "message": "summary.json not found"})

    except subprocess.CalledProcessError as e:
        return JSONResponse({"status": "error", "message": f"Pipeline failed: {e}"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

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
    with zipfile.ZipFile(zip_path, "w") as z:
        for file in OUTPUTS.glob("final_analysis_*.xlsx"):
            z.write(file, file.name)
    return FileResponse(zip_path, filename="final_excels.zip")

# ---------------------------------------------------------------------
# 🚀 DEV RUNNER
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
