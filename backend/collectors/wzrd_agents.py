"""WZRD Project Agent Collector.

Scans ~/wzrd-dev/hermes/hermes-agent/project_agents/ for agent directories,
reads agent.yaml config for each, and cross-references with sandboxes.json
to determine sandbox status.
"""

from __future__ import annotations

import json
from pathlib import Path

from .utils import default_wzrd_agents_dir, default_wzrd_hermes_dir
from .wzrd_models import AgentInfo, AgentsState

try:
    import yaml as _yaml
except ImportError:
    _yaml = None


def _load_yaml(text: str) -> dict:
    """Parse YAML text, falling back to a simple key:value parser."""
    if _yaml:
        try:
            data = _yaml.safe_load(text)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    result: dict = {}
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            val = val.strip()
            if val:
                result[key.strip()] = val
    return result


def _get_sandbox_names(hermes_dir: str | None = None) -> dict[str, str]:
    """Load sandbox name->status mapping from sandboxes.json.

    Returns dict mapping sandbox name to its status string.
    """
    base = Path(default_wzrd_hermes_dir(hermes_dir)) / ".wzrd"
    sb_path = base / "sandboxes.json"
    if not sb_path.exists():
        return {}

    try:
        data = json.loads(sb_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    entries = data if isinstance(data, list) else data.get("sandboxes", [])
    result: dict[str, str] = {}
    for entry in entries:
        if isinstance(entry, dict):
            name = entry.get("name", "")
            status = entry.get("status", "unknown")
            if name:
                result[name] = status
    return result


def _read_agent_yaml(agent_dir: Path) -> dict:
    """Read and parse agent.yaml from an agent directory."""
    yaml_path = agent_dir / "agent.yaml"
    if not yaml_path.exists():
        yaml_path = agent_dir / "agent.yml"
    if not yaml_path.exists():
        return {}

    try:
        text = yaml_path.read_text(encoding="utf-8")
    except OSError:
        return {}

    return _load_yaml(text)


def collect_agents(
    hermes_dir: str | None = None,
    agents_dir: str | None = None,
) -> AgentsState:
    """Collect WZRD project agent state.

    Args:
        hermes_dir: Override for the Hermes home directory.
        agents_dir: Override for the project_agents directory.

    Returns:
        AgentsState with agent info. Missing directories return
        an empty state.
    """
    if agents_dir is None:
        agents_dir = default_wzrd_agents_dir()

    agents_path = Path(agents_dir)
    if not agents_path.exists() or not agents_path.is_dir():
        return AgentsState()

    sandbox_map = _get_sandbox_names(hermes_dir)
    agents: list[AgentInfo] = []

    try:
        entries = sorted(agents_path.iterdir())
    except (OSError, PermissionError):
        return AgentsState()

    for entry in entries:
        if not entry.is_dir():
            continue

        config = _read_agent_yaml(entry)
        agent_name = entry.name

        # Determine modes
        modes = config.get("modes", [])
        if isinstance(modes, str):
            modes = [m.strip() for m in modes.split(",") if m.strip()]

        # Check sandbox status by matching agent name or configured sandbox
        sandbox_status = "none"
        configured_sb = config.get("sandbox", "") or config.get("sandbox_name", "")
        if configured_sb and configured_sb in sandbox_map:
            sandbox_status = sandbox_map[configured_sb]
        elif agent_name in sandbox_map:
            sandbox_status = sandbox_map[agent_name]

        # Check for blueprint and skills files
        has_blueprint = (entry / "blueprint.md").exists() or (
            entry / "BLUEPRINT.md"
        ).exists()
        has_skills = (entry / "skills").is_dir() or (entry / "skills.yaml").exists()

        agents.append(
            AgentInfo(
                name=agent_name,
                description=config.get("description", "") or config.get("desc", ""),
                modes=modes if isinstance(modes, list) else [],
                sandbox_status=sandbox_status,
                has_blueprint=has_blueprint,
                has_skills=has_skills,
                project_dir=str(entry),
            )
        )

    return AgentsState(agents=agents)
