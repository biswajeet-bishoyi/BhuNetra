import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))
os.chdir(backend_dir)

port = int(os.environ.get("PORT", 8000))
print(f"[run_server] Starting uvicorn on http://127.0.0.1:{port} ...", flush=True)

import uvicorn
from main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
