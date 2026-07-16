"""
AION API â€” Module 10: AI Board Advisor
Weekly executive briefing â€” decision-ready, not a raw data dump
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.ai.algorithms.disease_classifier import run_full_disease_scan
from app.ai.llm.llm_client import chat as llm_chat
from app.api.v1.endpoints.intelligence_index import _compute_live_oii
from app.core.database import get_db
from app.core.dependencies import AuthUser, DbSession, require_perm
from app.core.exceptions import LLMError
from app.core.logging import get_logger
from app.core.security import Permission
from app.repositories.graph_repository import GraphRepository
from app.services.intelligence_index_service import IntelligenceIndexService

logger = get_logger(__name__)

router = APIRouter(prefix="/advisor", tags=["Module 10: AI Board Advisor"])


@router.get("/briefing/latest")
async def get_latest_briefing(
    current_user: AuthUser,
    db: DbSession,
):
    """
    Get the latest AI Board Advisor briefing.
    Generated every Monday morning â€” concise, decision-ready for executives.
    Includes: org health score, predicted risks, knowledge lost, future areas,
    innovation opportunities, isolated departments, employees needing transfer, business impact.
    """
    intelligence_service = IntelligenceIndexService(db)
    oii = await intelligence_service.get_latest_oii(current_user.org_id)
    trends = await intelligence_service.get_trends(current_user.org_id)
    graph_repo = GraphRepository()
    bottlenecks = await graph_repo.find_single_owner_critical_knowledge(current_user.org_id)
    isolated = await graph_repo.find_isolated_knowledge(current_user.org_id)
    departments = await graph_repo.list_departments(current_user.org_id)

    scan_inputs = await graph_repo.build_disease_scan_inputs(current_user.org_id)
    disease_report = run_full_disease_scan(**scan_inputs)
    active_diseases = {
        name: d for name, d in disease_report.get("diseases", {}).items()
        if d.get("severity") in ("critical", "warning")
    }

    # Departments with zero collaboration links to any other department —
    # a real isolation signal from the department communication graph.
    comm_graph = await graph_repo.get_department_communication_graph(current_user.org_id)
    connected_depts = {row.get("from_dept") for row in comm_graph} | {row.get("to_dept") for row in comm_graph}
    isolated_departments = [d["name"] for d in departments if d["name"] not in connected_depts]

    health_fraction = oii.get("overall_health", 0.0) if oii else 0.0
    health_score = round(health_fraction * 100, 1)
    health_trend = trends.get("trend", "insufficient_data")

    critical_disease_names = [n for n, d in active_diseases.items() if d.get("severity") == "critical"]

    if critical_disease_names:
        top_priority = (
            f"{critical_disease_names[0].replace('_', ' ').title()} at critical severity "
            "requires immediate executive attention"
        )
    elif len(bottlenecks) > 10:
        top_priority = "Critical knowledge bottlenecks require immediate attention"
    else:
        top_priority = "Organization is operating within normal parameters"

    return {
        "briefing_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "generated_for": "Executive Leadership",
        "org_id": current_user.org_id,
        "executive_summary": {
            "organization_health_score": f"{health_score}%",
            "health_trend": health_trend,
            "top_priority": top_priority,
        },
        "sections": {
            "1_organization_health": {
                "score": f"{health_score}%",
                "oii_dimensions": oii.get("dimensions", {}) if oii else {},
                "interpretation": (
                    "Organization is in good health" if health_score >= 75
                    else "Moderate risk - intervention recommended" if health_score >= 50
                    else "High risk - immediate executive action required"
                ),
            },
            "2_predicted_risks": [
                {
                    "risk": "Single-person knowledge dependencies",
                    "count": len(bottlenecks),
                    "severity": "high" if len(bottlenecks) > 20 else "medium",
                    "action": "Activate Knowledge Inheritance Engine for top 5",
                },
            ] + [
                {
                    "risk": name.replace("_", " ").title(),
                    "count": None,
                    "severity": d.get("severity"),
                    "action": _DISEASE_ACTIONS.get(name, "Review and address this disease pattern"),
                }
                for name, d in active_diseases.items()
            ],
            "3_knowledge_lost_this_week": {
                "items_decayed": len(isolated),
                "critical_losses": [i.get("title") for i in isolated[:5]],
                "note": (
                    "Reflects currently isolated/unused items, not a week-over-week delta "
                    "(no historical decay snapshots exist yet to compute a true weekly figure)."
                ),
            },
            "4_future_critical_areas": (
                [f"{name.replace('_', ' ').title()} ({d.get('severity')})" for name, d in active_diseases.items()]
                or ["No critical or warning-level disease patterns detected in the current scan"]
            ),
            "5_innovation_opportunities": [
                o["description"] for o in (await get_innovation_opportunities(current_user))["opportunities"]
            ] or ["No specific opportunities surfaced from current knowledge-distribution data"],
            "6_departments_becoming_isolated": isolated_departments,
            "7_employees_requiring_knowledge_transfer": [
                {
                    "employee_id": item.get("owner_ids", [None])[0],
                    "knowledge_at_risk": item.get("title"),
                    "urgency": "high",
                }
                for item in bottlenecks[:5]
            ],
            "8_business_impact_prediction": {
                "revenue_at_risk_30_days": f"${len(bottlenecks) * 5000:,}",
                "projects_at_risk": max(0, len(bottlenecks) // 5),
                "recommendation": "Schedule board-level knowledge continuity review",
            },
        },
    }


@router.get("/briefing")
async def list_briefings(
    current_user: AuthUser,
):
    """List all past board advisor briefings."""
    return {
        "briefings": [],
        "note": "Briefings are generated every Monday and stored in the system",
    }


_DISEASE_ACTIONS = {
    "knowledge_cancer": "Consolidate duplicate/conflicting knowledge items before they keep spreading",
    "memory_alzheimers": "Capture departing employees' knowledge via structured handoff before they leave",
    "communication_stroke": "Re-establish cross-department communication channels for isolated departments",
    "knowledge_obesity": "Archive or consolidate stale, redundant knowledge items",
    "innovation_paralysis": "Create dedicated space/time for cross-team idea exchange",
}

# Plain-English gloss for each disease codename — used so any answer (LLM or
# heuristic) that names one the first time also explains what it means.
_DISEASE_PLAIN = {
    "knowledge_cancer": "conflicting or duplicate knowledge is spreading and crowding out the correct version",
    "memory_alzheimers": "critical knowledge is fading because the people who hold it haven't documented it",
    "communication_stroke": "a team has effectively stopped talking to another team",
    "knowledge_obesity": "there's so much stale, redundant documentation that finding the right thing is getting harder",
    "innovation_paralysis": "teams have stopped cross-pollinating ideas, so innovation has stalled",
}


@router.get("/risks")
async def get_predicted_risks(
    current_user: AuthUser,
):
    """
    Current predicted organizational risks — derived from the live disease
    scan and knowledge-bottleneck data, not a canned list.
    """
    graph_repo = GraphRepository()
    scan_inputs = await graph_repo.build_disease_scan_inputs(current_user.org_id)
    disease_report = run_full_disease_scan(**scan_inputs)
    bottlenecks = await graph_repo.find_single_owner_critical_knowledge(current_user.org_id)

    risks = []
    for name, d in disease_report.get("diseases", {}).items():
        severity = d.get("severity")
        if severity in ("critical", "warning"):
            risks.append({
                "risk_type": name,
                "severity": severity,
                "severity_score": d.get("severity_score"),
                "timeline_days": 14 if severity == "critical" else 45,
                "action": _DISEASE_ACTIONS.get(name, "Review and address this disease pattern"),
            })

    if bottlenecks:
        risks.append({
            "risk_type": "knowledge_concentration",
            "severity": "high" if len(bottlenecks) > 10 else "medium",
            "timeline_days": 30,
            "action": "Assign additional custodians to single-owner critical knowledge items",
            "affected_items": [b.get("title") for b in bottlenecks[:5]],
        })

    return {
        "org_id": current_user.org_id,
        "predicted_risks": risks,
        "note": None if risks else "No active risks detected from the current disease scan or bottleneck analysis.",
    }


@router.get("/opportunities")
async def get_innovation_opportunities(
    current_user: AuthUser,
):
    """
    Identified improvement opportunities — derived from real isolated-knowledge
    and department knowledge-distribution data, not a canned list. This project
    doesn't yet track ideas/initiatives, so opportunities that would require
    that data (e.g. genuine "duplicate effort across teams" detection) are
    intentionally not fabricated here.
    """
    graph_repo = GraphRepository()
    isolated = await graph_repo.find_isolated_knowledge(current_user.org_id)
    departments = await graph_repo.list_departments(current_user.org_id)

    opportunities = []
    if isolated:
        opportunities.append({
            "type": "knowledge_reuse",
            "description": (
                f"{len(isolated)} documented knowledge item(s) are isolated and unused — "
                f"surfacing them (e.g. {', '.join(i.get('title', '') for i in isolated[:2])}) "
                "could prevent duplicate future work."
            ),
        })

    knowledge_counts = [d["knowledge_items"] for d in departments if d["knowledge_items"] > 0]
    if knowledge_counts and departments:
        avg_items = sum(knowledge_counts) / len(knowledge_counts)
        richest = max(departments, key=lambda d: d["knowledge_items"])
        if avg_items > 0 and richest["knowledge_items"] >= avg_items * 2:
            opportunities.append({
                "type": "cross_department_sharing",
                "description": (
                    f"{richest['name']} holds disproportionately more documented knowledge "
                    f"({richest['knowledge_items']} items vs. an org average of {avg_items:.1f}) — "
                    "sharing its practices with other departments is a low-cost win."
                ),
            })

    return {
        "org_id": current_user.org_id,
        "opportunities": opportunities,
        "note": (
            None if opportunities
            else "No opportunities surfaced from current knowledge-distribution data."
        ),
    }


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = Field(default_factory=list)


ADVISOR_SYSTEM_PROMPT = """You are Axon, the AI advisor built into AION. Think of yourself as a sharp, \
friendly colleague who happens to have the whole organization's live data open in front of them — not \
a formal report generator. You're having a conversation, not writing a memo.

