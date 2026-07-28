"""
AION API — Public platform facts (unauthenticated).

Powers the counters on the marketing page. Everything here describes the *platform*
— how many role tiers exist, how many endpoints are mounted — and is derived from the
running code rather than typed into the HTML, so the landing page cannot drift from
what actually ships.

Deliberately exposes no organization data: no counts of documents, people, or
departments belonging to any customer. Those require a token.
"""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.security import ROLE_PERMISSIONS, UserRole

router = APIRouter(prefix="/public", tags=["Public"])

# The six departments the enterprise layer ships with (SRS Section 5).
SUPPORTED_DEPARTMENTS = 6
# Core intelligence modules surfaced on the landing page (SRS Section 3).
CORE_MODULES = 5

#: The five SRS Section 6 tiers, as distinct from the legacy internal roles.
SRS_ROLE_TIERS = (
    UserRole.EMPLOYEE,
    UserRole.MANAGER,
    UserRole.DEPT_HEAD,
    UserRole.ORG_ADMIN,
    UserRole.EXECUTIVE,
)


@router.get("/platform")
async def platform_facts(request: Request):
    """Counts describing this deployment, computed at request time."""
    # Count mounted GET/POST API routes rather than maintaining a number by hand.
    endpoints = {
        route.path
        for route in request.app.routes
        if getattr(route, "path", "").startswith("/api/v1")
    }
    return {
        "departments_supported": SUPPORTED_DEPARTMENTS,
        "role_tiers": len(SRS_ROLE_TIERS),
        "role_tier_names": [r.value for r in SRS_ROLE_TIERS],
        "api_endpoints": len(endpoints),
        "core_modules": CORE_MODULES,
        "permissions_defined": len(
            {p for perms in ROLE_PERMISSIONS.values() for p in perms}
        ),
    }
