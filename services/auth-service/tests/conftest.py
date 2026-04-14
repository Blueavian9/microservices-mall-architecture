"""Tests run with SKIP_DB=1 — no Postgres or NATS."""

from __future__ import annotations

import os

os.environ["SKIP_DB"] = "1"
os.environ["DATABASE_URL"] = "postgresql://u:p@127.0.0.1:5432/testdb"
os.environ["JWT_SECRET"] = "x" * 32
os.environ["JWT_REFRESH_SECRET"] = "y" * 32
os.environ["ALLOWED_ORIGINS"] = "http://localhost:5173"
os.environ.pop("NATS_URL", None)

from src.settings import get_settings

get_settings.cache_clear()
