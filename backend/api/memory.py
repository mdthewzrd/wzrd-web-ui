"""Memory endpoints."""

from __future__ import annotations

import fcntl
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.collectors.memory import collect_memory
from backend.collectors.config import collect_config
from backend.collectors.utils import default_hermes_dir
from .serialize import to_dict

router = APIRouter()

ENTRY_DELIMITER = "\n§\n"


def _memory_path(target: str) -> Path:
    """Return the path for MEMORY.md or USER.md."""
    memories_dir = Path(default_hermes_dir()) / "memories"
    if target == "user":
        return memories_dir / "USER.md"
    return memories_dir / "MEMORY.md"


def _lock_path(target: str) -> Path:
    return _memory_path(target).with_suffix(".md.lock")


def _read_entries(target: str) -> list[str]:
    """Read and split entries from a memory file."""
    path = _memory_path(target)
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    return [p.strip() for p in content.split("§") if p.strip()]


def _write_entries(target: str, entries: list[str]) -> None:
    """Atomically write entries back to a memory file."""
    path = _memory_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = ENTRY_DELIMITER.join(entries) + "\n" if entries else ""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        os.replace(tmp, str(path))
    except Exception:
        os.close(fd) if not os.get_inheritable(fd) else None
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _with_lock(target: str, fn):
    """Execute fn while holding the memory file lock."""
    lock = _lock_path(target)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.touch(exist_ok=True)
    with open(lock, "r") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            return fn()
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


# ── Read ──────────────────────────────────────────────────────────────────────


@router.get("/memory")
async def get_memory():
    """Memory and user profile state."""
    config = collect_config()
    memory, user = collect_memory(
        memory_char_limit=config.memory_char_limit,
        user_char_limit=config.user_char_limit,
    )
    return {
        "memory": to_dict(memory),
        "user": to_dict(user),
    }


# ── Write ─────────────────────────────────────────────────────────────────────


class AddBody(BaseModel):
    target: str  # "memory" or "user"
    content: str


class EditBody(BaseModel):
    target: str
    old_text: str
    content: str


class DeleteBody(BaseModel):
    target: str
    old_text: str


@router.post("/memory")
async def add_entry(body: AddBody):
    """Add a new memory entry."""
    if body.target not in ("memory", "user"):
        raise HTTPException(400, "target must be 'memory' or 'user'")
    content = body.content.strip()
    if not content:
        raise HTTPException(400, "content cannot be empty")

    def do():
        entries = _read_entries(body.target)
        # Duplicate check
        for e in entries:
            if e == content:
                raise HTTPException(409, "Duplicate entry")
        entries.append(content)
        _write_entries(body.target, entries)
        return {"ok": True, "entry_count": len(entries)}

    return _with_lock(body.target, do)


@router.put("/memory")
async def edit_entry(body: EditBody):
    """Replace a memory entry (matched by old_text substring)."""
    if body.target not in ("memory", "user"):
        raise HTTPException(400, "target must be 'memory' or 'user'")
    new_content = body.content.strip()
    if not new_content:
        raise HTTPException(400, "content cannot be empty")

    def do():
        entries = _read_entries(body.target)
        matches = [i for i, e in enumerate(entries) if body.old_text in e]
        if not matches:
            raise HTTPException(404, "No entry matches old_text")
        if len(matches) > 1:
            raise HTTPException(409, "Multiple entries match — use a more specific old_text")
        entries[matches[0]] = new_content
        _write_entries(body.target, entries)
        return {"ok": True, "entry_count": len(entries)}

    return _with_lock(body.target, do)


@router.delete("/memory")
async def delete_entry(body: DeleteBody):
    """Remove a memory entry (matched by old_text substring)."""
    if body.target not in ("memory", "user"):
        raise HTTPException(400, "target must be 'memory' or 'user'")

    def do():
        entries = _read_entries(body.target)
        matches = [i for i, e in enumerate(entries) if body.old_text in e]
        if not matches:
            raise HTTPException(404, "No entry matches old_text")
        if len(matches) > 1:
            raise HTTPException(409, "Multiple entries match — use a more specific old_text")
        entries.pop(matches[0])
        _write_entries(body.target, entries)
        return {"ok": True, "entry_count": len(entries)}

    return _with_lock(body.target, do)
