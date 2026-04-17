"""WZRD PIV (Persistent Identity Vector) state endpoint."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter()

HERMES_HOME = Path(os.environ.get("HERMES_HOME") or os.path.expanduser("~/.hermes"))


def _load_piv_state() -> dict[str, Any]:
    """Load PIV state from various sources."""
    state: dict[str, Any] = {
        "status": "unknown",
        "identity": {},
        "pairing": {},
        "auth": {},
    }

    # Check auth.json
    auth_file = HERMES_HOME / "auth.json"
    if auth_file.exists():
        try:
            auth_data = json.loads(auth_file.read_text())
            state["auth"] = {
                "authenticated": bool(auth_data),
                "methods": list(auth_data.keys()) if isinstance(auth_data, dict) else [],
            }
        except (json.JSONDecodeError, OSError):
            pass

    # Check config.yaml for identity info
    config_file = HERMES_HOME / "config.yaml"
    if config_file.exists():
        try:
            text = config_file.read_text()
            state["config_exists"] = True
            # Extract agent name if present
            for line in text.splitlines():
                if line.startswith("name:"):
                    state["identity"]["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("agent_id:") or line.startswith("id:"):
                    state["identity"]["agent_id"] = line.split(":", 1)[1].strip()
        except OSError:
            pass

    # Check pairing directory
    pairing_dir = HERMES_HOME / "pairing"
    if pairing_dir.exists():
        pairs = []
        for f in pairing_dir.iterdir():
            if f.is_file() and f.suffix == ".json" and not f.name.startswith("_"):
                try:
                    data = json.loads(f.read_text())
                    pairs.append({"file": f.name, "data": data})
                except (json.JSONDecodeError, OSError):
                    pairs.append({"file": f.name, "error": "Could not parse"})
        state["pairing"] = {"active": len(pairs), "pairs": pairs}

    # Check USER.md for identity profile
    user_md = HERMES_HOME / "memories" / "USER.md"
    if user_md.exists():
        try:
            state["identity"]["user_profile"] = user_md.read_text()[:2000]
        except OSError:
            pass

    # Check MEMORY.md
    memory_md = HERMES_HOME / "memories" / "MEMORY.md"
    if memory_md.exists():
        try:
            content = memory_md.read_text()
            state["memory_size"] = len(content)
            state["memory_preview"] = content[:500]
        except OSError:
            pass

    # Determine overall status
    if state.get("auth", {}).get("authenticated"):
        state["status"] = "active"
    elif state.get("config_exists"):
        state["status"] = "configured"
    else:
        state["status"] = "uninitialized"

    return state


@router.get("/wzrd/piv")
async def get_piv():
    """Get current PIV (Persistent Identity Vector) state."""
    return _load_piv_state()
