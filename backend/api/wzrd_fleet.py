"""WZRD fleet coordination status endpoint."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter()

HERMES_HOME = Path(os.environ.get("HERMES_HOME") or os.path.expanduser("~/.hermes"))


def _load_fleet_status() -> dict[str, Any]:
    """Load fleet coordination status."""
    status: dict[str, Any] = {
        "coordinator": "hermes-gateway",
        "processes": [],
        "platforms": {},
        "handoffs": [],
        "status": "unknown",
    }

    # Load processes.json
    proc_file = HERMES_HOME / "processes.json"
    if proc_file.exists():
        try:
            procs = json.loads(proc_file.read_text())
            if isinstance(procs, list):
                status["processes"] = procs
                status["process_count"] = len(procs)
        except (json.JSONDecodeError, OSError):
            pass

    # Load gateway_state.json for platform status
    gw_file = HERMES_HOME / "gateway_state.json"
    if gw_file.exists():
        try:
            gw = json.loads(gw_file.read_text())
            status["gateway_pid"] = gw.get("pid")
            status["gateway_state"] = gw.get("gateway_state", "unknown")
            platforms = gw.get("platforms", {})
            status["platforms"] = {}
            for pname, pdata in platforms.items():
                if isinstance(pdata, dict):
                    status["platforms"][pname] = {
                        "state": pdata.get("state", "unknown"),
                        "error": pdata.get("error_message"),
                    }
        except (json.JSONDecodeError, OSError):
            pass

    # Check handoffs directory
    handoffs_dir = HERMES_HOME / "handoffs"
    if handoffs_dir.exists():
        handoffs = []
        for f in sorted(handoffs_dir.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                handoffs.append(f.name)
        status["handoffs"] = handoffs
        status["handoff_count"] = len(handoffs)

    # Check night_work directory
    night_work_dir = HERMES_HOME / "night_work"
    if night_work_dir.exists():
        tasks = []
        for f in sorted(night_work_dir.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                tasks.append(f.name)
        status["night_work_tasks"] = tasks

    # Determine overall fleet status
    gw_state = status.get("gateway_state", "unknown")
    proc_count = status.get("process_count", 0)
    if gw_state == "running" or proc_count > 0:
        status["status"] = "active"
    elif gw_state == "stopped":
        status["status"] = "stopped"
    else:
        status["status"] = gw_state

    return status


@router.get("/wzrd/fleet")
async def get_fleet():
    """Get fleet coordination status."""
    return _load_fleet_status()
