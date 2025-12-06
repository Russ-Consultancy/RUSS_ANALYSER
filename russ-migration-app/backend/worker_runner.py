# backend/worker_runner.py
import subprocess
from pathlib import Path
from jobs import update_meta, Status
import shlex
import os

PYTHON = "python"  # adjust to your venv path if needed, e.g. "python3" or "/usr/local/bin/python3"

def run_job(job_id, job_dir: Path, input_files_dir: Path, analysis_template: Path, ppt_template: Path, client, cloud="azure"):
    """
    Worker runner to execute multi_analyze.py for AWS or Azure cloud AWR analysis.
    - client: client name (used for folder naming)
    - cloud: target cloud ("aws" or "azure")
    """
    try:
        update_meta(job_id, status=Status.RUNNING.value, message="🚀 Starting AWR worker for analysis")

        # ---------------------------------------------------------------------
        # 🧩 Prepare input directory
        # ---------------------------------------------------------------------
        worker_input = job_dir / "worker_input"
        worker_input.mkdir(exist_ok=True)

        for f in input_files_dir.iterdir():
            if f.suffix.lower() in [".html", ".htm"]:
                target = worker_input / f.name
                target.write_bytes(f.read_bytes())

        update_meta(job_id, message=f"✅ Uploaded {len(list(worker_input.glob('*.html')))} AWR files for processing")

        # ---------------------------------------------------------------------
        # 🧠 Define worker paths
        # ---------------------------------------------------------------------
        worker_base = Path("/app/worker") if Path("/app/worker").exists() else Path(__file__).resolve().parent / "worker"
        multi_analyze_script = worker_base / "multi_analyze.py"

        # ---------------------------------------------------------------------
        # 🏃 Run the analysis
        # ---------------------------------------------------------------------
        cmd = [
            PYTHON,
            str(multi_analyze_script),
            cloud.lower()  # pass cloud argument ("aws" or "azure")
        ]

        update_meta(job_id, message="🧩 Running Multi-Analysis: " + " ".join(shlex.quote(x) for x in cmd))
        subprocess.check_call(cmd, cwd=str(worker_base))

        # ---------------------------------------------------------------------
        # ✅ Success
        # ---------------------------------------------------------------------
        outputs_dir = worker_base.parent / "outputs"
        if outputs_dir.exists():
            update_meta(
                job_id,
                status=Status.DONE.value,
                message=f"✅ Completed AWR analysis for {client} on {cloud.upper()}. Results saved in {outputs_dir}",
            )
        else:
            update_meta(job_id, status=Status.DONE.value, message="✅ Completed (no outputs folder found)")

    except subprocess.CalledProcessError as e:
        update_meta(job_id, status=Status.FAILED.value, message=f"❌ Worker failed: {e}")
    except Exception as e:
        update_meta(job_id, status=Status.FAILED.value, message=f"⚠️ Unexpected error: {str(e)}")
