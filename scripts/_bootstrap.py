"""Shared bootstrap for the scripts in this directory.

Import this FIRST, before any `app.*` import. It loads `backend/.env`, puts
`backend/` on the path, and — for scripts that write — redirects the database
to a Neon test branch.

The ordering matters: `app.config.get_settings()` is `lru_cache`d and
`app.db.session` builds the engine at import time, so `DATABASE_URL` has to be
rewritten before anything under `app.` is imported. That is the whole reason
this lives in a module rather than inline in each script.
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parent.parent

load_dotenv(REPO / "backend" / ".env")
sys.path.insert(0, str(REPO / "backend"))


def _host_of(url: str) -> str:
    """Hostname only — never print a connection string, it carries the password."""
    try:
        return urlsplit(url).hostname or "(unparseable)"
    except ValueError:
        return "(unparseable)"


def describe_target() -> str:
    return _host_of(os.environ.get("DATABASE_URL", ""))


def use_test_branch(required: bool = True) -> None:
    """Point the app's database at `TEST_DATABASE_URL`.

    Call before importing anything from `app.`. Scripts that write rows should
    use this so they never touch the main branch: these scripts have no
    fixtures and no rollback, so every run leaves permanent data behind.

    Set `ALLOW_MAIN_DB=1` to bypass deliberately.
    """
    test_url = os.environ.get("TEST_DATABASE_URL", "").strip()

    if test_url:
        os.environ["DATABASE_URL"] = test_url
        print(f"[db] test branch → {_host_of(test_url)}\n")
        return

    if not required or os.environ.get("ALLOW_MAIN_DB"):
        print(
            f"[db] *** MAIN BRANCH → {describe_target()} ***\n"
            "[db] This script writes rows that cannot be rolled back.\n"
        )
        return

    sys.exit(
        "TEST_DATABASE_URL is not set.\n\n"
        "This script writes rows with no fixtures and no rollback, so it is\n"
        "pinned to a Neon test branch rather than the main database.\n\n"
        "Create a branch in the Neon console (Branches → New branch, from\n"
        "main), copy its POOLED connection string, and add it to backend/.env:\n\n"
        "    TEST_DATABASE_URL=postgresql://...-pooler...neon.tech/neondb?sslmode=require\n\n"
        "To run against the main database anyway: ALLOW_MAIN_DB=1 python <script>"
    )
