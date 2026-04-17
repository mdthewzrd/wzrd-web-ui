"""WZRD Fleet Coordination Collector.

Scans ~/.hermes/.wzrd/memory/zone6_fleet/ for fleet coordination
files and returns active agent count, agent roles, and status.
"""

from __future__ import annotations

import json
from pathlib import Path

from .utils import default_wzrd_memory_dir
from .wzrd_models import FleetAgent, FleetState


def _parse_agent_file(path: Path) -> FleetAgent | None:
    """Try to parse a single fleet agent file (JSON or text)."""
    name = path.stem
    try:
        text = path.read_text(encoding="utf-8").strip()
    except (OSError, PermissionError):
        return None

    # Try JSON first
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return FleetAgent(
                name=data.get("name", name),
                role=data.get("role", data.get("type", "")),
                status=data.get("status", "active"),
            )
    except json.JSONDecodeError:
        pass

    # Fallback: treat as text, try to extract role from first line
    lines = text.split("\n")
    role = ""
    if lines:
        first = lines[0].strip()
        # Try "role: X" or "type: X" patterns
        for prefix in ("role:", "type:", "status:"):
            if first.lower().startswith(prefix):
                role = first.split(":", 1)[1].strip()
                break

    return FleetAgent(name=name, role=role, status="active")


def _parse_agents_json(path: Path) -> list[FleetAgent]:
    """Parse a single JSON file containing a list of agents."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    if isinstance(data, list):
        agents: list[FleetAgent] = []
        for item in data:
            if isinstance(item, dict):
                agents.append(
                    FleetAgent(
                        name=item.get("name", "unknown"),
                        role=item.get("role", item.get("type", "")),
                        status=item.get("status", "active"),
                    )
                )
        return agents
    return []


def collect_fleet(memory_dir: str | None = None) -> FleetState:
    """Collect WZRD fleet coordination state.

    Args:
        memory_dir: Override for the WZRD memory directory.

    Returns:
        FleetState with active agent info. Returns an inactive
        state if the fleet directory does not exist.
    """
    base = Path(default_wzrd_memory_dir(memory_dir)) / "zone6"

    if not base.exists() or not base.is_dir():
        return FleetState(coordination_status="inactive")

    agents: list[FleetAgent] = []

    try:
        entries = sorted(base.iterdir())
    except (OSError, PermissionError):
        return FleetState(coordination_status="inactive")

    for entry in entries:
        if not entry.is_file():
            continue

        # Check for a single aggregated file first
        if entry.name in ("agents.json", "fleet.json", "coordination.json"):
            agents.extend(_parse_agents_json(entry))
            continue

        # Individual agent files
        agent = _parse_agent_file(entry)
        if agent:
            agents.append(agent)

    # Deduplicate by name (keep first occurrence)
    seen: set[str] = set()
    unique: list[FleetAgent] = []
    for a in agents:
        if a.name not in seen:
            seen.add(a.name)
            unique.append(a)

    status = "active" if unique else "inactive"

    return FleetState(
        active_agents=len(unique),
        agent_list=unique,
        coordination_status=status,
    )
