"""File browser API endpoints for WZRD.dev Dashboard."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Safe root directory — all file operations are constrained to this directory
SAFE_ROOT = Path(
    os.environ.get("WZRDFILES_ROOT")
    or os.path.expanduser("~/wzrd-dev")
).resolve()


def _resolve_path(path_str: str) -> Path:
    """Resolve a path string relative to SAFE_ROOT, preventing traversal attacks."""
    # Expand ~ 
    expanded = os.path.expanduser(path_str)
    # If path starts with the safe root already, use it as-is
    candidate = Path(expanded)
    if not candidate.is_absolute():
        candidate = SAFE_ROOT / candidate
    resolved = candidate.resolve()
    # Ensure resolved path is within SAFE_ROOT
    if not str(resolved).startswith(str(SAFE_ROOT)):
        raise HTTPException(status_code=403, detail="Path traversal not allowed")
    return resolved


def _file_icon(name: str, is_dir: bool) -> str:
    """Return an emoji icon based on file extension."""
    if is_dir:
        return "📁"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    icons = {
        "py": "🐍",
        "js": "📜",
        "ts": "📜",
        "tsx": "📜",
        "jsx": "📜",
        "json": "📦",
        "yaml": "⚙️",
        "yml": "⚙️",
        "toml": "⚙️",
        "md": "📝",
        "txt": "📄",
        "sh": "🖥️",
        "bash": "🖥️",
        "css": "🎨",
        "html": "🌐",
        "sql": "🗃️",
        "db": "🗃️",
        "log": "📋",
        "env": "🔒",
        "png": "🖼️",
        "jpg": "🖼️",
        "svg": "🖼️",
        "gif": "🖼️",
    }
    return icons.get(ext, "📄")


def _scan_dir(path: Path, depth: int = 0, max_depth: int = 3) -> Dict[str, Any]:
    """Recursively scan a directory and return a tree structure."""
    rel = str(path.relative_to(SAFE_ROOT)) if path != SAFE_ROOT else "."
    name = path.name if path != SAFE_ROOT else SAFE_ROOT.name
    is_dir = path.is_dir()

    node: Dict[str, Any] = {
        "name": name,
        "path": rel,
        "icon": _file_icon(name, is_dir),
        "is_dir": is_dir,
    }

    if is_dir and depth < max_depth:
        children: List[Dict[str, Any]] = []
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            entries = []
        for entry in entries:
            # Skip hidden files/dirs and __pycache__
            if entry.name.startswith(".") or entry.name == "__pycache__" or entry.name == "node_modules":
                continue
            try:
                children.append(_scan_dir(entry, depth + 1, max_depth))
            except (PermissionError, OSError):
                continue
        node["children"] = children
    elif is_dir:
        node["children"] = None  # Indicates there are more items (lazy-loadable)

    if not is_dir:
        try:
            node["size"] = path.stat().st_size
        except OSError:
            node["size"] = 0

    return node


@router.get("/files/tree")
async def get_tree(path: str = Query(".", description="Path relative to safe root")):
    """Get directory tree structure."""
    try:
        resolved = _resolve_path(path)
    except HTTPException:
        raise
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    if not resolved.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")
    return _scan_dir(resolved)


@router.get("/files/read")
async def read_file(path: str = Query(..., description="File path relative to safe root")):
    """Read file contents."""
    try:
        resolved = _resolve_path(path)
    except HTTPException:
        raise
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if resolved.is_dir():
        raise HTTPException(status_code=400, detail="Path is a directory")
    # Limit file size to 2MB
    size = resolved.stat().st_size
    if size > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 2MB)")
    try:
        content = resolved.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Read error: {e}")
    return {
        "path": str(resolved.relative_to(SAFE_ROOT)),
        "content": content,
        "size": size,
        "name": resolved.name,
    }


class WriteRequest(BaseModel):
    path: str
    content: str


@router.post("/files/write")
async def write_file(req: WriteRequest):
    """Write file contents."""
    try:
        resolved = _resolve_path(req.path)
    except HTTPException:
        raise
    # Ensure parent directory exists
    resolved.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Atomic write via temp file
        import tempfile
        fd, tmp = tempfile.mkstemp(dir=str(resolved.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(req.content)
            os.replace(tmp, str(resolved))
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Write error: {e}")
    return {"status": "ok", "path": str(resolved.relative_to(SAFE_ROOT))}


class MkdirRequest(BaseModel):
    path: str


@router.post("/files/mkdir")
async def mkdir(req: MkdirRequest):
    """Create a directory."""
    try:
        resolved = _resolve_path(req.path)
    except HTTPException:
        raise
    if resolved.exists():
        raise HTTPException(status_code=409, detail="Path already exists")
    try:
        resolved.mkdir(parents=True, exist_ok=False)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Mkdir error: {e}")
    return {"status": "ok", "path": str(resolved.relative_to(SAFE_ROOT))}
