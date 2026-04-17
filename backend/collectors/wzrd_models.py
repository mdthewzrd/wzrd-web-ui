"""WZRD-specific data models for the TUI collector library."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


# ── Memory Zones ────────────────────────────────────────────


@dataclass
class ZoneFile:
    """A single file within a memory zone."""

    name: str
    size: int  # bytes
    modified: Optional[datetime] = None


# ── Zone 1: Identity ────────────────────────────────────────


@dataclass
class UserProfile:
    """Parsed user profile from Zone 1."""

    user_id: str = ""
    style: str = ""
    complexity_level: str = ""
    response_verbosity: str = ""
    prefers_cli_formatting: bool = False
    likes_analogies: bool = False
    wants_tangible_outputs: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── Zone 2: Working Memory ──────────────────────────────────


@dataclass
class WorkingMemoryItem:
    """A single working memory item from Zone 2."""

    item_id: str = ""
    session_id: str = ""
    key: str = ""
    value: Any = None
    item_type: str = ""
    created_at: Optional[datetime] = None


# ── Zone 3: Output Buffer ───────────────────────────────────


@dataclass
class OutputBufferItem:
    """A single output item from Zone 3."""

    output_id: str = ""
    output_type: str = ""
    content: str = ""
    status: str = ""
    priority: int = 0


# ── Zone 4: Project Knowledge ───────────────────────────────


@dataclass
class ExecutionSummary:
    """Summary of a single execution from Zone 4."""

    execution_id: str = ""
    project_id: str = ""
    task_description: str = ""
    mode: str = ""
    status: str = ""
    duration_ms: int = 0
    tools_used: list[str] = field(default_factory=list)
    skills_used: list[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# ── Zone 5: Wisdom ──────────────────────────────────────────


@dataclass
class WisdomPattern:
    """A learned pattern from Zone 5."""

    pattern_id: str = ""
    pattern_type: str = ""
    category: str = ""
    context: str = ""
    action: str = ""
    result: str = ""
    confidence: float = 0.0
    frequency: int = 0


# ── Zone 6: Fleet Coordination ──────────────────────────────


@dataclass
class FleetPattern:
    """A fleet-level pattern from Zone 6."""

    pattern_id: str = ""
    pattern_type: str = ""
    category: str = ""
    confidence: float = 0.0
    fleet_success_rate: float = 0.0
    projects_used: list[str] = field(default_factory=list)


# ── Aggregated Zone Info ────────────────────────────────────


@dataclass
class ZoneInfo:
    """State of a single WZRD memory zone."""

    zone_id: int
    name: str
    description: str
    file_count: int = 0
    total_size: int = 0  # bytes
    files: list[ZoneFile] = field(default_factory=list)
    capacity_used: int = 0
    capacity_max: int = 0
    # Deep content
    user_profile: Optional[UserProfile] = None
    working_memory_items: list[WorkingMemoryItem] = field(default_factory=list)
    output_buffer_items: list[OutputBufferItem] = field(default_factory=list)
    executions: list[ExecutionSummary] = field(default_factory=list)
    wisdom_patterns: list[WisdomPattern] = field(default_factory=list)
    fleet_patterns: list[FleetPattern] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)

    @property
    def capacity_pct(self) -> float:
        return (
            (self.capacity_used / self.capacity_max * 100)
            if self.capacity_max > 0
            else 0.0
        )


@dataclass
class ZonesState:
    """Aggregated state of all WZRD memory zones."""

    zones: list[ZoneInfo] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return sum(z.file_count for z in self.zones)

    @property
    def total_size(self) -> int:
        return sum(z.total_size for z in self.zones)


# ── Sandboxes ──────────────────────────────────────────────


@dataclass
class SandboxInfo:
    """A single WZRD sandbox container."""

    name: str
    profile: str = ""
    status: str = "unknown"  # running, stopped, unknown
    container_id: str = ""
    created_at: Optional[datetime] = None
    capabilities: list[str] = field(default_factory=list)
    project_dir: str = ""


@dataclass
class SandboxesState:
    """Aggregated state of WZRD sandboxes."""

    sandboxes: list[SandboxInfo] = field(default_factory=list)
    docker_available: bool = True

    @property
    def running_count(self) -> int:
        return sum(1 for s in self.sandboxes if s.status == "running")

    @property
    def total(self) -> int:
        return len(self.sandboxes)


# ── Mode State ─────────────────────────────────────────────

AVAILABLE_MODES = [
    "ACQUISITION",
    "PROCESSING",
    "CREATION",
    "STORAGE",
    "VALIDATION",
    "DELIVERY",
    "OPTIMIZATION",
    "MAINTENANCE",
]


@dataclass
class ModeHistoryEntry:
    """A single mode transition in history."""

    mode: str
    activated_at: Optional[datetime] = None


@dataclass
class ModeState:
    """Current WZRD session mode and history."""

    current_mode: str = "CHAT"
    activated_at: Optional[datetime] = None
    available_modes: list[str] = field(default_factory=lambda: list(AVAILABLE_MODES))
    mode_history: list[ModeHistoryEntry] = field(default_factory=list)


# ── Project Agents ─────────────────────────────────────────


@dataclass
class AgentInfo:
    """A single WZRD project agent."""

    name: str
    description: str = ""
    modes: list[str] = field(default_factory=list)
    sandbox_status: str = "none"  # running, stopped, none
    has_blueprint: bool = False
    has_skills: bool = False
    project_dir: str = ""


@dataclass
class AgentsState:
    """Aggregated state of WZRD project agents."""

    agents: list[AgentInfo] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.agents)

    @property
    def active_count(self) -> int:
        return sum(1 for a in self.agents if a.sandbox_status == "running")


# ── PIV Workflow ───────────────────────────────────────────


@dataclass
class PIVPhaseEntry:
    """A single phase in PIV history."""

    phase: str  # plan, implement, validate, learn
    started_at: Optional[datetime] = None


@dataclass
class PIVState:
    """Current PIV (Plan-Implement-Validate-Learn) workflow state."""

    current_phase: str = ""  # empty means no active PIV
    task_description: str = ""
    started_at: Optional[datetime] = None
    phase_history: list[PIVPhaseEntry] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        return bool(self.current_phase)


# ── Fleet Coordination ─────────────────────────────────────


@dataclass
class FleetAgent:
    """A single agent in the fleet."""

    name: str
    role: str = ""
    status: str = "unknown"


@dataclass
class FleetState:
    """Fleet coordination state from zone 6."""

    active_agents: int = 0
    agent_list: list[FleetAgent] = field(default_factory=list)
    coordination_status: str = "inactive"  # active, inactive, unknown


# ── Blueprints ──────────────────────────────────────────────


@dataclass
class BlueprintStep:
    """A single step in a blueprint."""

    name: str = ""
    action: str = ""
    command: str = ""
    description: str = ""


@dataclass
class BlueprintInfo:
    """A single WZRD blueprint."""

    filename: str = ""
    name: str = ""
    version: str = ""
    description: str = ""
    category: str = ""
    author: str = ""
    tags: list[str] = field(default_factory=list)
    steps: list[BlueprintStep] = field(default_factory=list)


@dataclass
class BlueprintsState:
    """Aggregated state of WZRD blueprints."""

    blueprints: list[BlueprintInfo] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.blueprints)

    @property
    def categories(self) -> dict[str, int]:
        """Count of blueprints per category."""
        cats: dict[str, int] = {}
        for bp in self.blueprints:
            cats[bp.category] = cats.get(bp.category, 0) + 1
        return cats
