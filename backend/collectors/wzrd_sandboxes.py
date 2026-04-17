"""WZRD Sandbox Manager Collector.

Reads sandbox metadata from ~/.hermes/.wzrd/sandboxes.json and checks
Docker container status via subprocess. Does not depend on docker-py.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

from .utils import default_wzrd_hermes_dir, parse_timestamp
from .wzrd_models import SandboxInfo, SandboxesState


def _check_docker_available() -> bool:
    """Check if the docker CLI is available and the daemon is responsive."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def _inspect_container(container_id: str) -> str:
    """Check Docker container status. Returns 'running', 'stopped', or 'unknown'."""
    if not container_id:
        return "unknown"
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}", container_id],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            status = result.stdout.strip()
            return (
                status
                if status in ("running", "paused", "restarting", "exited", "dead")
                else "unknown"
            )
        return "stopped"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return "unknown"


def _load_sandboxes_json(path: Path) -> list[dict]:
    """Parse sandboxes.json and return a list of sandbox dicts."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "sandboxes" in data:
            return data["sandboxes"]
        return []
    except (json.JSONDecodeError, OSError):
        return []


def collect_sandboxes(hermes_dir: str | None = None) -> SandboxesState:
    """Collect WZRD sandbox state.

    Args:
        hermes_dir: Override for the Hermes home directory.

    Returns:
        SandboxesState with sandbox info. If Docker is unavailable,
        docker_available is False and all container statuses are 'unknown'.
    """
    base = Path(default_wzrd_hermes_dir(hermes_dir)) / ".wzrd"
    sandboxes_path = base / "sandboxes.json"
    docker_ok = _check_docker_available()

    raw = _load_sandboxes_json(sandboxes_path)
    sandboxes: list[SandboxInfo] = []

    for entry in raw:
        container_id = entry.get("container_id", "") or entry.get("containerId", "")
        if docker_ok and container_id:
            status = _inspect_container(container_id)
        else:
            status = "unknown" if not docker_ok else "stopped"

        created_raw = entry.get("created_at") or entry.get("createdAt")
        created_at = parse_timestamp(created_raw) if created_raw else None

        capabilities = entry.get("capabilities", [])
        if isinstance(capabilities, str):
            capabilities = [c.strip() for c in capabilities.split(",") if c.strip()]

        sandboxes.append(
            SandboxInfo(
                name=entry.get("name", "unnamed"),
                profile=entry.get("profile", ""),
                status=status,
                container_id=container_id,
                created_at=created_at,
                capabilities=capabilities if isinstance(capabilities, list) else [],
                project_dir=entry.get("project_dir", "") or entry.get("projectDir", ""),
            )
        )

    return SandboxesState(sandboxes=sandboxes, docker_available=docker_ok)
