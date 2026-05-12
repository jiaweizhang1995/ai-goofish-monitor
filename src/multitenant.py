"""
Workspace-token multi-tenancy bolt-on.

Public ops-hub deploy at goofish.lemonation.cloud is multi-user. Each visitor gets
their own isolated workspace, identified by a token cookie. xianyu cookie state
files, tasks, and AI account names are scoped per workspace.

Single-file shim — minimal blast radius on upstream code. Tasks filter via
context-var; account files via path prefix; auto-provision workspace on first
visit; middleware blocks unauth'd /api/* and /ws/*.
"""
from __future__ import annotations

import contextvars
import hashlib
import os
import re
import secrets
import time
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from src.infrastructure.persistence.sqlite_connection import sqlite_connection


WS_COOKIE = "gf_ws_token"
WS_HEADER = "x-workspace-token"

# Context-var so deep code (repositories, services) can read current workspace
# without changing every signature.
_current_workspace_id: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "_current_workspace_id", default=None
)


def current_workspace_id() -> Optional[int]:
    return _current_workspace_id.get()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Schema bootstrap (extends sqlite_connection.init_schema)
# ---------------------------------------------------------------------------

def ensure_workspace_schema() -> None:
    """Create workspaces table + workspace_id column on tasks. Idempotent."""
    with sqlite_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workspaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash TEXT UNIQUE NOT NULL,
                label TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        # workspace_id on tasks
        cols = [r[1] for r in conn.execute("PRAGMA table_info(tasks)").fetchall()]
        if "workspace_id" not in cols:
            conn.execute(
                "ALTER TABLE tasks ADD COLUMN workspace_id INTEGER"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_workspace ON tasks(workspace_id)")
        # workspace_id on result_items + price_snapshots (best-effort scoping)
        for table in ("result_items", "price_snapshots"):
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if "workspace_id" not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN workspace_id INTEGER")
        conn.commit()


def create_workspace(label: str = "") -> tuple[int, str]:
    """Create a workspace; returns (workspace_id, raw_token). Token shown once."""
    token = secrets.token_urlsafe(24)
    with sqlite_connection() as conn:
        cur = conn.execute(
            "INSERT INTO workspaces (token_hash, label, created_at) VALUES (?, ?, ?)",
            (
                _hash_token(token),
                (label or "").strip()[:64],
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            ),
        )
        ws_id = cur.lastrowid
        conn.commit()
    return ws_id, token


def lookup_workspace(token: str) -> Optional[tuple[int, str]]:
    if not token:
        return None
    with sqlite_connection() as conn:
        row = conn.execute(
            "SELECT id, label FROM workspaces WHERE token_hash = ?",
            (_hash_token(token),),
        ).fetchone()
    if not row:
        return None
    return int(row[0]), row[1] or ""


# ---------------------------------------------------------------------------
# Path / filename scoping helpers
# ---------------------------------------------------------------------------

_ACCOUNT_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,50}$")


def scoped_account_filename(workspace_id: int, raw_name: str) -> str:
    """Translate a user-facing account name to its on-disk filename.

    Per-workspace prefix prevents cross-workspace collisions and listing leaks.
    """
    return f"ws{workspace_id}__{raw_name}.json"


def is_filename_in_workspace(workspace_id: int, filename: str) -> bool:
    return filename.startswith(f"ws{workspace_id}__") and filename.endswith(".json")


def strip_workspace_prefix(filename: str) -> str:
    """Inverse of scoped_account_filename — return user-facing name."""
    base = filename[:-5] if filename.endswith(".json") else filename
    if "__" in base:
        prefix, _, rest = base.partition("__")
        if prefix.startswith("ws") and prefix[2:].isdigit():
            return rest
    return base


# ---------------------------------------------------------------------------
# FastAPI middleware
# ---------------------------------------------------------------------------

# Paths that should NOT require a workspace cookie (public).
_PUBLIC_EXACT = {
    "/",
    "/health",
    "/auth/status",            # legacy admin gate, kept for compatibility
    "/auth/logout",
    "/api/workspace/auto-create",
    "/api/workspace/me",
}
_PUBLIC_PREFIXES = ("/assets/", "/static/", "/favicon")


def _is_public(path: str) -> bool:
    if path in _PUBLIC_EXACT:
        return True
    if path.startswith(_PUBLIC_PREFIXES):
        return True
    # SPA history routes: anything not /api/* and not /ws/* is the SPA shell.
    if not path.startswith("/api/") and not path.startswith("/ws"):
        return True
    return False


async def workspace_middleware(request: Request, call_next):
    """Require a valid workspace token on /api/* and /ws/*.

    Auto-provisions a workspace on first visit to / so the SPA "just works".
    """
    path = request.url.path

    # Resolve workspace from cookie or header (cookies preferred for browsers).
    token = request.cookies.get(WS_COOKIE) or request.headers.get(WS_HEADER)
    ws = lookup_workspace(token) if token else None

    new_token: Optional[str] = None
    if ws is None and path == "/":
        # First-visit auto-provision: SPA shell GET. Mint a workspace + set cookie.
        ws_id, new_token = create_workspace(label="auto")
        ws = (ws_id, "auto")

    if ws is not None:
        ws_id = ws[0]
        token_var = _current_workspace_id.set(ws_id)
    else:
        token_var = None

    try:
        if not _is_public(path) and ws is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "工作区未识别，请刷新页面或重新登录"},
            )

        response: Response = await call_next(request)

        if new_token:
            # 365-day cookie. HttpOnly so XSS in SPA can't exfiltrate it.
            # SameSite=Lax so the cookie survives top-level navigations.
            response.set_cookie(
                WS_COOKIE,
                new_token,
                max_age=60 * 60 * 24 * 365,
                httponly=True,
                samesite="lax",
                secure=False,  # Caddy terminates TLS; backend sees HTTP.
            )
        return response
    finally:
        if token_var is not None:
            _current_workspace_id.reset(token_var)


# ---------------------------------------------------------------------------
# Routes (mounted by app.py)
# ---------------------------------------------------------------------------

def register_routes(app) -> None:
    from fastapi import APIRouter
    from pydantic import BaseModel

    r = APIRouter(prefix="/api/workspace", tags=["workspace"])

    class _UseBody(BaseModel):
        token: str

    @r.post("/auto-create")
    async def auto_create(response: Response):
        ws_id, token = create_workspace(label="auto")
        response.set_cookie(
            WS_COOKIE, token,
            max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax",
        )
        return {"workspace_id": ws_id, "token": token}

    @r.post("/use")
    async def use_token(body: _UseBody, response: Response):
        ws = lookup_workspace(body.token)
        if ws is None:
            return JSONResponse(status_code=401, content={"detail": "Token 无效"})
        response.set_cookie(
            WS_COOKIE, body.token,
            max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax",
        )
        return {"workspace_id": ws[0], "label": ws[1]}

    @r.get("/me")
    async def me(request: Request):
        token = request.cookies.get(WS_COOKIE) or request.headers.get(WS_HEADER)
        ws = lookup_workspace(token) if token else None
        if ws is None:
            return JSONResponse(status_code=401, content={"authenticated": False})
        return {"authenticated": True, "workspace_id": ws[0], "label": ws[1]}

    app.include_router(r)
