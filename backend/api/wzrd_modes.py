"""WZRD mode management endpoints."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

HERMES_HOME = Path(os.environ.get("HERMES_HOME") or os.path.expanduser("~/.hermes"))
MODES_DIR = HERMES_HOME / "modes"
SESSION_MODE_FILE = HERMES_HOME / "session_mode.json"

# Try to import wzrd_modes tool
try:
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        "wzrd_modes",
        str(Path.home() / "wzrd-dev/hermes/hermes-agent/tools/wzrd_modes.py"),
    )
    if _spec and _spec.origin and Path(_spec.origin).exists():
        _mm = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mm)  # type: ignore
        mode_manager = _mm
    else:
        mode_manager = None
except Exception:
    mode_manager = None


def _available_modes() -> list[str]:
    """List available mode directories."""
    modes = []
    if MODES_DIR.exists():
        for d in sorted(MODES_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith("_") and not d.name.startswith("."):
                modes.append(d.name)
    return modes or [
        "architecture", "coding", "debugging", "documentation",
        "orchestration", "planning", "research", "testing",
    ]


def _current_mode() -> str:
    """Read current mode from session_mode.json."""
    if SESSION_MODE_FILE.exists():
        try:
            data = json.loads(SESSION_MODE_FILE.read_text())
            return data.get("mode", data.get("current_mode", "unknown"))
        except (json.JSONDecodeError, OSError):
            pass
    return "unknown"


@router.get("/wzrd/modes")
async def get_modes():
    """Get current mode and available modes."""
    available = _available_modes()
    current = _current_mode()

    # Build mode details
    mode_details = []
    for m in available:
        mode_dir = MODES_DIR / m
        config_file = mode_dir / "config.yaml" if mode_dir.exists() else None
        detail: dict[str, Any] = {
            "name": m,
            "active": m == current,
        }
        if config_file and config_file.exists():
            try:
                detail["config"] = config_file.read_text()[:2000]
            except OSError:
                pass
        mode_details.append(detail)

    return {
        "current_mode": current,
        "available_modes": mode_details,
    }


class SwitchModeRequest(BaseModel):
    mode: str


@router.put("/wzrd/modes")
async def switch_mode(body: SwitchModeRequest):
    """Switch to a different mode."""
    available = _available_modes()
    if body.mode not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown mode '{body.mode}'. Available: {', '.join(available)}",
        )

    if mode_manager and hasattr(mode_manager, "switch_mode"):
        try:
            result = mode_manager.switch_mode(body.mode)
            return {"status": "switched", "mode": body.mode, "result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Fallback: write directly to session_mode.json
    SESSION_MODE_FILE.write_text(json.dumps({
        "mode": body.mode,
        "switched_at": __import__("datetime").datetime.now().isoformat(),
    }, indent=2))

    return {"status": "switched", "mode": body.mode}