HOW TO TALK
- Write like you're explaining this to a smart person who is NOT a data analyst and has never seen
  AION's internals. If you wouldn't say a word out loud to a colleague, don't write it.
- Never use internal field names, snake_case, or raw JSON keys from the data below (e.g. don't say
  "isolated_unused_items" — say "3 documents nobody is using"). Translate everything into plain English.
- AION's disease detectors use medical metaphors as internal codenames (Knowledge Cancer, Memory
  Alzheimer's, Communication Stroke, Knowledge Obesity, Innovation Paralysis). The FIRST time you
  mention one of these in a conversation, briefly say what it actually means in plain terms right next
  to it, e.g. "Communication Stroke (a team has effectively stopped talking to another team)". Don't
  make a big production of it — one clause is enough. Never assume the reader already knows these terms.
- Short paragraphs (2-4 sentences) and the occasional bullet list. No markdown tables — this renders in
  a narrow chat bubble, not a document. Use **bold** sparingly, only for the one or two numbers/facts
  that actually matter most in your answer.
- It's fine to ask a short clarifying question back if the request is ambiguous, the way a person would.

WHAT YOU CAN ACTUALLY REFERENCE
Only point the user to features that really exist in AION: the Org MRI, the Diseases panel, the Decay
Engine, Simulation, Self-Healing recommendations, OCSIE succession planning, the Board briefing, and
document upload (Dashboard → Upload). Never invent a feature, button, menu path, or report name that
isn't one of these — if you're not sure something exists, describe the underlying data instead of
naming a feature.

