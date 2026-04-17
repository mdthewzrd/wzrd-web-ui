"""WZRD agents endpoints."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()

HERMES_HOME = Path(os.environ.get("HERMES_HOME") or os.path.expanduser("~/.hermes"))
CHANNEL_DIR_FILE = HERMES_HOME / "channel_directory.json"
PROJECTS_DIR = HERMES_HOME / "hermes-agent"


def _discover_agents() -> list[dict[str, Any]]:
    """Discover agents from channel directory and project structure."""
    agents: list[dict[str, Any]] = []

    # From channel_directory.json
    if CHANNEL_DIR_FILE.exists():
        try:
            data = json.loads(CHANNEL_DIR_FILE.read_text())
            platforms = data.get("platforms", {})
            updated_at = data.get("updated_at")
            for platform_name, channels in platforms.items():
                if isinstance(channels, list):
                    for ch in channels:
                        if isinstance(ch, dict):
                            agents.append({
                                "name": ch.get("name", ch.get("id", "unknown")),
                                "type": "channel",
                                "platform": platform_name,
                                "channel_id": ch.get("id"),
                                "updated_at": updated_at,
                            })
                        elif isinstance(ch, str):
                            agents.append({
                                "name": ch,
                                "type": "channel",
                                "platform": platform_name,
                            })
        except (json.JSONDecodeError, OSError):
            pass

    # From project agents directory
    agents_dir = HERMES_HOME / "agents"
    if agents_dir.exists():
        for f in sorted(agents_dir.iterdir()):
            if f.is_dir() and not f.name.startswith("_"):
                agents.append({
                    "name": f.name,
                    "type": "project_agent",
                    "path": str(f),
                })
            elif f.is_file() and f.suffix in (".json", ".yaml", ".yml"):
                agents.append({
                    "name": f.stem,
                    "type": "agent_config",
                    "path": str(f),
                })

    return agents


@router.get("/wzrd/agents")
async def list_agents():
    """List all project agents."""
    agents = _discover_agents()
    return {"agents": agents, "count": len(agents)}


@router.get("/wzrd/agents/{name}")
async def get_agent(name: str):
    """Get agent details."""
    agents = _discover_agents()
    agent = next((a for a in agents if a.get("name") == name), None)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    # Try to load agent config if it has a path
    agent_path = agent.get("path")
    if agent_path:
        p = Path(agent_path)
        if p.is_file():
            try:
                agent["config"] = p.read_text()[:5000]
            except OSError:
                pass
        elif p.is_dir():
            files = []
            for f in sorted(p.iterdir()):
                if f.is_file() and not f.name.startswith("."):
                    files.append(f.name)
            agent["files"] = files

    return agent
