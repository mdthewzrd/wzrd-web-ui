"""WZRD memory zones endpoints."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..collectors.utils import default_wzrd_memory_dir
from ..collectors.wzrd_zones import collect_zones

router = APIRouter()

# The 6 canonical memory zones
ZONE_DEFS = [
    {
        "id": "zone1",
        "name": "Zone 1 — User Profile",
        "description": "User preferences, habits, and learning style",
    },
    {
        "id": "zone2",
        "name": "Zone 2 — Session Context",
        "description": "Current session state and recent interactions",
    },
    {
        "id": "zone3",
        "name": "Zone 3 — Project Knowledge",
        "description": "Project-specific knowledge and handoffs",
    },
    {
        "id": "zone4",
        "name": "Zone 4 — Long-Term Memory",
        "description": "Persistent facts and accumulated knowledge",
    },
    {
        "id": "zone5",
        "name": "Zone 5 — Patterns & Corrections",
        "description": "Behavioral patterns and correction history",
    },
    {
        "id": "zone6",
        "name": "Zone 6 — System State",
        "description": "Agent configuration, mode, and runtime state",
    },
]


def _zone_path(zone_id: str) -> Path:
    return Path(default_wzrd_memory_dir()) / zone_id


def _zone_status(zone_id: str) -> dict[str, Any]:
    """Get zone status by scanning its directory."""
    zp = _zone_path(zone_id)
    files = []
    if zp.exists():
        for f in sorted(zp.iterdir()):
            if f.is_file():
                try:
                    size = f.stat().st_size
                except OSError:
                    size = 0
                files.append({"name": f.name, "size": size})
    return {
        "exists": zp.exists(),
        "file_count": len(files),
        "files": files,
    }


@router.get("/wzrd/zones")
async def list_zones():
    """List all 6 memory zones with status using the deep collector."""
    from ..api.serialize import to_dict

    zones_state = collect_zones()
    return {"zones": [to_dict(z) for z in zones_state.zones]}


@router.get("/wzrd/zones/{zone_id}")
async def get_zone(zone_id: str):
    """Get single zone details using the deep collector."""
    zone_def = next((z for z in ZONE_DEFS if z["id"] == zone_id), None)
    if not zone_def:
        raise HTTPException(status_code=404, detail=f"Unknown zone: {zone_id}")

    from ..api.serialize import to_dict

    zones_state = collect_zones()
    # zone_id in collector is int (1-6), API uses strings like "zone1"
    zone_num = int(zone_id.replace("zone", ""))
    zone_info = next((z for z in zones_state.zones if z.zone_id == zone_num), None)
    if zone_info:
        return {**zone_def, **to_dict(zone_info)}

    # Fallback: return basic zone def with empty state
    return {
        **zone_def,
        "file_count": 0,
        "total_size": 0,
        "files": [],
        "parse_errors": [],
    }


class ZoneSearchRequest(BaseModel):
    query: str


@router.post("/wzrd/zones/{zone_id}/search")
async def search_zone(zone_id: str, body: ZoneSearchRequest):
    """Search within a zone for text matching the query."""
    zone_def = next((z for z in ZONE_DEFS if z["id"] == zone_id), None)
    if not zone_def:
        raise HTTPException(status_code=404, detail=f"Unknown zone: {zone_id}")

    zp = _zone_path(zone_id)
    results = []
    query_lower = body.query.lower()

    if zp.exists():
        for f in zp.iterdir():
            if not f.is_file():
                continue
            try:
                text = f.read_text()
            except OSError:
                continue
            if query_lower in text.lower():
                # Find matching lines
                matches = []
                for i, line in enumerate(text.splitlines(), 1):
                    if query_lower in line.lower():
                        matches.append({"line": i, "text": line[:200]})
                results.append({"file": f.name, "matches": matches})

    return {"zone": zone_id, "query": body.query, "results": results}
