from fastapi import APIRouter, Form, HTTPException
from datetime import datetime, timedelta
import hashlib, hmac, base64, sqlite3, os
from passlib.context import CryptContext
from pathlib import Path

router = APIRouter(prefix="/api")

DB_PATH = Path(__file__).parent / "licenses.db"
SECRET_KEY = b"russ_secret_key"  # change to secure value
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Init DB
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        mac TEXT,
        license_key TEXT,
        expires TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

def generate_license(username, mac):
    expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
    msg = f"{username}|{mac}|{expires}".encode()
    token = base64.urlsafe_b64encode(
        hmac.new(SECRET_KEY, msg, hashlib.sha256).digest()
    ).decode().strip("=")
    return token, expires

@router.post("/register")
def register(username: str = Form(...), password: str = Form(...), mac_address: str = Form(...)):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Username already exists")

    password_hash = pwd_context.hash(password)
    license_key, expires = generate_license(username, mac_address)
    cur.execute("INSERT INTO users (username, password_hash, mac, license_key, expires) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, mac_address, license_key, expires))
    conn.commit()
    conn.close()

    return {"username": username, "license_key": license_key, "expires": expires}

@router.post("/login")
def login(username: str = Form(...), password: str = Form(...), mac_address: str = Form(...)):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT username, password_hash, mac, license_key, expires FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=400, detail="User not found")

    db_user, db_hash, db_mac, db_license, db_expiry = row
    if not pwd_context.verify(password, db_hash):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if mac_address != db_mac:
        raise HTTPException(status_code=400, detail="Device MAC does not match")
    if datetime.utcnow() > datetime.fromisoformat(db_expiry):
        raise HTTPException(status_code=400, detail="License expired")

    return {"username": db_user, "license_key": db_license, "expires": db_expiry}
