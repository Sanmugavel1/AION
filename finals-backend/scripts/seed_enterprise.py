"""Seed the NovaTech enterprise layer (SRS Sections 5, 6, 17, 40).

Creates the six departments and places the organization's *existing* people into them
with the five-tier role model. Reusing the existing accounts matters: those people are
already nodes in the knowledge graph with real KNOWS edges, so department scorecards
reflect real ownership instead of a parallel cast of invented employees.

Idempotent. demo@aion.ai stays org_admin so the current dashboard login is unaffected.
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select

from app.core.database import AsyncSessionFactory
from app.core.security import UserRole, hash_password
from app.models.enterprise import TimelineEvent
from app.models.knowledge import KnowledgeItem
from app.models.organization import Department, Organization
from app.models.user import User

PASSWORD = "DemoPass123!"
ANCHOR_EMAIL = "demo@aion.ai"

# name, code, domains whose knowledge belongs to this department
DEPARTMENTS = [
    ("Human Resources", "HR", ["hr", "policy"]),
    ("Research & Development", "RND", ["engineering", "product"]),
    ("Finance", "FIN", ["finance"]),
    ("Manufacturing", "MFG", ["operations"]),
    ("Sales & Marketing", "SLS", ["sales"]),
    ("Information Technology", "IT", ["security", "legal"]),
]

# existing username -> (dept code, role). Heads and managers are drawn from the same
# people the graph already knows, so ownership and org chart agree.
ASSIGNMENTS = {
    "alice.chen":     ("RND", UserRole.DEPT_HEAD),
    "marcus.webb":    ("RND", UserRole.MANAGER),
    "wei.zhang":      ("RND", UserRole.EMPLOYEE),
    "priya.nair":     ("HR",  UserRole.DEPT_HEAD),
    "nina.kowalski":  ("HR",  UserRole.MANAGER),
    "grace.osei":     ("FIN", UserRole.DEPT_HEAD),
    "jordan.lee":     ("FIN", UserRole.MANAGER),
    "tom.fitzgerald": ("MFG", UserRole.DEPT_HEAD),
    "omar.haddad":    ("MFG", UserRole.MANAGER),
    "sofia.reyes":    ("SLS", UserRole.DEPT_HEAD),
    "elena.petrova":  ("SLS", UserRole.MANAGER),
    "daniel.kim":     ("IT",  UserRole.DEPT_HEAD),
}

TITLES = {
    UserRole.DEPT_HEAD: "Head of {dept}",
    UserRole.MANAGER: "{dept} Manager",
    UserRole.EMPLOYEE: "{dept} Specialist",
}

# Executive tier is genuinely new — no existing account plays this part (Section 27).
EXECUTIVES = [
    ("Rohan Desai", "rohan.desai.exec", "Chief Executive Officer"),
    ("Amara Nwosu", "amara.nwosu.exec", "Chief Knowledge Officer"),
]


async def main() -> None:
    async with AsyncSessionFactory() as db:
        anchor = (await db.execute(
            select(User).where(User.email == ANCHOR_EMAIL)
        )).scalar_one_or_none()
        if anchor is None:
            print(f"No {ANCHOR_EMAIL} account — run seed_demo_data.py first.")
            return
        org = (await db.execute(
            select(Organization).where(Organization.id == anchor.org_id)
        )).scalar_one()
        print(f"organization: {org.name}")

        # --- departments ---------------------------------------------------
        dept_by_code, created_d = {}, 0
        for name, code, _ in DEPARTMENTS:
            d = (await db.execute(select(Department).where(
                Department.org_id == org.id, Department.code == code
            ))).scalar_one_or_none()
            if d is None:
                d = Department(org_id=org.id, name=name, code=code, is_active=True)
                db.add(d)
                created_d += 1
            else:
                d.name, d.is_active = name, True
            dept_by_code[code] = d
        await db.flush()
        print(f"departments: {len(dept_by_code)} ({created_d} created)")

        # seed_demo_data() creates its own starter departments (Engineering, Product,
        # Sales, Operations, Security) before this script ever runs. Once the real
        # six are in place those are just clutter — deactivate anything else so
        # department-count and org-wide aggregates (command center, scorecards)
        # aren't polluted with empty leftover departments.
        stale = (await db.execute(select(Department).where(
            Department.org_id == org.id,
            Department.is_active.is_(True),
            Department.code.notin_(dept_by_code.keys()),
        ))).scalars().all()
        for d in stale:
            d.is_active = False
        if stale:
            print(f"deactivated stale starter departments: {[d.code for d in stale]}")

        # --- place existing people into the org chart ------------------------
        placed = 0
        for username, (code, role) in ASSIGNMENTS.items():
            u = (await db.execute(select(User).where(
                User.username == username, User.org_id == org.id
            ))).scalar_one_or_none()
            if u is None:
                print(f"  ! no account '{username}', skipping")
                continue
            dept = dept_by_code[code]
            u.dept_id, u.role = dept.id, role.value
            u.job_title = TITLES[role].format(dept=dept.name)
            if role is UserRole.DEPT_HEAD:
                dept.head_user_id = u.id
            placed += 1
        print(f"people placed into departments: {placed}")

        # Anyone left in this org without a department becomes an IT employee rather
        # than an orphan the department-scoped API would reject outright.
        strays = (await db.execute(select(User).where(
            User.org_id == org.id, User.dept_id.is_(None), User.role == "analyst"
        ))).scalars().all()
        for u in strays:
            u.dept_id = dept_by_code["IT"].id
            u.role = UserRole.EMPLOYEE.value
            u.job_title = "Information Technology Specialist"
        if strays:
            print(f"unassigned analysts placed in IT: {len(strays)}")

        # --- executive tier ---------------------------------------------------
        pw = hash_password(PASSWORD)
        created_e = 0
        for full_name, username, title in EXECUTIVES:
            u = (await db.execute(
                select(User).where(User.username == username)
            )).scalar_one_or_none()
            if u is None:
                u = User(
                    org_id=org.id, email=f"{username}@novatech.example",
                    username=username, full_name=full_name, hashed_password=pw,
                    is_active=True, is_verified=True,
                )
                db.add(u)
                created_e += 1
            u.role, u.job_title, u.dept_id = UserRole.EXECUTIVE.value, title, None
        print(f"executives: {created_e} created ({len(EXECUTIVES)} total)")

        # --- map knowledge to departments by domain ---------------------------
        domain_to_dept = {
            dom: dept_by_code[code].id
            for _n, code, domains in DEPARTMENTS for dom in domains
        }
        items = (await db.execute(
            select(KnowledgeItem).where(KnowledgeItem.org_id == org.id)
        )).scalars().all()
        assigned = 0
        for it in items:
            target = domain_to_dept.get((it.domain or "").lower())
            if target and it.dept_id != target:
                it.dept_id = target
                assigned += 1
        print(f"knowledge mapped to departments: {assigned} of {len(items)}")

        # --- timeline --------------------------------------------------------
        have = (await db.execute(select(func.count()).select_from(TimelineEvent).where(
            TimelineEvent.org_id == org.id
        ))).scalar() or 0
        if have == 0:
            now = datetime.now(timezone.utc)
            for etype, title, code, days in [
                ("leadership_change", "Rohan Desai appointed Chief Executive Officer", None, 900),
                ("company_event", "Bengaluru R&D centre opened", "RND", 720),
                ("policy", "Global data-handling policy published", "IT", 540),
                ("innovation", "Autonomous inspection prototype cleared field trials", "RND", 360),
                ("project", "Cold-chain logistics programme kicked off", "MFG", 240),
                ("training", "Company-wide security awareness programme completed", "IT", 120),
                ("company_event", "Passed 500 employees across 15 countries", None, 60),
            ]:
                db.add(TimelineEvent(
                    org_id=org.id,
                    dept_id=dept_by_code[code].id if code else None,
                    event_type=etype, title=title,
                    occurred_at=now - timedelta(days=days), source_type="seed",
                ))
            print("timeline: 7 milestones seeded")
        else:
            print(f"timeline: {have} event(s) already present")

        await db.commit()

        print("\ndepartment roster:")
        for _n, code, _d in DEPARTMENTS:
            d = dept_by_code[code]
            ppl = (await db.execute(select(func.count()).select_from(User).where(
                User.dept_id == d.id))).scalar()
            kn = (await db.execute(select(func.count()).select_from(KnowledgeItem).where(
                KnowledgeItem.dept_id == d.id))).scalar()
            head = (await db.execute(select(User.full_name).where(
                User.id == d.head_user_id))).scalar() if d.head_user_id else None
            print(f"  {d.name:24s} {ppl:2d} people | {kn:2d} items | head: {head or '—'}")
        print(f"\nnew executive accounts use password: {PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
