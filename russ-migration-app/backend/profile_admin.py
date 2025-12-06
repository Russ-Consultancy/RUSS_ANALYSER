# backend/profile_admin.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import sqlite3
import os
import shutil
import time
from passlib.context import CryptContext

router = APIRouter(prefix="/api", tags=["profile_admin"])


HERE = Path(__file__).resolve().parent
BASE = HERE.parent  # 👈 go up from backend/ to project root
DB_PATH = BASE / "backend" / "licenses.db"

# Use the same uploads dir that app.py serves
UPLOADS = BASE / "uploads"
PROFILES_DIR = UPLOADS / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def hash_password(password):
    return pwd_context.hash(password)

def migrate_add_columns_if_missing():
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE users ADD COLUMN profile_image TEXT;")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0;")
    except Exception:
        pass
    conn.commit()
    conn.close()

migrate_add_columns_if_missing()

def require_auth(email: str = None, password: str = None, license_key: str = None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if email:
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
    elif license_key:
        cur.execute("SELECT * FROM users WHERE license_key=?", (license_key,))
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Email or license key required")

    user = cur.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if password:
        if not pwd_context.verify(password[:72], user["password_hash"]):
            raise HTTPException(status_code=401, detail="Incorrect password")
    elif license_key:
        if license_key != user["license_key"]:
            raise HTTPException(status_code=401, detail="Invalid license key")
    else:
        raise HTTPException(status_code=401, detail="Authentication required")

    return dict(user)

def require_admin_auth(email: str, password: str):
    user = require_auth(email=email, password=password)
    if int(user.get("is_admin", 0)) != 1:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

# -------------------- Profile Endpoints --------------------

@router.get("/profile")
def get_profile(email: str = None, password: str = None, license_key: str = None):
    user = require_auth(email=email, password=password, license_key=license_key)
    image_url = f"/uploads/profiles/{user['profile_image']}" if user.get("profile_image") else None
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "profile_image_url": image_url,
        "is_admin": int(user["is_admin"]) if "is_admin" in user.keys() else 0
    }

@router.post("/profile")
async def update_profile(
    email: str = Form(None),
    password: str = Form(None),
    license_key: str = Form(None),
    new_name: str = Form(None),
    new_email: str = Form(None),
    old_password: str = Form(None),
    new_password: str = Form(None)
):
    user = require_auth(email=email, password=password, license_key=license_key)
    conn = get_db_conn()
    cur = conn.cursor()

    updates = {}
    if new_name:
        updates["name"] = new_name.strip()
    if new_email:
        cur.execute("SELECT id FROM users WHERE email=? AND id!=?", (new_email, user["id"]))
        if cur.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Email already in use")
        updates["email"] = new_email.strip()

    if new_password:
        if not old_password:
            conn.close()
            raise HTTPException(status_code=400, detail="Old password required")
        if not verify_password(old_password, user["password_hash"]):
            conn.close()
            raise HTTPException(status_code=401, detail="Old password incorrect")
        updates["password_hash"] = hash_password(new_password)

    if updates:
        set_parts = ", ".join([f"{k}=?" for k in updates.keys()])
        params = list(updates.values()) + [user["id"]]
        cur.execute(f"UPDATE users SET {set_parts} WHERE id=?", params)
        conn.commit()

    cur.execute("SELECT * FROM users WHERE id=?", (user["id"],))
    row = cur.fetchone()
    conn.close()

    profile_image = row["profile_image"] if "profile_image" in row.keys() else None
    image_url = f"/uploads/profiles/{profile_image}" if profile_image else None
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "profile_image_url": image_url,
        "is_admin": int(row["is_admin"]) if "is_admin" in row.keys() else 0
    }

@router.post("/profile/image")
async def upload_profile_image(
    email: str = Form(None),
    password: str = Form(None),
    license_key: str = Form(None),
    file: UploadFile = File(...)
):
    # Authenticate user
    user = require_auth(email=email, password=password, license_key=license_key)

    # Ensure directory exists
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    # Generate unique new filename
    filename = f"{user['id']}_{int(time.time())}_{file.filename}"
    dest_path = PROFILES_DIR / filename

    # Save new image file
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Delete old image (optional cleanup)
    old_filename = user.get("profile_image")
    if old_filename:
        old_path = PROFILES_DIR / old_filename
        if old_path.exists():
            try:
                old_path.unlink()
            except Exception as e:
                print(f"⚠️ Could not delete old image {old_filename}: {e}")

    # Update DB with new filename
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET profile_image=? WHERE id=?", (filename, user["id"]))
    conn.commit()
    conn.close()

    # Return new image URL (with cache-busting timestamp)
    image_url = f"/uploads/profiles/{filename}?v={int(time.time())}"

    return {"status": "ok", "profile_image_url": image_url}


# -------------------- Admin Endpoints --------------------

@router.get("/admin/users")
async def admin_list_users(email: str, password: str):
    _ = require_admin_auth(email, password)
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, is_admin, profile_image FROM users")
    rows = cur.fetchall()
    conn.close()
    users = []
    for r in rows:
        img_url = f"/uploads/profiles/{r['profile_image']}" if r["profile_image"] else None
        users.append({
            "id": r["id"],
            "name": r["name"],
            "email": r["email"],
            "is_admin": int(r["is_admin"] or 0),
            "profile_image_url": img_url
        })
    return {"users": users}

@router.post("/admin/users/{user_id}")
async def admin_update_user(
    user_id: int,
    admin_email: str = Form(...),
    admin_password: str = Form(...),
    name: str = Form(None),
    email: str = Form(None),
    is_admin: int = Form(None)
):
    _ = require_admin_auth(admin_email, admin_password)
    conn = get_db_conn()
    cur = conn.cursor()
    updates = {}
    if name is not None:
        updates["name"] = name.strip()
    if email is not None:
        cur.execute("SELECT id FROM users WHERE email=? AND id!=?", (email, user_id))
        if cur.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Email already in use")
        updates["email"] = email.strip()
    if is_admin is not None:
        updates["is_admin"] = int(is_admin)
    if updates:
        set_parts = ", ".join([f"{k}=?" for k in updates.keys()])
        params = list(updates.values()) + [user_id]
        cur.execute(f"UPDATE users SET {set_parts} WHERE id=?", params)
        conn.commit()
    conn.close()
    return {"status": "ok"}

@router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: int, admin_email: str, admin_password: str):
    _ = require_admin_auth(admin_email, admin_password)
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}
