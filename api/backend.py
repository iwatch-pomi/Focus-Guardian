"""Vercel Python serverless function entry point.

Vercel rewrites /api/v1/* → this function.
The ASGI app receives the original path (e.g. /api/v1/snapshots),
which FastAPI matches via the router prefix "/api/v1".
"""

import os
import sys

# Make the repo root importable so `from backend.xxx import ...` works
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("IS_SERVERLESS", "true")

from backend.api.main import app  # noqa: E402  (must be after sys.path setup)
