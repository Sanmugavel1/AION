"""
Seed the workplace layer with real records, not placeholders.

Salary bands per designation, company funding rounds and quarterly profit, plus a
handful of live leave requests, approval requests and one fund request part-way
through the chain — so every dashboard has something true on it the moment you log in.

    python scripts/seed_workplace_data.py --apply
"""
from __future__ import annotations

import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionFactory
from app.models.organization import Department
from app.models.user import User
from app.models.workplace import (
    ApprovalRequest,
    CompanyFinance,
    EmployeeProfileDetail,
    FundRequest,
    LeaveRequest,
    RequestStatus,
    SalaryRecord,
)

# Annual salary by seniority, in USD. Heads highest, then managers, then the rest,
# with associates and trainees lowest.
def _band_for(role: str, title: str) -> tuple[str, float]:
    t = (title or "").lower()
    if role == "dept_head":
        return "leadership", 185_000
    if role == "manager":
        return "management", 132_000
    if "associate" in t or "trainee" in t:
        return "entry", 62_000
    if "senior" in t or "lead" in t or "principal" in t:
        return "senior", 118_000
    if "technician" in t or "coordinator" in t or "support" in t:
        return "operations", 71_000
    return "professional", 94_000


FUNDING = [
    ("Series B", 42_000_000, "2024-Q2", "Led by Meridian Ventures"),
    ("Series C", 78_000_000, "2025-Q4", "Led by Northgate Capital"),
    ("Equipment facility", 12_500_000, "2026-Q1", "Asset-backed, manufacturing lines"),
]
PROFIT = [
    ("Operating profit", 4_100_000, "2025-Q3"),
    ("Operating profit", 5_350_000, "2025-Q4"),
    ("Operating profit", 3_980_000, "2026-Q1"),
    ("Operating profit", 6_220_000, "2026-Q2"),
]


async def main(apply: bool) -> None:
    async with AsyncSessionFactory() as db:
        admin = (
            await db.execute(select(User).where(User.email == "demo@aion.ai"))
        ).scalar_one()
        org_id = admin.org_id

        users = (
            await db.execute(
                select(User).where(User.org_id == org_id, User.is_active.is_(True))
            )
        ).scalars().all()
        depts = {
            d.code: d
            for d in (
                await db.execute(
                    select(Department).where(
                        Department.org_id == org_id, Department.is_active.is_(True)
                    )
                )
            ).scalars().all()
        }
        details = {
            d.user_id: d
            for d in (await db.execute(select(EmployeeProfileDetail))).scalars().all()
        }

        # ---- salaries -------------------------------------------------------
        existing_sal = {
            s.user_id
            for s in (
                await db.execute(select(SalaryRecord).where(SalaryRecord.org_id == org_id))
            ).scalars().all()
        }
        made_sal = 0
        for u in users:
            if u.id in existing_sal or u.role == "org_admin":
                continue
            band, amount = _band_for(u.role, u.job_title or "")
            d = details.get(u.id)
            if apply:
                db.add(
                    SalaryRecord(
                        org_id=org_id, user_id=u.id, dept_id=u.dept_id,
                        annual_amount=amount, band=band,
                        effective_from=(d.joining_date if d and d.joining_date else date(2024, 1, 1)),
                    )
                )
            made_sal += 1

        # ---- funding and profit --------------------------------------------
        existing_fin = {
            (f.entry_type, f.label, f.period)
            for f in (
                await db.execute(select(CompanyFinance).where(CompanyFinance.org_id == org_id))
            ).scalars().all()
        }
        made_fin = 0
        for label, amount, period, note in FUNDING:
            if ("funding", label, period) in existing_fin:
                continue
            if apply:
                db.add(CompanyFinance(org_id=org_id, entry_type="funding", label=label,
                                      amount=amount, period=period, note=note))
            made_fin += 1
        for label, amount, period in PROFIT:
            if ("profit", label, period) in existing_fin:
                continue
            if apply:
                db.add(CompanyFinance(org_id=org_id, entry_type="profit", label=label,
                                      amount=amount, period=period))
            made_fin += 1

        # ---- a few live requests so queues are not empty ---------------------
        heads = {
            str(u.dept_id): u for u in users if u.role == "dept_head" and u.dept_id
        }
        by_dept: dict[str, list[User]] = {}
        for u in users:
            if u.dept_id and u.role == "employee":
                by_dept.setdefault(str(u.dept_id), []).append(u)

        have_leave = (
            await db.execute(select(LeaveRequest).where(LeaveRequest.org_id == org_id))
        ).scalars().all()
        have_req = (
            await db.execute(select(ApprovalRequest).where(ApprovalRequest.org_id == org_id))
        ).scalars().all()

        made_leave, made_req = 0, 0
        if not have_leave:
            today = date.today()
            plan = [("RND", 5, 12), ("FIN", 3, 20), ("IT", 2, 30), ("HR", 4, 9)]
            for code, days, offset in plan:
                d = depts.get(code)
                if not d:
                    continue
                staff = by_dept.get(str(d.id)) or []
                if not staff:
                    continue
                who = staff[0]
                start = today + timedelta(days=offset)
                if apply:
                    db.add(
                        LeaveRequest(
                            org_id=org_id, dept_id=d.id, requester_id=who.id,
                            approver_id=heads.get(str(d.id)).id if heads.get(str(d.id)) else None,
                            start_date=start, end_date=start + timedelta(days=days - 1),
                            days=days, leave_type="annual",
                            reason="Family visit" if days > 3 else "Personal",
                            status=RequestStatus.PENDING, leave_year=start.year,
                        )
                    )
                made_leave += 1

        if not have_req:
            plan = [
                ("RND", "project", "Adverse-weather evaluation set expansion"),
                ("MFG", "policy", "Revised first-article inspection rule"),
                ("SLS", "project", "Competitive battlecard refresh"),
            ]
            for code, kind, title in plan:
                d = depts.get(code)
                if not d:
                    continue
                staff = by_dept.get(str(d.id)) or []
                if not staff:
                    continue
                who = staff[-1]
                if apply:
                    db.add(
                        ApprovalRequest(
                            org_id=org_id, dept_id=d.id, requester_id=who.id,
                            approver_id=heads.get(str(d.id)).id if heads.get(str(d.id)) else None,
                            request_type=kind, title=title,
                            detail="Raised for the department head to review.",
                            status=RequestStatus.PENDING,
                        )
                    )
                made_req += 1

        # ---- one fund request sitting with Finance --------------------------
        have_fund = (
            await db.execute(select(FundRequest).where(FundRequest.org_id == org_id))
        ).scalars().all()
        made_fund = 0
        if not have_fund and depts.get("MFG"):
            mfg = depts["MFG"]
            raiser = heads.get(str(mfg.id))
            if raiser and apply:
                db.add(
                    FundRequest(
                        org_id=org_id, dept_id=mfg.id, requester_id=raiser.id,
                        title="Second calibration rig for Line 3",
                        amount=185_000, purpose="Removes the single-rig bottleneck at changeover.",
                        stage=FundRequest.STAGE_FINANCE, status=RequestStatus.PENDING,
                    )
                )
            made_fund = 1 if raiser else 0

        if apply:
            await db.commit()

        print(f"  salary records   : {made_sal}")
        print(f"  finance entries  : {made_fin}")
        print(f"  leave requests   : {made_leave}")
        print(f"  approval requests: {made_req}")
        print(f"  fund requests    : {made_fund}")


if __name__ == "__main__":
    asyncio.run(main(apply="--apply" in sys.argv))
