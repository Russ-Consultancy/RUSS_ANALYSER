# backend/history_utils.py
import json
import shutil
from pathlib import Path
from datetime import datetime

# Base directories
OUTPUTS = Path(__file__).resolve().parent.parent / "outputs"
HISTORY_FILE = OUTPUTS / "history.json"
HISTORY_DIR = OUTPUTS / "history"  # future folder-based structure


# ===============================
# 🔹 Core JSON I/O Utilities
# ===============================
def load_history() -> list:
    """Load all history entries from the global history.json file."""
    try:
        if HISTORY_FILE.exists():
            with HISTORY_FILE.open("r") as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"⚠️ Failed to load history: {e}")
        return []


def save_history(data: list) -> None:
    """Save all history entries to the global history.json file."""
    try:
        OUTPUTS.mkdir(parents=True, exist_ok=True)
        with HISTORY_FILE.open("w") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Saved {len(data)} entries to history.json")
    except Exception as e:
        print(f"❌ Failed to save history: {e}")


def append_to_history_entry(entry: dict) -> None:
    """Append a new entry to history.json safely."""
    history = load_history()
    history.append(entry)
    save_history(history)


# ===============================
# 🔹 Optional Future Enhancements
# ===============================

def append_user_history(entry: dict, user_email: str, cloud: str = "unknown") -> None:
    """
    Append per-user report entry (Phase II ready).
    Creates outputs/history/<user_email>/<timestamp>_summary.json
    """
    try:
        if not user_email:
            user_email = "unknown_user"

        user_folder = HISTORY_DIR / user_email.replace("@", "_at_")
        user_folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_path = user_folder / f"{cloud}_{timestamp}_summary.json"

        with file_path.open("w") as f:
            json.dump(entry, f, indent=2)

        print(f"📦 Saved report for {user_email} → {file_path.name}")
    except Exception as e:
        print(f"❌ Failed to append user history: {e}")


def load_user_history(user_email: str) -> list:
    """
    Load all report files for a user (Phase II ready).
    Returns combined entries sorted by date.
    """
    try:
        user_folder = HISTORY_DIR / user_email.replace("@", "_at_")
        if not user_folder.exists():
            return []

        records = []
        for file in user_folder.glob("*.json"):
            with file.open("r") as f:
                data = json.load(f)
                data["_file"] = file.name
                records.append(data)

        # Sort by timestamp if available
        records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return records

    except Exception as e:
        print(f"⚠️ Failed to load user history: {e}")
        return []


def cleanup_old_user_history(user_email: str, keep_last_n: int = 10):
    """
    Automatically remove old report files, keeping only the most recent N runs.
    Useful when FTP uploads generate many auto-runs.
    """
    try:
        user_folder = HISTORY_DIR / user_email.replace("@", "_at_")
        if not user_folder.exists():
            return

        files = sorted(user_folder.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if len(files) > keep_last_n:
            for old_file in files[keep_last_n:]:
                old_file.unlink()
            print(f"🧹 Cleaned up {len(files) - keep_last_n} old reports for {user_email}")

    except Exception as e:
        print(f"⚠️ Cleanup failed for {user_email}: {e}")


def archive_user_history(user_email: str) -> Path:
    """
    Compresses a user’s history folder into a zip file (Phase III ready).
    Returns path to the created archive.
    """
    try:
        user_folder = HISTORY_DIR / user_email.replace("@", "_at_")
        if not user_folder.exists():
            print(f"⚠️ No history to archive for {user_email}")
            return None

        archive_path = OUTPUTS / f"{user_email.replace('@', '_at_')}_archive.zip"
        shutil.make_archive(str(archive_path).replace(".zip", ""), "zip", user_folder)
        print(f"📦 Archived history for {user_email} → {archive_path.name}")
        return archive_path

    except Exception as e:
        print(f"❌ Archiving failed for {user_email}: {e}")
        return None
