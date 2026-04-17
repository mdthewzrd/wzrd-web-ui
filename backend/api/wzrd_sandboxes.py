"""WZRD sandbox management endpoints."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

HERMES_HOME = Path(os.environ.get("HERMES_HOME") or os.path.expanduser("~/.hermes"))
SANDBOX_DIR = HERMES_HOME / "sandboxes"
SANDBOX_JSON = SANDBOX_DIR / "sandboxes.json"

# Try to import the sandbox manager tool
try:
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        "wzrd_sandbox_manager",
        str(Path.home() / "wzrd-dev/hermes/hermes-agent/tools/wzrd_sandbox_manager.py"),
    )
    if _spec and _spec.origin and Path(_spec.origin).exists():
        _sm = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_sm)  # type: ignore
        sandbox_manager = _sm
    else:
        sandbox_manager = None
except Exception:
    sandbox_manager = None


def _load_sandboxes() -> list[dict[str, Any]]:
    """Load sandbox data from sandboxes.json."""
    if SANDBOX_JSON.exists():
        try:
            return json.loads(SANDBOX_JSON.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    # Fallback: scan directory
    sandboxes = []
    if SANDBOX_DIR.exists():
        for d in sorted(SANDBOX_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith("_") and not d.name.startswith("."):
                sandboxes.append({
                    "name": d.name,
                    "path": str(d),
                    "status": "unknown",
                })
    return sandboxes


def _docker_status(name: str) -> dict[str, Any]:
    """Check Docker container status for a sandbox."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}", name],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return {"docker_status": result.stdout.strip(), "running": result.stdout.strip() == "running"}
        return {"docker_status": "not_found", "running": False}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {"docker_status": "unknown", "running": False}


@router.get("/wzrd/sandboxes")
async def list_sandboxes():
    """List all sandboxes with Docker status."""
    sandboxes = _load_sandboxes()
    for sb in sandboxes:
        sb.update(_docker_status(sb.get("name", "")))
    return {"sandboxes": sandboxes}


class CreateSandboxRequest(BaseModel):
    name: str
    profile: str = "default"
    project_dir: Optional[str] = None


@router.post("/wzrd/sandboxes")
async def create_sandbox(body: CreateSandboxRequest):
    """Create a new sandbox."""
    if sandbox_manager and hasattr(sandbox_manager, "create_sandbox"):
        try:
            result = sandbox_manager.create_sandbox(
                name=body.name,
                profile=body.profile,
                project_dir=body.project_dir,
            )
            return {"status": "created", "sandbox": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Fallback: just record it
    sandboxes = _load_sandboxes()
    if any(sb.get("name") == body.name for sb in sandboxes):
        raise HTTPException(status_code=409, detail=f"Sandbox '{body.name}' already exists")

    new_sb = {
        "name": body.name,
        "profile": body.profile,
        "project_dir": body.project_dir,
        "status": "created",
        "docker_status": "not_started",
    }
    sandboxes.append(new_sb)

    # Persist
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    SANDBOX_JSON.write_text(json.dumps(sandboxes, indent=2))

    return {"status": "created", "sandbox": new_sb}


@router.get("/wzrd/sandboxes/{name}")
async def get_sandbox(name: str):
    """Get sandbox details."""
    sandboxes = _load_sandboxes()
    sb = next((s for s in sandboxes if s.get("name") == name), None)
    if not sb:
        raise HTTPException(status_code=404, detail=f"Sandbox '{name}' not found")
    sb.update(_docker_status(name))
    return sb


class ExecRequest(BaseModel):
    command: str
    timeout: int = 30


@router.post("/wzrd/sandboxes/{name}/exec")
async def exec_in_sandbox(name: str, body: ExecRequest):
    """Execute a command in a sandbox."""
    if sandbox_manager and hasattr(sandbox_manager, "exec_in_sandbox"):
        try:
            result = sandbox_manager.exec_in_sandbox(
                name=name, command=body.command, timeout=body.timeout,
            )
            return {"output": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Fallback: docker exec
    try:
        result = subprocess.run(
            ["docker", "exec", name, "sh", "-c", body.command],
            capture_output=True, text=True, timeout=body.timeout,
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout[:10000],
            "stderr": result.stderr[:5000],
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Docker not available")


class InstallRequest(BaseModel):
    package: str
    manager: str = "pip"


@router.post("/wzrd/sandboxes/{name}/install")
async def install_package(name: str, body: InstallRequest):
    """Install a package in a sandbox."""
    if sandbox_manager and hasattr(sandbox_manager, "install_package"):
        try:
            result = sandbox_manager.install_package(
                name=name, package=body.package, manager=body.manager,
            )
            return {"status": "installed", "result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Fallback: docker exec pip/npm install
    cmd_map = {
        "pip": f"pip install {body.package}",
        "npm": f"npm install {body.package}",
        "apt": f"apt-get install -y {body.package}",
    }
    cmd = cmd_map.get(body.manager, f"pip install {body.package}")

    try:
        result = subprocess.run(
            ["docker", "exec", name, "sh", "-c", cmd],
            capture_output=True, text=True, timeout=120,
        )
        return {
            "status": "installed" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:5000],
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Install timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Docker not available")


@router.delete("/wzrd/sandboxes/{name}")
async def delete_sandbox(name: str):
    """Delete a sandbox."""
    if sandbox_manager and hasattr(sandbox_manager, "delete_sandbox"):
        try:
            sandbox_manager.delete_sandbox(name=name)
            return {"status": "deleted", "name": name}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Fallback: docker rm + remove from json
    try:
        subprocess.run(
            ["docker", "rm", "-f", name],
            capture_output=True, text=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    sandboxes = _load_sandboxes()
    sandboxes = [sb for sb in sandboxes if sb.get("name") != name]
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    SANDBOX_JSON.write_text(json.dumps(sandboxes, indent=2))

    return {"status": "deleted", "name": name}
