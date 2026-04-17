"""WZRD Memory Zone Collector.

Reads from ~/wzrd-dev/memory/zone{1-6}/ directories and returns
structured zone state with file listings, capacity info, and parsed content.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .utils import default_wzrd_memory_dir, parse_timestamp
from .wzrd_models import (
    ExecutionSummary,
    FleetPattern,
    OutputBufferItem,
    UserProfile,
    WorkingMemoryItem,
    WisdomPattern,
    ZoneFile,
    ZoneInfo,
    ZonesState,
)

# Zone metadata
ZONES: dict[int, tuple[str, str]] = {
    1: ("Identity", "Core identity and personality files"),
    2: ("Working Memory", "Active context and working state"),
    3: ("Output Buffer", "Pending outputs and queued responses"),
    4: ("Project Knowledge", "Project-specific knowledge and context"),
    5: ("Wisdom", "Accumulated learnings and insights"),
    6: ("Fleet Coordination", "Multi-agent coordination data"),
}


def _scan_zone_files(zone_dir: Path) -> tuple[list[ZoneFile], int]:
    """Scan directory for files, return (files, total_size)."""
    files: list[ZoneFile] = []
    total_size = 0

    try:
        for entry in sorted(zone_dir.iterdir()):
            if entry.is_file():
                try:
                    stat = entry.stat()
                    total_size += stat.st_size
                    files.append(
                        ZoneFile(
                            name=entry.name,
                            size=stat.st_size,
                            modified=datetime.fromtimestamp(stat.st_mtime),
                        )
                    )
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass

    return files, total_size


def _load_json(path: Path) -> dict | None:
    """Load a JSON file, return None on failure."""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def _load_json_list(path: Path) -> list[dict]:
    """Load a JSON file containing a list of dicts."""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []
    except (json.JSONDecodeError, OSError):
        return []


# ── Zone-specific parsers ───────────────────────────────────


def _parse_zone1(zone_dir: Path) -> tuple[Optional[UserProfile], list[str]]:
    """Parse Zone 1 user profile JSON."""
    errors: list[str] = []
    # Look for any .json file in zone dir
    for f in sorted(zone_dir.glob("*.json")):
        data = _load_json(f)
        if data is None:
            errors.append(f"Failed to parse {f.name}")
            continue

        prefs = data.get("preferences", {})
        habits = data.get("habits", {})
        return (
            UserProfile(
                user_id=data.get("user_id", ""),
                style=prefs.get("style", ""),
                complexity_level=prefs.get("complexity_level", ""),
                response_verbosity=prefs.get("response_verbosity", ""),
                prefers_cli_formatting=habits.get("prefers_cli_formatting", False),
                likes_analogies=habits.get("likes_analogies", False),
                wants_tangible_outputs=habits.get("wants_tangible_outputs", False),
                created_at=parse_timestamp(data.get("created_at")),
                updated_at=parse_timestamp(data.get("updated_at")),
            ),
            errors,
        )
    return None, errors


def _parse_zone2(zone_dir: Path) -> tuple[list[WorkingMemoryItem], list[str]]:
    """Parse Zone 2 working memory items."""
    items: list[WorkingMemoryItem] = []
    errors: list[str] = []
    for f in sorted(zone_dir.glob("*.json")):
        # Could be a list or single item
        data = _load_json(f)
        if data is None:
            # Try as list
            for item in _load_json_list(f):
                items.append(
                    WorkingMemoryItem(
                        item_id=item.get("item_id", ""),
                        session_id=item.get("session_id", ""),
                        key=item.get("key", ""),
                        value=item.get("value"),
                        item_type=item.get("item_type", ""),
                        created_at=parse_timestamp(item.get("created_at")),
                    )
                )
            continue
        items.append(
            WorkingMemoryItem(
                item_id=data.get("item_id", ""),
                session_id=data.get("session_id", ""),
                key=data.get("key", ""),
                value=data.get("value"),
                item_type=data.get("item_type", ""),
                created_at=parse_timestamp(data.get("created_at")),
            )
        )
    return items, errors


def _parse_zone3(zone_dir: Path) -> tuple[list[OutputBufferItem], list[str]]:
    """Parse Zone 3 output buffer items."""
    items: list[OutputBufferItem] = []
    errors: list[str] = []
    for f in sorted(zone_dir.glob("*.json")):
        for item in _load_json_list(f):
            items.append(
                OutputBufferItem(
                    output_id=item.get("output_id", ""),
                    output_type=item.get("output_type", ""),
                    content=str(item.get("content", ""))[:200],
                    status=item.get("status", ""),
                    priority=item.get("priority", 0),
                )
            )
    return items, errors


def _parse_zone4(zone_dir: Path) -> tuple[list[ExecutionSummary], list[str]]:
    """Parse Zone 4 execution records."""
    executions: list[ExecutionSummary] = []
    errors: list[str] = []
    for f in sorted(zone_dir.glob("*.json")):
        # Skip index.json
        if f.name == "index.json":
            continue
        data = _load_json(f)
        if data is None:
            errors.append(f"Failed to parse {f.name}")
            continue
        executions.append(
            ExecutionSummary(
                execution_id=data.get("execution_id", ""),
                project_id=data.get("project_id", ""),
                task_description=data.get("task_description", ""),
                mode=data.get("mode", ""),
                status=data.get("status", ""),
                duration_ms=data.get("duration_ms", 0),
                tools_used=data.get("tools_used", []),
                skills_used=data.get("skills_used", []),
                start_time=parse_timestamp(data.get("start_time")),
                end_time=parse_timestamp(data.get("end_time")),
            )
        )
    return executions, errors


def _parse_zone5(zone_dir: Path) -> tuple[list[WisdomPattern], list[str]]:
    """Parse Zone 5 wisdom patterns."""
    patterns: list[WisdomPattern] = []
    errors: list[str] = []
    for f in sorted(zone_dir.glob("*.json")):
        for item in _load_json_list(f):
            patterns.append(
                WisdomPattern(
                    pattern_id=item.get("pattern_id", ""),
                    pattern_type=item.get("pattern_type", ""),
                    category=item.get("category", ""),
                    context=item.get("context", ""),
                    action=item.get("action", ""),
                    result=item.get("result", ""),
                    confidence=item.get("confidence", 0.0),
                    frequency=item.get("frequency", 0),
                )
            )
    return patterns, errors


def _parse_zone6(zone_dir: Path) -> tuple[list[FleetPattern], list[str]]:
    """Parse Zone 6 fleet patterns."""
    patterns: list[FleetPattern] = []
    errors: list[str] = []
    for f in sorted(zone_dir.glob("*.json")):
        for item in _load_json_list(f):
            patterns.append(
                FleetPattern(
                    pattern_id=item.get("pattern_id", ""),
                    pattern_type=item.get("pattern_type", ""),
                    category=item.get("category", ""),
                    confidence=item.get("confidence", 0.0),
                    fleet_success_rate=item.get("fleet_success_rate", 0.0),
                    projects_used=item.get("projects_used", []),
                )
            )
    return patterns, errors


# Parsers by zone ID
_ZONE_PARSERS = {
    1: _parse_zone1,
    2: _parse_zone2,
    3: _parse_zone3,
    4: _parse_zone4,
    5: _parse_zone5,
    6: _parse_zone6,
}


def _scan_zone(zone_dir: Path, zone_id: int) -> ZoneInfo:
    """Scan a single zone directory and return its state."""
    name, description = ZONES.get(zone_id, (f"Zone {zone_id}", ""))

    if not zone_dir.exists() or not zone_dir.is_dir():
        return ZoneInfo(zone_id=zone_id, name=name, description=description)

    files, total_size = _scan_zone_files(zone_dir)

    info = ZoneInfo(
        zone_id=zone_id,
        name=name,
        description=description,
        file_count=len(files),
        total_size=total_size,
        files=files,
    )

    # Deep parse zone content
    parser = _ZONE_PARSERS.get(zone_id)
    if parser:
        if zone_id == 1:
            profile, errors = parser(zone_dir)
            info.user_profile = profile
            info.parse_errors = errors
        elif zone_id == 2:
            items, errors = parser(zone_dir)
            info.working_memory_items = items
            info.parse_errors = errors
        elif zone_id == 3:
            items, errors = parser(zone_dir)
            info.output_buffer_items = items
            info.parse_errors = errors
        elif zone_id == 4:
            executions, errors = parser(zone_dir)
            info.executions = executions
            info.parse_errors = errors
        elif zone_id == 5:
            patterns, errors = parser(zone_dir)
            info.wisdom_patterns = patterns
            info.parse_errors = errors
        elif zone_id == 6:
            patterns, errors = parser(zone_dir)
            info.fleet_patterns = patterns
            info.parse_errors = errors

    return info


def collect_zones(memory_dir: str | None = None) -> ZonesState:
    """Collect state of all WZRD memory zones.

    Args:
        memory_dir: Override for the WZRD memory directory.

    Returns:
        ZonesState with info for all 6 zones. Missing directories
        are returned as empty zones with zero file counts.
    """
    base = Path(default_wzrd_memory_dir(memory_dir))
    zones: list[ZoneInfo] = []

    for zone_id in range(1, 7):
        zone_dir = base / f"zone{zone_id}"
        zone_info = _scan_zone(zone_dir, zone_id)
        # Handle nested structure: zone1/zone1/*.json
        if zone_info.file_count == 0:
            nested = zone_dir / f"zone{zone_id}"
            if nested.is_dir():
                zone_info = _scan_zone(nested, zone_id)
        zones.append(zone_info)

    return ZonesState(zones=zones)
