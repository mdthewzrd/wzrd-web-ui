"""WZRD Blueprint Collector.

Scans ~/wzrd-dev/blueprints/ for YAML blueprint files and returns
structured blueprint state with steps, categories, and metadata.
"""

from __future__ import annotations

from pathlib import Path

from .utils import default_wzrd_blueprint_dir
from .wzrd_models import BlueprintInfo, BlueprintStep, BlueprintsState

try:
    import yaml as _yaml
except ImportError:
    _yaml = None


def _parse_yaml(text: str) -> dict:
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


def _parse_blueprint(path: Path) -> BlueprintInfo | None:
    """Parse a single blueprint YAML file."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, PermissionError):
        return None

    data = _parse_yaml(text)
    if not data:
        return None

    steps: list[BlueprintStep] = []
    raw_steps = data.get("steps", [])
    if isinstance(raw_steps, list):
        for step in raw_steps:
            if isinstance(step, dict):
                steps.append(
                    BlueprintStep(
                        name=step.get("name", ""),
                        action=step.get("action", ""),
                        command=step.get("command", ""),
                        description=step.get("description", ""),
                    )
                )

    tags = data.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    return BlueprintInfo(
        filename=path.name,
        name=data.get("name", path.stem),
        version=str(data.get("version", "")),
        description=data.get("description", ""),
        category=data.get("category", ""),
        author=data.get("author", ""),
        tags=tags if isinstance(tags, list) else [],
        steps=steps,
    )


def collect_blueprints(blueprint_dir: str | None = None) -> BlueprintsState:
    """Collect WZRD blueprint state.

    Args:
        blueprint_dir: Override for the blueprints directory.

    Returns:
        BlueprintsState with parsed blueprint info.
    """
    base = Path(default_wzrd_blueprint_dir(blueprint_dir))
    if not base.exists() or not base.is_dir():
        return BlueprintsState()

    blueprints: list[BlueprintInfo] = []
    errors: list[str] = []

    try:
        entries = sorted(base.iterdir())
    except (OSError, PermissionError):
        return BlueprintsState()

    for entry in entries:
        if not entry.is_file():
            continue
        if entry.suffix not in (".yaml", ".yml"):
            continue
        bp = _parse_blueprint(entry)
        if bp:
            blueprints.append(bp)
        else:
            errors.append(f"Failed to parse {entry.name}")

    return BlueprintsState(blueprints=blueprints, parse_errors=errors)
