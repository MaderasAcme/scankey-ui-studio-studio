#!/usr/bin/env bash
set -Eeuo pipefail
: "${PORT:=8080}"

# Intento de autodetección simple: busca "X = FastAPI("
detect_app() {
python3 - <<'PY'
import re, pathlib, sys
root = pathlib.Path(".")
for p in root.rglob("*.py"):
    try:
        t = p.read_text("utf-8", errors="ignore")
    except Exception:
        continue
    m = re.search(r'^\s*([A-Za-z_]\w*)\s*=\s*FastAPI\(', t, re.M)
    if m:
        mod = str(p.with_suffix("")).replace("/", ".").lstrip(".")
        print(f"{mod}:{m.group(1)}")
        sys.exit(0)
print("main:app")
PY
}

APP_MODULE="${APP_MODULE:-$(detect_app)}"
echo "Starting APP_MODULE=$APP_MODULE on 0.0.0.0:${PORT}"
exec gunicorn -k uvicorn.workers.UvicornWorker -b "0.0.0.0:${PORT}" "$APP_MODULE"
