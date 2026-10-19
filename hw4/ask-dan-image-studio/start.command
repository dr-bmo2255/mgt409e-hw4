#!/bin/bash
# Ask Dan Image Studio — double-click to launch (macOS). Opens http://127.0.0.1:8765
cd "$(dirname "$0")/backend" || exit 1
UV="$HOME/.local/bin/uv"; command -v uv >/dev/null && UV=uv
if [ ! -x .venv/bin/uvicorn ]; then "$UV" sync || exit 1; fi
if [ ! -f ../frontend/dist/index.html ] && command -v npm >/dev/null; then (cd ../frontend && npm install && npm run build); fi
(sleep 2; open "http://127.0.0.1:8765") &
exec .venv/bin/uvicorn app:app --host 127.0.0.1 --port 8765
