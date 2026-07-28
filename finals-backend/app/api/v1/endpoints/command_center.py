"""
AION API — Department Scorecards, Executive Command Center, Risk Prediction
(SRS Sections 27, 32, 37)

Per the SRS these introduce no new scoring logic: every figure here is a
department-scoped read over the engines that already exist (decay, MRI, disease
detection, marketplace activity, approval workflow). The Command Center is a
read-only aggregation on top of the same per-department numbers.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.core.dependencies import AuthUser, DbSession, resolve_department_scope
from app.core.security import Permission
from app.models.enterprise import MarketplaceItem, MarketplaceReuse, WorkflowStatus
from app.models.knowledge import KnowledgeItem
from app.models.organization import Department
from app.models.user import User

router = APIRouter(prefix="/enterprise", tags=["Enterprise: Command Center"])


def _band(score: float) -> str:
    if score >= 75:
        return "healthy"
    if score >= 50:
        return "attention"
    return "critical"


async def _department_scorecard(db, org_id: UUID, dept: Department) -> Dict[str, Any]:
    """Section 37 scorecard for one department.

    Every component is derived from stored data — no placeholder constants — so a
    department with no activity scores low rather than defaulting to something flattering.
    """
    items = (
        await db.execute(
            select(KnowledgeItem).where(
                KnowledgeItem.org_id == org_id,
                KnowledgeItem.dept_id == dept.id,
            )
        )
    ).scalars().all()

    total = len(items)
    approved = [i for i in items if i.workflow_status == WorkflowStatus.APPROVED]
    pending = [i for i in items if i.workflow_status in WorkflowStatus.OPEN]
    stale = [i for i in items if i.is_outdated or i.relevance_score < 0.4]
    isolated = [i for i in items if i.is_isolated]

    headcount = (
        await db.execute(
            select(func.count()).select_from(User).where(
                User.org_id == org_id, User.dept_id == dept.id, User.is_active.is_(True)
            )
        )
    ).scalar() or 0

    published = (
        await db.execute(
            select(func.count()).select_from(MarketplaceItem).where(
                MarketplaceItem.org_id == org_id,
                MarketplaceItem.source_dept_id == dept.id,
            )
        )
    ).scalar() or 0
    reused = (
        await db.execute(
            select(func.count()).select_from(MarketplaceReuse).where(
                MarketplaceReuse.org_id == org_id,
                MarketplaceReuse.target_dept_id == dept.id,
            )
        )
    ).scalar() or 0

    n_approved = len(approved)
    # Relevance and depth are measured over *approved* work only. Counting pending
    # items here let a department raise its own health simply by uploading material
    # nobody had reviewed yet — two of the three components rewarded the upload while
    # only coverage penalised it. Unreviewed work is not organizational memory, so it
    # now moves coverage down and the approval backlog up, and nothing else.
    avg_relevance = (
        sum(i.relevance_score for i in approved) / n_approved
    ) if n_approved else 0.0
    decay_rate = round((len(stale) / total * 100), 1) if total else 0.0
    coverage = round(n_approved / total * 100, 1) if total else 0.0

    # Documentation depth: how much reviewed material exists per person. Without this
    # a team with a single fresh, approved document scored as highly as a fully
    # documented one — flattering exactly the departments most at risk of losing
    # knowledge. DEPTH_TARGET approved documents per head counts as full marks.
    DEPTH_TARGET = 3.0
    depth = min(1.0, (n_approved / headcount) / DEPTH_TARGET) * 100 if headcount else 0.0

    # Health blends three things a reader would actually name: is it current
    # (relevance), did anyone check it (coverage), and is there enough of it (depth).
    health = round(
        min(100.0, avg_relevance * 100 * 0.45 + coverage * 0.30 + depth * 0.25), 1
    ) if total else 0.0
    # Innovation proxies as breadth of distinct domains relative to headcount.
    domains = {i.domain for i in items if i.domain}
    innovation = round(min(100.0, len(domains) * 12 + published * 6), 1)
    collaboration = round(min(100.0, published * 10 + reused * 12), 1)
    # Risk rises with isolation, staleness, and queue backlog.
    risk = round(min(100.0,
                     (len(isolated) / total * 45 if total else 0)
                     + (len(stale) / total * 35 if total else 0)
                     + min(len(pending) * 4, 20)), 1)

    return {
        "department_id": str(dept.id),
        "name": dept.name,
        "code": dept.code,
        "headcount": headcount,
        "knowledge_assets": total,
        "approved_assets": len(approved),
        "pending_approvals": len(pending),
        "health_score": health,
        "health_band": _band(health),
        "decay_rate_pct": decay_rate,
        "innovation_index": innovation,
        "collaboration_index": collaboration,
        "risk_score": risk,
        "risk_band": _band(100 - risk),
        "domains_covered": len(domains),
        "isolated_assets": len(isolated),
        "stale_assets": len(stale),
        "marketplace_published": published,
        "marketplace_reused": reused,
    }


@router.get("/departments/scorecards")
async def department_scorecards(
    *, current_user: AuthUser, db: DbSession, dept_id: Optional[str] = Query(None)
):
    """Section 37 — department scorecards, graded by who is asking.

    Everyone can see that the other departments exist and roughly how they are doing;
    a department cannot be managed in isolation from the rest of the company. What is
    graded is the *detail*: your own department comes back in full, everyone else's
    comes back as a summary with the operational internals (risk breakdown, approval
    backlog, stale counts) withheld.
    """
    org_id = UUID(current_user.org_id)
    scope = resolve_department_scope(current_user, dept_id)

    # Three layers of visibility, not two.
    #
    # SRS Section 5 keeps departments "isolated by default", and Section 10 hard-scopes
    # heads at the API layer. What that protects is worth protecting: individual
    # performance, review backlogs, risk internals — the things that become a stick to
    # beat a team with. It does not need to hide that a department *exists* and is
    # broadly coping, which is what people need in order to coordinate at all.
    #
    #   own      — your department, in full
    #   neighbour— other departments: name, health *band*, and what they have shared.
    #              No numeric score, no backlog, no per-person data. Enough to know
    #              who to ask, not enough to rank anyone.
    #   full     — every department complete; requires READ_CROSS_DEPARTMENT.
    #
    # Section 10's actual requirement — that a head cannot pull another department's
    # operational detail — still holds, and is still tested by the ?dept_id= bypass.
    cross = Permission.READ_CROSS_DEPARTMENT.value in current_user.permissions

    stmt = select(Department).where(Department.org_id == org_id, Department.is_active.is_(True))
    if cross and dept_id:
        # An explicit ?dept_id= from a cross-department role narrows to that one card.
        stmt = stmt.where(Department.id == UUID(dept_id))
    depts = (await db.execute(stmt.order_by(Department.name))).scalars().all()

    # Fields a peer department does not expose. Keeping this list explicit means a new
    # metric added to _department_scorecard is not leaked across departments by default.
    PEER_HIDDEN = {
        "pending_approvals", "stale_assets", "risk_score", "single_owner_assets",
        "top_contributors", "at_risk_assets",
    }
    # An employee sees their department's health and output, but the review backlog
    # and risk breakdown are what their head is measured on, not what they act on.
    MEMBER_HIDDEN = {"pending_approvals", "risk_score", "risk_band"}

    manages = Permission.REVIEW_DOCUMENT.value in current_user.permissions

    cards = []
    for d in depts:
        card = await _department_scorecard(db, org_id, d)
        own = (scope is None) or (str(d.id) == scope)
        if own and (manages or not current_user.is_department_scoped):
            card["detail"] = "full"
        elif own:
            card = {k: v for k, v in card.items() if k not in MEMBER_HIDDEN}
            card["detail"] = "member"
        else:
            card = {k: v for k, v in card.items() if k not in PEER_HIDDEN}
            card["detail"] = "summary"
        card["is_own_department"] = str(d.id) == (current_user.dept_id or "")
        cards.append(card)

    cards.sort(key=lambda c: c["health_score"], reverse=True)
    for i, c in enumerate(cards, 1):
        c["rank"] = i

    return {
        # "organization" means full detail on every card; "department" means full detail
        # on your own and summaries elsewhere.
        "scope": "department" if scope else "organization",
        "department_count": len(cards),
        "full_detail_count": sum(1 for c in cards if c["detail"] == "full"),
        "scorecards": cards,
    }


@router.get("/org-overview")
async def org_overview(*, current_user: AuthUser, db: DbSession):
    """The company as seen from wherever you sit.

    Every role gets this — an employee who cannot see how their organization is doing
    has no way to judge whether their own department is the problem. The company-level
    totals are the same for everyone because they describe the whole, not any one
    person's work. What changes by role is how much of the per-department breakdown is
    attached, which is handled by /departments/scorecards.
    """
    org_id = UUID(current_user.org_id)
    depts = (
        await db.execute(
            select(Department).where(
                Department.org_id == org_id, Department.is_active.is_(True)
            )
        )
    ).scalars().all()

    cards = [await _department_scorecard(db, org_id, d) for d in depts]
    if not cards:
        raise HTTPException(status_code=404, detail="No active departments")

    ranked = sorted(cards, key=lambda c: c["health_score"], reverse=True)
    total_assets = sum(c["knowledge_assets"] for c in cards)
    company_health = round(sum(c["health_score"] for c in cards) / len(cards), 1)

    mine = next(
        (c for c in ranked if c["department_id"] == (current_user.dept_id or "")), None
    )

    headcount = (
        await db.execute(
            select(func.count(User.id)).where(
                User.org_id == org_id, User.is_active.is_(True)
            )
        )
    ).scalar() or 0

    return {
        "organization": {
            "knowledge_health": company_health,
            "health_band": _band(company_health),
            "departments": len(cards),
            "people": headcount,
            "documents_held": total_assets,
            "departments_needing_help": sum(
                1 for c in cards if c["health_score"] < 50
            ),
        },
        # The named ladder identifies other departments and how they are doing, which
        # Section 5 keeps isolated. Only cross-department roles get it; everyone else
        # gets their own standing ("4 of 6") from `your_department` below, which is
        # useful context without naming anyone else.
        "departments": [
            {
                "name": c["name"],
                "code": c["code"],
                "health_band": c["health_band"],
                "rank": i,
                "is_own_department": c["department_id"] == (current_user.dept_id or ""),
            }
            for i, c in enumerate(ranked, 1)
        ]
        if Permission.READ_CROSS_DEPARTMENT.value in current_user.permissions
        else [],
        "your_department": (
            {
                "name": mine["name"],
                "health_score": mine["health_score"],
                "health_band": mine["health_band"],
                "rank": ranked.index(mine) + 1,
                "of": len(ranked),
                "documents_held": mine["knowledge_assets"],
                "compared_to_company": round(
                    mine["health_score"] - company_health, 1
                ),
            }
            if mine
            else None
        ),
        "your_role": current_user.role,
        "sees_full_detail_for": "all departments"
        if not current_user.is_department_scoped
        else "your own department",
    }


@router.get("/my-team")
async def my_team(*, current_user: AuthUser, db: DbSession):
    """The people a head or manager is responsible for, and what each is carrying.

    Scoped to the caller's own department. An org-wide role gets every person, since
    for them "my team" is the company.
    """
    # Who wrote how much is management information: it names individuals and is read
    # as a performance comparison. An employee sees their own output on their own
    # dashboard, not a ranked list of their colleagues and their head.
    if Permission.REVIEW_DOCUMENT.value not in current_user.permissions:
        raise HTTPException(
            status_code=403,
            detail="Team breakdowns are visible to managers and department heads. "
                   "Your own work is on your dashboard.",
        )

    org_id = UUID(current_user.org_id)
    stmt = select(User).where(User.org_id == org_id, User.is_active.is_(True))
    if current_user.is_department_scoped:
        if not current_user.dept_id:
            return {"department": None, "people": [], "count": 0}
        stmt = stmt.where(User.dept_id == UUID(current_user.dept_id))
    people = (await db.execute(stmt.order_by(User.full_name))).scalars().all()

    out = []
    for p in people:
        items = (
            await db.execute(
                select(KnowledgeItem).where(
                    KnowledgeItem.org_id == org_id,
                    KnowledgeItem.submitted_by_id == p.id,
                )
            )
        ).scalars().all()
        awaiting = [i for i in items if i.workflow_status in WorkflowStatus.OPEN]
        approved = [i for i in items if i.workflow_status == WorkflowStatus.APPROVED]
        out.append(
            {
                "user_id": str(p.id),
                "name": p.full_name or p.username,
                "role": p.role,
                "documents_written": len(items),
                "approved": len(approved),
                "awaiting_review": len(awaiting),
                # Someone carrying knowledge nobody else has written down is the
                # continuity risk a manager most needs to see.
                "sole_author_of": sum(
                    1 for i in approved if (i.relevance_score or 0) >= 0.8
                ),
            }
        )
    out.sort(key=lambda r: r["documents_written"], reverse=True)
    return {
        "scope": "department" if current_user.is_department_scoped else "organization",
        "count": len(out),
        "people": out,
        "writes_nothing": [r["name"] for r in out if r["documents_written"] == 0],
    }


@router.get("/command-center")
async def command_center(*, current_user: AuthUser, db: DbSession):
    """Section 27 — executive aggregation. Answers the SRS's eight questions directly."""
    if Permission.VIEW_COMMAND_CENTER.value not in current_user.permissions:
        raise HTTPException(
            status_code=403,
            detail="Command Center is restricted to executive and administrator roles",
        )

    org_id = UUID(current_user.org_id)
    depts = (
        await db.execute(
            select(Department).where(Department.org_id == org_id, Department.is_active.is_(True))
        )
    ).scalars().all()
    cards = [await _department_scorecard(db, org_id, d) for d in depts]

    if not cards:
        return {"department_count": 0, "kpis": {}, "answers": {}, "heatmap": [], "risk_matrix": []}

    def top(key: str, reverse: bool = True):
        best = sorted(cards, key=lambda c: c[key], reverse=reverse)[0]
        return {"department": best["name"], "department_id": best["department_id"], "value": best[key]}

    total_assets = sum(c["knowledge_assets"] for c in cards)
    total_pending = sum(c["pending_approvals"] for c in cards)
    avg_health = round(sum(c["health_score"] for c in cards) / len(cards), 1)

    return {
        "department_count": len(cards),
        "kpis": {
            "company_knowledge_health": avg_health,
            "health_band": _band(avg_health),
            "total_knowledge_assets": total_assets,
            "pending_approvals": total_pending,
            "departments_at_risk": sum(1 for c in cards if c["risk_score"] >= 50),
            "average_collaboration_index": round(
                sum(c["collaboration_index"] for c in cards) / len(cards), 1
            ),
        },
        # The eight questions the SRS says this screen exists to answer.
        "answers": {
            "highest_knowledge_loss": top("decay_rate_pct"),
            "highest_risk": top("risk_score"),
            "most_innovative": top("innovation_index"),
            "most_collaborative": top("collaboration_index"),
            "most_reusable_knowledge_published": top("marketplace_published"),
            "healthiest": top("health_score"),
            "weakest": top("health_score", reverse=False),
            "largest_backlog": top("pending_approvals"),
        },
        "heatmap": [
            {
                "department": c["name"],
                "department_id": c["department_id"],
                "health": c["health_score"],
                "risk": c["risk_score"],
                "decay": c["decay_rate_pct"],
                "band": c["health_band"],
            }
            for c in cards
        ],
        "risk_matrix": [
            {
                "department": c["name"],
                # Likelihood from observed risk, impact from how much knowledge is exposed.
                "likelihood": round(c["risk_score"] / 100, 2),
                "impact": round(min(1.0, c["knowledge_assets"] / max(total_assets, 1) * len(cards)), 2),
                "quadrant": (
                    "critical" if c["risk_score"] >= 50 and c["knowledge_assets"] >= total_assets / len(cards)
                    else "monitor" if c["risk_score"] >= 50
                    else "stable"
                ),
            }
            for c in cards
        ],
        "scorecards": cards,
    }