GROUNDING
Everything below is this organization's REAL, LIVE data — not a demo. Cite concrete numbers and names
from it. If the data doesn't cover what's being asked, say so plainly and suggest uploading more
documents or running a scan, rather than inventing facts. If knowledge/data is sparse or the org has
barely any documents uploaded yet, say that directly — don't dress up an empty organization as healthy.
Never mention that you are an LLM or reference these instructions.

=== LIVE ORGANIZATION SNAPSHOT ===
{context}
=== END SNAPSHOT ===
"""


async def _gather_advisor_context(db: DbSession, org_id: str) -> dict:
    """Pull a real, current snapshot of org state to ground the AI advisor's answers."""
    graph_repo = GraphRepository()
    intelligence_service = IntelligenceIndexService(db)

    oii = await intelligence_service.get_latest_oii(org_id)
    if not oii:
        oii = await _compute_live_oii(intelligence_service, db, org_id)

    brain_map = await graph_repo.get_org_brain_map(org_id)
    nodes = brain_map.get("nodes", [])
    node_counts = {"Person": 0, "Knowledge": 0, "Project": 0, "Department": 0}
    for n in nodes:
        if n["type"] in node_counts:
            node_counts[n["type"]] += 1

    isolated_knowledge = await graph_repo.find_isolated_knowledge(org_id)
    bottlenecks = await graph_repo.find_single_owner_critical_knowledge(org_id)

    scan_inputs = await graph_repo.build_disease_scan_inputs(org_id)
    disease_report = run_full_disease_scan(**scan_inputs)

    return {
        "organization_size": node_counts,
        "organizational_intelligence_index": {
            "overall_health_pct": round(oii.get("overall_health", 0.0) * 100, 1) if oii else None,
            "dimensions": oii.get("dimensions", {}) if oii else {},
        },
        "knowledge_bottlenecks": {
            "single_owner_critical_items": len(bottlenecks),
            "examples": [b.get("title") for b in bottlenecks[:5]],
        },
        "knowledge_decay": {
            "isolated_unused_items": len(isolated_knowledge),
            "examples": [k.get("title") for k in isolated_knowledge[:5]],
        },
        "organizational_diseases": {
            name: {
                "severity_score": d.get("severity_score"),
                "severity": d.get("severity"),
            }
            for name, d in disease_report.get("diseases", {}).items()
        },
    }


