import sys, os, importlib.util, uvicorn

# ✅ Explicitly add both /app and /app/backend to sys.path
for path in ["/app", "/app/backend"]:
    if path not in sys.path:
        sys.path.insert(0, path)

print("🐍 Working directory:", os.getcwd())
print("🔍 sys.path:", sys.path)
print("🔎 Checking if backend.app is importable...")

spec = importlib.util.find_spec("backend.app")
if spec is None:
    print("❌ Cannot find backend.app, aborting.")
    print("📂 Contents of /app/backend:", os.listdir("/app/backend"))
    raise SystemExit(1)
else:
    print("✅ Found backend.app, starting server...")

uvicorn.run("backend.app:app", host="0.0.0.0", port=8000)
