"""Shared utilities for WZRD.dev Dashboard collectors."""

import os
from datetime import datetime
from typing import Optional

try:
    import yaml as _yaml
except ImportError:
    _yaml = None


def load_yaml(text: str) -> dict:
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


def default_hermes_dir(hermes_dir: str | None = None) -> str:
    """Return the hermes directory.

    Priority: explicit arg > HERMES_HOME env var > ~/.hermes
    """
    if hermes_dir:
        return hermes_dir
    return os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))


def default_projects_dir(projects_dir: str | None = None) -> str:
    """Return the projects directory.

    Priority: explicit arg > REMI_DASHBOARD_PROJECTS_DIR env var > ~/projects
    """
    if projects_dir:
        return projects_dir
    return os.environ.get(
        "REMI_DASHBOARD_PROJECTS_DIR", os.path.expanduser("~/projects")
    )


# ── WZRD.dev Path Resolution ────────────────────────────────


def default_wzrd_dir(wzrd_dir: str | None = None) -> str:
    """Return the WZRD.dev root directory.

    Priority: explicit arg > WZRD_HOME env var > ~/wzrd-dev
    """
    if wzrd_dir:
        return wzrd_dir
    return os.environ.get("WZRD_HOME", os.path.expanduser("~/wzrd-dev"))


def default_wzrd_memory_dir(memory_dir: str | None = None) -> str:
    """Return the WZRD memory directory.

    Priority: explicit arg > WZRD_MEMORY_PATH env var > {wzrd_dir}/memory
    """
    if memory_dir:
        return memory_dir
    env = os.environ.get("WZRD_MEMORY_PATH")
    if env:
        return env
    return os.path.join(default_wzrd_dir(), "memory")


def default_wzrd_blueprint_dir(blueprint_dir: str | None = None) -> str:
    """Return the WZRD blueprints directory.

    Priority: explicit arg > WZRD_BLUEPRINT_DIR env var > {wzrd_dir}/blueprints
    """
    if blueprint_dir:
        return blueprint_dir
    env = os.environ.get("WZRD_BLUEPRINT_DIR")
    if env:
        return env
    return os.path.join(default_wzrd_dir(), "blueprints")


def default_wzrd_hermes_dir(hermes_dir: str | None = None) -> str:
    """Return the WZRD hermes directory (session state, sandboxes, PIV).

    Priority: explicit arg > HERMES_HOME env var > {wzrd_dir}/hermes
    """
    if hermes_dir:
        return hermes_dir
    env = os.environ.get("HERMES_HOME")
    if env:
        return env
    return os.path.join(default_wzrd_dir(), "hermes")


def default_wzrd_agents_dir(agents_dir: str | None = None) -> str:
    """Return the WZRD project agents directory.

    Priority: explicit arg > WZRD_AGENTS_DIR env var > {wzrd_hermes_dir}/hermes-agent/project_agents
    """
    if agents_dir:
        return agents_dir
    env = os.environ.get("WZRD_AGENTS_DIR")
    if env:
        return env
    return os.path.join(default_wzrd_hermes_dir(), "hermes-agent", "project_agents")


def safe_get(row, key, default=None):
    """Safely access a column from a sqlite3.Row or tuple.

    Returns default if the column is missing, access fails, or value is None.
    """
    try:
        val = row[key]
        return val if val is not None else default
    except (IndexError, KeyError):
        return default


def parse_timestamp(value) -> Optional[datetime]:
    """Parse a timestamp from various formats (unix int/float, ISO string).

    Returns None if parsing fails.
    """
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        if isinstance(value, str):
            try:
                return datetime.fromtimestamp(float(value))
            except ValueError:
                return datetime.fromisoformat(value)
    except (ValueError, TypeError, OSError):
        pass
    return None