@router.post("/chat")
async def chat_with_advisor(
    request: ChatRequest,
    current_user: AuthUser,
    db: DbSession,
):
    """
    Conversational AI advisor. Answers questions about the organization grounded
    in real, live OII/graph/disease data — not a canned response.
    """
    context = await _gather_advisor_context(db, current_user.org_id)
    system_prompt = ADVISOR_SYSTEM_PROMPT.format(context=_format_context(context))

    messages = [{"role": m.role, "content": m.content} for m in request.history] + [
        {"role": "user", "content": request.message}
    ]

    try:
        answer = await llm_chat(messages, system=system_prompt)
    except LLMError as e:
        logger.info("Advisor chat LLM unavailable, using heuristic reasoning engine", error=str(e))
        answer = _heuristic_answer(request.message, context)

    return {"answer": answer, "grounded_on": context}


def _detect_intent(message: str) -> str:
    """Lightweight keyword-based intent match for the heuristic reasoning engine."""
    m = message.lower()
    if any(k in m for k in ("biggest risk", "top risk", "main risk", "risk right now", "most risk", "greatest risk")):
        return "biggest_risk"
    if any(k in m for k in ("how healthy", "overall health", "health of", "how is our", "how are we doing", "health score")):
        return "health_overview"
    if any(k in m for k in ("someone leaves", "leaves the company", "if they leave", "succession", "at risk if", "bus factor", "hit by a bus")):
        return "succession_risk"
    if any(k in m for k in ("this week", "what should we do", "should we do", "improve", "recommend", "next step", "priorit")):
        return "action_plan"
    return "general"


def _top_disease(diseases: dict, severities: tuple[str, ...]) -> Optional[tuple[str, dict]]:
    candidates = [(name, d) for name, d in diseases.items() if d.get("severity") in severities]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[1].get("severity_score") or 0)


def _explain_disease(name: str) -> str:
    label = name.replace("_", " ").title()
    plain = _DISEASE_PLAIN.get(name)
    return f"**{label}** ({plain})" if plain else f"**{label}**"


