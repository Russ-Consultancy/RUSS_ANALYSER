"""
Run this once to ensure there is at least one admin user.
It finds the first user in the database (by id) and sets is_admin=1
if no admin currently exists.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "licenses.db"

def bootstrap_admin():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ensure column exists
    try:
        cur.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0;")
    except Exception:
        pass

    cur.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1;")
    count_admins = cur.fetchone()[0]

    if count_admins == 0:
        cur.execute("SELECT id, email FROM users ORDER BY id ASC LIMIT 1;")
        row = cur.fetchone()
        if row:
            first_id, email = row
            cur.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (first_id,))
            conn.commit()
            print(f"✅ Bootstrap complete: made {email} an admin user.")
        else:
            print("No users found — register one first.")
    else:
        print("Admin user(s) already exist, nothing changed.")
    conn.close()

if __name__ == "__main__":
    bootstrap_admin()
