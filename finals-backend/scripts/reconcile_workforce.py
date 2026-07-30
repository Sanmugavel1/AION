"""
Reconcile the workforce to exactly 61: 6 departments x 10 (1 head + 9), plus 1 admin.

`seed_workforce.py` matched existing people by name but left their old `role` alone,
which produced two wrong outcomes in Manufacturing: Omar Haddad stayed a `manager`
although the roster lists him as the head, and Amara Nwosu stayed an `executive` while
being placed as an assembly technician. It also left two people who are not on any
roster (a second Manufacturing head, and an executive) still active, taking the count
to 63.

This script makes the roster authoritative for role, and deactivates anyone in the
organization who is neither on a roster nor the single administrator. Deactivation is
reversible — `is_active` is flipped, nothing is deleted.

    python scripts/reconcile_workforce.py            # report
    python scripts/reconcile_workforce.py --apply    # write
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionFactory
from app.core.security import UserRole
from app.models.organization import Department
from app.models.user import User

from scripts.seed_workforce import WORKFORCE

#: The one account that sits outside the six departments.
ADMIN_EMAIL = "demo@aion.ai"


def _roster_roles() -> dict[str, tuple[str, str]]:
    """name(lower) -> (role, department code)."""
    out: dict[str, tuple[str, str]] = {}
    for code, spec in WORKFORCE.items():
        head_name = spec["head"][0]
        out[head_name.strip().lower()] = (UserRole.DEPT_HEAD.value, code)
        for name, title, _skills in spec["people"]:
            role = (
                UserRole.MANAGER.value
                if "Manager" in title or "Lead" in title or "Supervisor" in title
                else UserRole.EMPLOYEE.value
            )
            out[name.strip().lower()] = (role, code)
    return out


async def main(apply: bool) -> None:
    roster = _roster_roles()

    async with AsyncSessionFactory() as db:
        admin = (
            await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        ).scalar_one()
        org_id = admin.org_id

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
        users = (
            await db.execute(
                select(User).where(User.org_id == org_id, User.is_active.is_(True))
            )
        ).scalars().all()

        role_fixes, deactivate = [], []
        for u in users:
            if u.id == admin.id:
                continue
            entry = roster.get((u.full_name or "").strip().lower())
            if entry is None:
                deactivate.append(u)
                continue
            want_role, want_code = entry
            want_dept = depts.get(want_code)
            if u.role != want_role or (want_dept and u.dept_id != want_dept.id):
                role_fixes.append((u, want_role, want_code, want_dept))

        print(f"  role/department corrections : {len(role_fixes)}")
        for u, want_role, code, _ in role_fixes:
            print(f"     {u.full_name:20s} {u.role:11s} -> {want_role:11s} ({code})")
        print(f"  not on any roster, deactivate: {len(deactivate)}")
        for u in deactivate:
            print(f"     {u.full_name:20s} {u.role:11s} {u.email}")

        if apply:
            for u, want_role, _code, want_dept in role_fixes:
                u.role = want_role
                if want_dept:
                    u.dept_id = want_dept.id
            for u in deactivate:
                u.is_active = False
            await db.commit()

        # Report the resulting shape.
        users = (
            await db.execute(
                select(User).where(User.org_id == org_id, User.is_active.is_(True))
            )
        ).scalars().all()
        print(f"\n  active users now: {len(users)}  (target 61)")
        print("  DEPARTMENT  MEMBERS  HEAD  MANAGERS  EMPLOYEES")
        for code, d in sorted(depts.items()):
            mem = [u for u in users if u.dept_id == d.id]
            h = sum(1 for u in mem if u.role == UserRole.DEPT_HEAD.value)
            m = sum(1 for u in mem if u.role == UserRole.MANAGER.value)
            e = sum(1 for u in mem if u.role == UserRole.EMPLOYEE.value)
            flag = "" if (len(mem) == 10 and h == 1) else "   <-- off target"
            print(f"  {code:10s} {len(mem):7d}  {h:4d}  {m:8d}  {e:9d}{flag}")
        outside = [u for u in users if not u.dept_id]
        print(f"  outside departments: {len(outside)} "
              f"({', '.join(u.full_name for u in outside)})")


if __name__ == "__main__":
    asyncio.run(main(apply="--apply" in sys.argv))