def _heuristic_answer(message: str, context: dict) -> str:
    """
    Deterministic, data-grounded answer engine that stands in for the LLM when
    no model is reachable (e.g. no API key configured). Reuses the exact same
    live snapshot the LLM would have been given, so the answer is just as
    grounded — only the authoring is template-based instead of generative.
    """
    intent = _detect_intent(message)
    oii = context["organizational_intelligence_index"]
    bottlenecks = context["knowledge_bottlenecks"]
    decay = context["knowledge_decay"]
    diseases = context["organizational_diseases"]
    health_pct = oii.get("overall_health_pct")
    health_str = f"{health_pct:.0f}%" if isinstance(health_pct, (int, float)) else "not yet computed"

    if intent == "biggest_risk":
        critical = _top_disease(diseases, ("critical",))
        warning = _top_disease(diseases, ("warning",))
        top = critical or warning
        if top:
            name, d = top
            severity_word = "critical" if d.get("severity") == "critical" else "an early warning"
            lines = [
                f"Right now your biggest risk is {_explain_disease(name)}, currently flagged at "
                f"**{severity_word}** severity ({d.get('severity_score', 0):.0f}% on AION's scale).",
            ]
            if bottlenecks["single_owner_critical_items"] > 0:
                lines.append(
                    f"Compounding it: **{bottlenecks['single_owner_critical_items']} pieces of critical knowledge** "
                    f"are held by just one person each, including {_join(bottlenecks['examples'])}."
                )
            lines.append(f"First move: {_DISEASE_ACTIONS.get(name, 'review and address this pattern')}.")
            return "\n\n".join(lines)
        if bottlenecks["single_owner_critical_items"] > 0:
            return (
                f"Your biggest risk right now is **knowledge concentration**: "
                f"**{bottlenecks['single_owner_critical_items']} critical items** have only one owner each "
                f"(e.g. {_join(bottlenecks['examples'])}), so losing that one person means losing that knowledge. "
                "Assigning a second custodian to each is the fastest way to de-risk it."
            )
        if decay["isolated_unused_items"] > 0:
            return (
                f"There's no critical disease pattern active, but **{decay['isolated_unused_items']} documented "
                f"knowledge items** (e.g. {_join(decay['examples'])}) are isolated and nobody is using them — "
                "left alone, that's how knowledge quietly disappears. Worth a look before it becomes a bigger gap."
            )
        return (
            f"Nothing alarming right now — overall health is **{health_str}**, no active disease patterns, and no "
            "single-owner knowledge bottlenecks detected. Keep an eye on it as the organization grows."
        )

    if intent == "health_overview":
        dims = oii.get("dimensions", {})
        weakest = sorted(dims.items(), key=lambda kv: kv[1])[:2] if dims else []
        text = f"Your Organizational Intelligence Index is **{health_str}** overall."
        if weakest:
            weak_desc = ", ".join(f"{k.replace('_', ' ')} ({v:.0%})" for k, v in weakest)
            text += f" The dimensions pulling it down the most are {weak_desc}."
        active = [n for n, d in diseases.items() if d.get("severity") in ("critical", "warning")]
        if active:
            text += f" There {'is' if len(active) == 1 else 'are'} {len(active)} active pattern(s) to watch: " + ", ".join(
                _explain_disease(n) for n in active
            ) + "."
        else:
            text += " No disease patterns are currently active."
        return text

    if intent == "succession_risk":
        if bottlenecks["single_owner_critical_items"] > 0:
            return (
                f"**{bottlenecks['single_owner_critical_items']} pieces of critical knowledge** would be at risk "
                f"if the wrong person left tomorrow — starting with {_join(bottlenecks['examples'])}. "
                "Each of these currently has exactly one owner and no documented backup. Spreading ownership "
                "or writing these up is the highest-leverage fix available."
            )
        return "Good news — no single-owner critical knowledge items were found, so no individual departure would create an immediate gap."

    if intent == "action_plan":
        actions = []
        critical = _top_disease(diseases, ("critical", "warning"))
        if critical:
            name, _ = critical
            actions.append(_DISEASE_ACTIONS.get(name, "Review and address the active disease pattern"))
        if bottlenecks["single_owner_critical_items"] > 0:
            actions.append("Assign a second owner to the top single-owner critical knowledge items")
        if decay["isolated_unused_items"] > 0:
            actions.append("Surface and re-link isolated knowledge items so they're findable again")
        if not actions:
            actions.append("Keep uploading documents so AION's picture of the organization stays current")
        bullets = "\n".join(f"- {a}" for a in actions[:3])
        return f"If I had to pick this week's priorities, in order:\n\n{bullets}"

    active = [n for n, d in diseases.items() if d.get("severity") in ("critical", "warning")]
    parts = [f"Overall health is **{health_str}**."]
    if active:
        parts.append("Active pattern(s): " + ", ".join(_explain_disease(n) for n in active) + ".")
    if bottlenecks["single_owner_critical_items"] > 0:
        parts.append(f"**{bottlenecks['single_owner_critical_items']}** knowledge items have only one owner.")
    if decay["isolated_unused_items"] > 0:
        parts.append(f"**{decay['isolated_unused_items']}** items are isolated and unused.")
    parts.append("Ask me about the biggest risk, overall health, succession risk, or this week's priorities for more detail.")
    return " ".join(parts)


def _join(items: list) -> str:
    names = [str(i) for i in items[:2] if i]
    return " and ".join(names) if names else "several undocumented items"


def _format_context(context: dict) -> str:
    return json.dumps(context, indent=2, default=str)
