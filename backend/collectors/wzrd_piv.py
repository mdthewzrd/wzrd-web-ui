"""WZRD PIV Workflow Collector.

Reads PIV (Plan-Implement-Validate-Learn) state from
~/.hermes/.wzrd/piv_state.json. Returns the current phase,
task description, and phase history.
"""

from __future__ import annotations

import json
from pathlib import Path

from .utils import default_wzrd_hermes_dir, parse_timestamp
from .wzrd_models import PIVPhaseEntry, PIVState


def collect_piv(hermes_dir: str | None = None) -> PIVState:
    """Collect WZRD PIV workflow state.

    Args:
        hermes_dir: Override for the Hermes home directory.

    Returns:
        PIVState with current phase info. Returns an empty/inactive
        state if piv_state.json does not exist or is unparseable.
    """
    base = Path(default_wzrd_hermes_dir(hermes_dir)) / ".wzrd"
    piv_path = base / "piv_state.json"

    if not piv_path.exists():
        return PIVState()

    try:
        data = json.loads(piv_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return PIVState()

    if not isinstance(data, dict):
        return PIVState()

    current_phase = data.get("current_phase", data.get("currentPhase", ""))
    task_description = data.get("task_description", data.get("taskDescription", ""))
    started_at = parse_timestamp(data.get("started_at") or data.get("startedAt"))

    # Parse phase history
    history: list[PIVPhaseEntry] = []
    raw_history = data.get("phase_history", data.get("phaseHistory"))
    if isinstance(raw_history, list):
        for item in raw_history:
            if isinstance(item, dict):
                history.append(
                    PIVPhaseEntry(
                        phase=item.get("phase", ""),
                        started_at=parse_timestamp(
                            item.get("started_at") or item.get("startedAt")
                        ),
                    )
                )
            elif isinstance(item, str):
                history.append(PIVPhaseEntry(phase=item))

    return PIVState(
        current_phase=current_phase,
        task_description=task_description,
        started_at=started_at,
        phase_history=history,
    )
