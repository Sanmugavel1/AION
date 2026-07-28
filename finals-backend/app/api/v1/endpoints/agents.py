"""
AION Department AI Agents.

From the handwritten notes: "All the department should have a unique AI agents to know
about the departments ... the finance dept. agent should be able to take care of all the
finance related details of the organization. Similarly, all department should have their
own specific AI agent dedicated to each one of them, and the admin dashboard should have
an complete organizational AI agent that should take care of complete flow."

Each agent is the same conversational machinery as Axon, but grounded in a *scoped*
context: a department agent is handed only its own department's people, documents,
requests and metrics, so it cannot answer about another department even if asked. The
organisation agent, on the admin dashboard, is handed the whole company.

No new scoring logic — every figure an agent quotes comes from the engines that already
exist, exactly as Axon does.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.ai.llm.llm_client import chat as llm_chat
from app.core.dependencies import AuthUser, DbSession
from app.core.exceptions import LLMError
from app.core.security import Permission
from app.models.knowledge import KnowledgeItem
from app.models.organization import Department
from app.models.user import User
from app.models.workplace import (
    ApprovalRequest,
    CompanyFinance,
    FundRequest,
    LeaveRequest,
    RequestStatus,
    SalaryRecord,
)

router = APIRouter(prefix="/agents", tags=["Department AI Agents"])


class AgentMessage(BaseModel):
    role: str
    content: str


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: List[AgentMessage] = Field(default_factory=list)


# Each department gets a name and a remit so the agent has a personality and a clear
# boundary, rather than being a generic bot with a department filter bolted on.
AGENT_PROFILE: Dict[str, Dict[str, str]] = {
    "FIN": {
        "name": "Ledger",
        "remit": "salaries, funding, profit, spend approvals and financial risk",
    },
    "HR": {
        "name": "Compass",
        "remit": "people, leave, onboarding, policies and team wellbeing",
    },
    "IT": {
        "name": "Relay",
        "remit": "systems, security, incidents, access and platform reliability",
    },
    "MFG": {
        "name": "Forge",
        "remit": "production lines, quality, changeovers and supply",
    },
    "RND": {
        "name": "Prism",
        "remit": "research, models, releases, experiments and technical risk",
    },
    "SLS": {
        "name": "Signal",
        "remit": "pipeline, deals, customers, competitors and revenue risk",
    },
}

ORG_AGENT = {
    "name": "Atlas",
    "remit": "the whole organization end to end, across every department",
}


DEPARTMENT_PROMPT = """You are {agent_name}, the AI agent for the {dept_name} department \
at {org_name}. You are a knowledgeable colleague inside this department, not a chatbot and \
not a report generator.

YOUR REMIT
You look after {remit}. You know this department and only this department. If someone asks \
about another department, say plainly that you only cover {dept_name} and suggest they ask \
that department's own agent or their head — never guess at another team's numbers.

HOW TO TALK
- Plain English. No internal field names, no snake_case, no JSON keys.
- Short paragraphs, two to four sentences. The occasional short list. No markdown tables.
- Quote real figures from the data below. If something is not in the data, say you do not \
have it rather than estimating.
- Be direct about problems. If people are waiting on approvals or nothing has been written \
down, say so.

WHAT YOU KNOW RIGHT NOW
{context}
"""

ORG_PROMPT = """You are Atlas, the organization-wide AI agent for {org_name}, on the \
administrator's dashboard. You see every department and the flow between them.

YOUR REMIT
The whole company: how each department is doing, where knowledge is being lost, what is \
waiting on a decision, and where the risk sits. You can compare departments — you are the \
only agent permitted to.

HOW TO TALK
- Plain English. No internal field names, no snake_case, no JSON keys.
- Short paragraphs, two to four sentences. No markdown tables.
- Quote real figures from the data below. If something is not in the data, say so.
- When a department is struggling, name it and say what would help.

