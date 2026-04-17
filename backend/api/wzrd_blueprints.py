"""WZRD blueprints endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ..collectors.wzrd_blueprints import collect_blueprints
from ..api.serialize import to_dict

router = APIRouter()


@router.get("/wzrd/blueprints")
async def list_blueprints():
    """List all WZRD blueprints."""
    state = collect_blueprints()
    return {
        "total": state.total,
        "categories": state.categories,
        "blueprints": [to_dict(bp) for bp in state.blueprints],
        "parse_errors": state.parse_errors,
    }
