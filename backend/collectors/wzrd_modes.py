"""WZRD Mode State Collector.

Reads the current session mode from session_mode.json.
Returns the active mode, activation timestamp, available modes list,
and mode history if tracked.
"""

from __future__ import annotations

import json
from pathlib import Path

from .utils import default_wzrd_hermes_dir, parse_timestamp
from .wzrd_models import AVAILABLE_MODES, ModeHistoryEntry, ModeState


def collect_modes(hermes_dir: str | None = None) -> ModeState:
    """Collect WZRD session mode state.

    Args:
        hermes_dir: Override for the Hermes home directory.

    Returns:
        ModeState with current mode. Defaults to ACQUISITION if the
        session_mode.json file is missing or unparseable.
    """
    base = Path(default_wzrd_hermes_dir(hermes_dir)) / ".wzrd"
    mode_path = base / "session_mode.json"

    if not mode_path.exists():
        return ModeState(current_mode="ACQUISITION")

    try:
        data = json.loads(mode_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ModeState(current_mode="ACQUISITION")

    if not isinstance(data, dict):
        return ModeState(current_mode="ACQUISITION")

    # Actual key is "mode" (not "current_mode"); also check alternate keys
    current_mode = data.get(
        "mode", data.get("current_mode", data.get("currentMode", "ACQUISITION"))
    )
    # Actual key is "switched_at" (not "activated_at"); also check alternates
    activated_at = parse_timestamp(
        data.get("switched_at") or data.get("activated_at") or data.get("activatedAt")
    )

    available = data.get("available_modes", data.get("availableModes"))
    if not isinstance(available, list):
        available = list(AVAILABLE_MODES)

    # Parse mode history
    history: list[ModeHistoryEntry] = []
    raw_history = data.get("mode_history", data.get("modeHistory"))
    if isinstance(raw_history, list):
        for item in raw_history:
            if isinstance(item, dict):
                history.append(
                    ModeHistoryEntry(
                        mode=item.get("mode", ""),
                        activated_at=parse_timestamp(
                            item.get("switched_at")
                            or item.get("activated_at")
                            or item.get("activatedAt")
                        ),
                    )
                )
            elif isinstance(item, str):
                history.append(ModeHistoryEntry(mode=item))

    return ModeState(
        current_mode=current_mode,
        activated_at=activated_at,
        available_modes=available,
        mode_history=history,
    )