WHAT YOU KNOW RIGHT NOW
{context}
"""


async def _department_context(db, org_id: UUID, dept: Department) -> Dict[str, Any]:
    """Everything a department agent is allowed to see, and nothing else."""
    people = (
        await db.execute(
            select(User).where(User.dept_id == dept.id, User.is_active.is_(True))
        )
    ).scalars().all()
    items = (
        await db.execute(
            select(KnowledgeItem).where(
                KnowledgeItem.org_id == org_id, KnowledgeItem.dept_id == dept.id
            )
        )
    ).scalars().all()
    leave = (
        await db.execute(
            select(LeaveRequest).where(
                LeaveRequest.dept_id == dept.id,
                LeaveRequest.status == RequestStatus.PENDING,
            )
        )
    ).scalars().all()
    approvals = (
        await db.execute(
            select(ApprovalRequest).where(
                ApprovalRequest.dept_id == dept.id,
                ApprovalRequest.status == RequestStatus.PENDING,
            )
        )
    ).scalars().all()
    funds = (
        await db.execute(
            select(FundRequest).where(FundRequest.dept_id == dept.id)
        )
    ).scalars().all()

    head = next((p for p in people if p.role == "dept_head"), None)
    ctx: Dict[str, Any] = {
        "department": dept.name,
        "head": head.full_name if head else "not assigned",
        "people_count": len(people),
        "people": [
            {"name": p.full_name, "role": p.role, "job": p.job_title} for p in people
        ],
        "documents_held": len(items),
        "documents_awaiting_review": sum(
            1 for i in items if i.workflow_status not in ("approved", "rejected")
        ),
        "document_titles": [i.title for i in items][:25],
        "leave_requests_pending": len(leave),
        "approval_requests_pending": len(approvals),
        "fund_requests": [
            {"title": f.title, "amount": f.amount, "stage": f.stage, "status": f.status}
            for f in funds
        ],
    }

    # Finance's agent additionally owns salary, funding and profit, per the notes.
    if dept.code == "FIN":
        salaries = (
            await db.execute(select(SalaryRecord).where(SalaryRecord.org_id == org_id))
        ).scalars().all()
        finance = (
            await db.execute(
                select(CompanyFinance).where(CompanyFinance.org_id == org_id)
            )
        ).scalars().all()
        ctx["company_payroll_annual"] = round(sum(s.annual_amount for s in salaries), 2)
        ctx["people_on_payroll"] = len(salaries)
        ctx["funding_and_profit"] = [
            {"type": f.entry_type, "label": f.label, "amount": f.amount, "period": f.period}
            for f in finance
        ]
        ctx["fund_requests_awaiting_finance"] = sum(
            1 for f in (await db.execute(select(FundRequest).where(
                FundRequest.org_id == org_id,
                FundRequest.stage == FundRequest.STAGE_FINANCE,
                FundRequest.status == RequestStatus.PENDING,
            ))).scalars().all()
        )
    return ctx


async def _org_context(db, org_id: UUID) -> Dict[str, Any]:
    """The whole company, for the administrator's agent."""
    depts = (
        await db.execute(
            select(Department).where(
                Department.org_id == org_id, Department.is_active.is_(True)
            )
        )
    ).scalars().all()
    people = (
        await db.execute(
            select(func.count(User.id)).where(
                User.org_id == org_id, User.is_active.is_(True)
            )
        )
    ).scalar() or 0
    items = (
        await db.execute(select(KnowledgeItem).where(KnowledgeItem.org_id == org_id))
    ).scalars().all()

    per_dept = []
    for d in depts:
        d_items = [i for i in items if str(i.dept_id) == str(d.id)]
        d_people = (
            await db.execute(
                select(func.count(User.id)).where(
                    User.dept_id == d.id, User.is_active.is_(True)
                )
            )
        ).scalar() or 0
        per_dept.append(
            {
                "department": d.name,
                "people": d_people,
                "documents": len(d_items),
                "awaiting_review": sum(
                    1 for i in d_items if i.workflow_status not in ("approved", "rejected")
                ),
            }
        )

    funds = (
        await db.execute(
            select(FundRequest).where(
                FundRequest.org_id == org_id,
                FundRequest.status == RequestStatus.PENDING,
            )
        )
    ).scalars().all()
    return {
        "organization_people": people,
        "departments": per_dept,
        "documents_total": len(items),
        "fund_requests_open": [
            {"title": f.title, "amount": f.amount, "stage": f.stage} for f in funds
        ],
        "leave_pending_company_wide": len(
            (
                await db.execute(
                    select(LeaveRequest).where(
                        LeaveRequest.org_id == org_id,
                        LeaveRequest.status == RequestStatus.PENDING,
                    )
                )
            ).scalars().all()
        ),
    }