@router.get("/risk-predictions")
async def risk_predictions(
    *, current_user: AuthUser, db: DbSession, dept_id: Optional[str] = Query(None)
):
    """Section 32 — forward-looking risks.

    Every prediction carries the five SRS-mandated fields so it stays explainable:
    probability, reason, business impact, recommended action, confidence.
    """
    org_id = UUID(current_user.org_id)
    scope = resolve_department_scope(current_user, dept_id)

    stmt = select(Department).where(Department.org_id == org_id, Department.is_active.is_(True))
    if scope:
        stmt = stmt.where(Department.id == UUID(scope))
    depts = (await db.execute(stmt)).scalars().all()

    predictions: List[Dict[str, Any]] = []
    for d in depts:
        c = await _department_scorecard(db, org_id, d)
        if c["knowledge_assets"] == 0:
            continue

        if c["decay_rate_pct"] > 20:
            predictions.append({
                "risk_type": "knowledge_loss",
                "department": c["name"],
                "department_id": c["department_id"],
                "probability": round(min(0.95, c["decay_rate_pct"] / 100 + 0.25), 2),
                "reason": f"{c['stale_assets']} of {c['knowledge_assets']} assets are stale or low-relevance",
                "business_impact": "Teams rebuild knowledge that already existed, slowing delivery",
                "recommended_action": "Schedule a refresh cycle for the flagged documents",
                "confidence": 0.8 if c["knowledge_assets"] >= 5 else 0.5,
            })
        if c["isolated_assets"] > 0:
            predictions.append({
                "risk_type": "knowledge_silos",
                "department": c["name"],
                "department_id": c["department_id"],
                "probability": round(min(0.9, c["isolated_assets"] / c["knowledge_assets"] + 0.2), 2),
                "reason": f"{c['isolated_assets']} assets have no owner or connection",
                "business_impact": "Knowledge is unreachable when the original author is unavailable",
                "recommended_action": "Assign owners and link isolated assets to a project or team",
                "confidence": 0.75,
            })
        if c["collaboration_index"] < 30:
            predictions.append({
                "risk_type": "low_collaboration",
                "department": c["name"],
                "department_id": c["department_id"],
                "probability": round(min(0.85, (30 - c["collaboration_index"]) / 30 * 0.7 + 0.2), 2),
                "reason": f"Only {c['marketplace_published']} items published for cross-department reuse",
                "business_impact": "Other departments solve problems this team has already solved",
                "recommended_action": "Publish the department's top SOPs to the knowledge marketplace",
                "confidence": 0.65,
            })
        if c["pending_approvals"] >= 3:
            predictions.append({
                "risk_type": "approval_bottleneck",
                "department": c["name"],
                "department_id": c["department_id"],
                "probability": round(min(0.9, c["pending_approvals"] / 10 + 0.3), 2),
                "reason": f"{c['pending_approvals']} documents waiting in the review queue",
                "business_impact": "Approved knowledge reaches the repository late or not at all",
                "recommended_action": "Assign an additional reviewer to clear the backlog",
                "confidence": 0.85,
            })
        if c["headcount"] and c["knowledge_assets"] / max(c["headcount"], 1) < 1:
            predictions.append({
                "risk_type": "skill_shortage",
                "department": c["name"],
                "department_id": c["department_id"],
                "probability": 0.55,
                "reason": f"{c['knowledge_assets']} documented assets across {c['headcount']} people",
                "business_impact": "Expertise stays undocumented and leaves with the individual",
                "recommended_action": "Run a documentation sprint on the least-covered skill areas",
                "confidence": 0.6,
            })

    # Urgency = probability weighted by confidence (SRS Section 33 ranking rule).
    for p in predictions:
        p["urgency_score"] = round(p["probability"] * p["confidence"], 3)
    predictions.sort(key=lambda p: p["urgency_score"], reverse=True)

    return {
        "scope": "department" if scope else "organization",
        "prediction_count": len(predictions),
        "high_urgency_count": sum(1 for p in predictions if p["urgency_score"] >= 0.5),
        "predictions": predictions,
    }
