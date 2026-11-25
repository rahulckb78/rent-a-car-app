"""Run the API (uvicorn --reload) and the Angular dev server together. Ctrl+C stops both."""
import os
import signal
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
port = os.environ.get("PORT", "8000")
env = {**os.environ, "NG_CLI_ANALYTICS": "false", "API_PORT": port}

procs = [
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", port],
        cwd=root / "backend",
        env=env,
    ),
    subprocess.Popen(["npm", "start"], cwd=root / "frontend", env=env),
]


def stop(*_):
    for p in procs:
        if p.poll() is None:
            p.terminate()


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)
code = 0
for p in procs:
    code = p.wait() or code
    stop()
sys.exit(code)