def _render(ctx: Dict[str, Any], indent: int = 0) -> str:
    """Readable key: value text. The model reads this better than raw JSON."""
    out = []
    pad = " " * indent
    for k, v in ctx.items():
        label = k.replace("_", " ")
        if isinstance(v, list):
            if not v:
                out.append(f"{pad}{label}: none")
            elif isinstance(v[0], dict):
                out.append(f"{pad}{label}:")
                for row in v[:20]:
                    bits = ", ".join(f"{a.replace('_',' ')} {b}" for a, b in row.items())
                    out.append(f"{pad}  - {bits}")
            else:
                out.append(f"{pad}{label}: {', '.join(str(x) for x in v[:20])}")
        else:
            out.append(f"{pad}{label}: {v}")
    return "\n".join(out)


@router.get("/directory")
async def agent_directory(*, current_user: AuthUser, db: DbSession):
    """Which agents exist, and which of them this person may talk to."""
    org_id = UUID(current_user.org_id)
    depts = (
        await db.execute(
            select(Department).where(
                Department.org_id == org_id, Department.is_active.is_(True)
            )
        )
    ).scalars().all()
    cross = Permission.READ_CROSS_DEPARTMENT.value in current_user.permissions

    agents = []
    for d in depts:
        profile = AGENT_PROFILE.get(d.code or "", {})
        mine = str(d.id) == (current_user.dept_id or "")
        agents.append(
            {
                "key": (d.code or "").lower(),
                "name": profile.get("name", d.name),
                "department": d.name,
                "remit": profile.get("remit", d.name),
                "is_own_department": mine,
                # A department agent answers for its own people. Cross-department
                # roles may consult any of them.
                "available": mine or cross,
            }
        )
    agents.sort(key=lambda a: (not a["is_own_department"], a["department"]))
    return {
        "agents": agents,
        "organization_agent": {
            "key": "org",
            "name": ORG_AGENT["name"],
            "remit": ORG_AGENT["remit"],
            "available": cross,
        },
    }


@router.post("/{agent_key}/chat")
async def chat_with_agent(
    agent_key: str,
    request: AgentChatRequest,
    current_user: AuthUser,
    db: DbSession,
):
    """Talk to a department agent, or to the organization agent (`org`)."""
    org_id = UUID(current_user.org_id)
    cross = Permission.READ_CROSS_DEPARTMENT.value in current_user.permissions
    key = agent_key.strip().lower()

    if key == "org":
        if not cross:
            raise HTTPException(
                status_code=403,
                detail="The organization agent is on the administrator's dashboard. "
                       "Your own department's agent can answer for your team.",
            )
        ctx = await _org_context(db, org_id)
        org_name = "the organization"
        system = ORG_PROMPT.format(org_name=org_name, context=_render(ctx))
        agent_name = ORG_AGENT["name"]
    else:
        dept = (
            await db.execute(
                select(Department).where(
                    Department.org_id == org_id,
                    func.lower(Department.code) == key,
                    Department.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if dept is None:
            raise HTTPException(status_code=404, detail=f"No agent for '{agent_key}'")
        if not cross and str(dept.id) != (current_user.dept_id or ""):
            raise HTTPException(
                status_code=403,
                detail=f"You can talk to your own department's agent. "
                       f"{dept.name} keeps its own.",
            )
        profile = AGENT_PROFILE.get(dept.code or "", {})
        agent_name = profile.get("name", dept.name)
        ctx = await _department_context(db, org_id, dept)
        system = DEPARTMENT_PROMPT.format(
            agent_name=agent_name,
            dept_name=dept.name,
            org_name="the organization",
            remit=profile.get("remit", dept.name),
            context=_render(ctx),
        )

    messages = [{"role": m.role, "content": m.content} for m in request.history] + [
        {"role": "user", "content": request.message}
    ]
    try:
        answer = await llm_chat(messages, system=system)
    except LLMError:
        # Same posture as Axon: say the assistant is unavailable rather than
        # inventing an answer from a template.
        raise HTTPException(
            status_code=503,
            detail=f"{agent_name} is unavailable right now. The figures on this page are still live.",
        )

    return {
        "agent": agent_name,
        "scope": "organization" if key == "org" else ctx.get("department"),
        "answer": answer,
        "grounded_on": sorted(ctx.keys()),
    }
