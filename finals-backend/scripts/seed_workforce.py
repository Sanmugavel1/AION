"""
Seed the full NovaTech workforce: 61 accounts in one pattern.

    6 departments x 10 members (1 head + 9)  = 60
    1 global administrator                   =  1
                                               --
                                               61

Every person gets a real record — employee code, designation, joining date, reporting
head, skills, and named projects — because a dashboard that reads "no data" proves
nothing. Idempotent: re-running tops each department up to 10 rather than duplicating.

    python scripts/seed_workforce.py            # report what would change
    python scripts/seed_workforce.py --apply    # write it
"""
from __future__ import annotations

import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionFactory
from app.core.security import UserRole, hash_password
from app.models.organization import Department, Organization
from app.models.user import User
from app.models.workplace import EmployeeProfileDetail

#: One password for every seeded account, so a demo can be driven without a lookup.
#: Hashed on write; never stored in plain text.
SHARED_PASSWORD = "DemoPass123!"
DOMAIN = "novatech.example"

# Nine people per department, plus the head listed first. Designations and projects are
# specific to the department so the data reads as a real company rather than filler.
WORKFORCE: dict[str, dict] = {
    "RND": {
        "head": ("Alice Chen", "Head of Research & Development"),
        "people": [
            ("Wei Zhang", "Senior Perception Engineer", ["computer-vision", "sensor-fusion"]),
            ("Marcus Webb", "Engineering Manager", ["team-lead", "release-management"]),
            ("Ana Ferreira", "Robotics Engineer", ["motion-planning", "ros"]),
            ("Tomas Vidal", "Machine Learning Engineer", ["model-training", "evaluation"]),
            ("Leila Haddad", "Simulation Engineer", ["digital-twin", "physics-sim"]),
            ("Sung-min Park", "Firmware Engineer", ["embedded-c", "real-time"]),
            ("Grace Whitfield", "Research Scientist", ["slam", "state-estimation"]),
            ("Ibrahim Sesay", "Test Engineer", ["hil-testing", "regression"]),
            ("Nora Lindqvist", "Associate Engineer", ["data-labelling", "tooling"]),
        ],
        "projects": ["Perception Stack v4", "Adverse-Weather Benchmark", "Shadow Deploy Harness"],
    },
    "MFG": {
        "head": ("Omar Haddad", "Head of Manufacturing"),
        "people": [
            ("Rosa Delgado", "Production Supervisor", ["line-balancing", "shift-planning"]),
            ("Kenji Sato", "Process Engineer", ["changeover", "yield-analysis"]),
            ("Bridget Kelly", "Quality Engineer", ["first-article", "spc"]),
            ("Pavel Novak", "Maintenance Lead", ["preventive-maintenance", "tooling"]),
            ("Amara Nwosu", "Assembly Technician", ["sensor-modules", "torque-spec"]),
            ("Liam Doherty", "Assembly Technician", ["harnessing", "inspection"]),
            ("Sofia Marchetti", "Supply Coordinator", ["kitting", "inventory"]),
            ("Hector Rivas", "Calibration Technician", ["metrology", "fixtures"]),
            ("Yuki Tanaka", "Industrial Engineer", ["layout", "takt-time"]),
        ],
        "projects": ["Line 3 Changeover Reduction", "Cold-Chain Handling", "Fixture Standardisation"],
    },
    "FIN": {
        "head": ("Grace Osei", "Head of Finance"),
        "people": [
            ("Jordan Lee", "Finance Manager", ["forecasting", "business-partnering"]),
            ("Priya Raman", "Financial Analyst", ["variance-analysis", "modelling"]),
            ("Daniel Fischer", "Revenue Accountant", ["revenue-recognition", "contracts"]),
            ("Mei Lin", "Accounts Payable Lead", ["vendor-payments", "controls"]),
            ("Samuel Adeyemi", "Payroll Specialist", ["payroll", "compliance"]),
            ("Elif Demir", "Treasury Analyst", ["cash-flow", "fx"]),
            ("Carlos Mendes", "Cost Accountant", ["standard-costing", "inventory"]),
            ("Hannah Brooks", "Procurement Analyst", ["sourcing", "supplier-terms"]),
            ("Ravi Iyer", "Finance Associate", ["reconciliation", "reporting"]),
        ],
        "projects": ["Quarter Close Automation", "Vendor Payment Controls", "Margin Review"],
    },
    "SLS": {
        "head": ("Sofia Reyes", "Head of Sales & Marketing"),
        "people": [
            ("Elena Petrova", "Regional Sales Manager", ["enterprise-deals", "forecasting"]),
            ("Tom Bradley", "Account Executive", ["prospecting", "negotiation"]),
            ("Aisha Bello", "Account Executive", ["renewals", "expansion"]),
            ("Nikolai Petrov", "Solutions Consultant", ["demos", "technical-fit"]),
            ("Clara Jensen", "Marketing Manager", ["campaigns", "positioning"]),
            ("Diego Santos", "Product Marketing", ["messaging", "competitive"]),
            ("Fatima Zahra", "Sales Operations", ["pipeline-hygiene", "reporting"]),
            ("Owen Murphy", "Partnerships Lead", ["channel", "alliances"]),
            ("Ines Costa", "Sales Associate", ["qualification", "crm"]),
        ],
        "projects": ["Enterprise Deal Desk", "Competitive Playbook", "Renewal Motion"],
    },
    "HR": {
        "head": ("Priya Nair", "Head of Human Resources"),
        "people": [
            ("Nina Kowalski", "HR Manager", ["employee-relations", "policy"]),
            ("Marcus Obi", "Talent Acquisition Lead", ["hiring", "assessment"]),
            ("Sara Lindgren", "HR Business Partner", ["performance", "coaching"]),
            ("Ahmed Farouk", "Learning & Development", ["training", "onboarding"]),
            ("Julia Moreau", "Compensation Analyst", ["banding", "benchmarking"]),
            ("Kofi Mensah", "HR Operations", ["records", "leave-administration"]),
            ("Rebecca Stone", "Recruiter", ["sourcing", "interviews"]),
            ("Ali Reza", "HR Associate", ["documentation", "compliance"]),
            ("Maya Sharma", "People Analytics", ["attrition", "engagement"]),
        ],
        "projects": ["First 90 Days Standard", "Grievance Escalation", "Shift Handover Protocol"],
    },
    "IT": {
        "head": ("Daniel Kim", "Head of Information Technology"),
        "people": [
            ("Bilal Ahmed", "Platform Engineer", ["kubernetes", "ci-cd"]),
            ("Laura Bianchi", "Security Engineer", ["threat-modelling", "iam"]),
            ("Peter Osei", "Site Reliability Engineer", ["observability", "on-call"]),
            ("Anya Volkova", "Network Engineer", ["routing", "segmentation"]),
            ("Chris Nolan", "Systems Administrator", ["identity", "endpoints"]),
            ("Divya Menon", "Database Administrator", ["postgres", "backup-restore"]),
            ("Marco Rossi", "Support Lead", ["incident-triage", "service-desk"]),
            ("Zainab Yusuf", "Cloud Engineer", ["iac", "cost-control"]),
            ("Erik Johansson", "IT Associate", ["provisioning", "asset-management"]),
        ],
        "projects": ["Incident Severity Standard", "Zero-Trust Rollout", "Backup Verification"],
    },
}


def _email(name: str) -> str:
    first, _, last = name.partition(" ")
    return f"{first}.{last}".lower().replace(" ", "").replace("-", "") + f"@{DOMAIN}"


def _username(name: str) -> str:
    first, _, last = name.partition(" ")
    return f"{first}.{last}".lower().replace(" ", "").replace("-", "")


async def main(apply: bool) -> None:
    async with AsyncSessionFactory() as db:
        anchor = (
            await db.execute(select(User).where(User.email == "demo@aion.ai"))
        ).scalar_one()
        org_id = anchor.org_id

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
        all_users = (
            await db.execute(select(User).where(User.org_id == org_id))
        ).scalars().all()
        # Match on name, not email: twelve of these people already exist on the
        # novarobotics.ai domain from the earlier seed. Keying on email would mint a
        # second Alice Chen rather than finding the first, and their existing logins
        # (used throughout testing) must keep working.
        by_name = {u.full_name.strip().lower(): u for u in all_users}
        by_email = {u.email: u for u in all_users}

        # Employee codes continue from whatever is already issued.
        used_codes = {
            p.employee_code
            for p in (
                await db.execute(select(EmployeeProfileDetail))
            ).scalars().all()
        }
        next_code = 1001
        while f"EMP{next_code}" in used_codes:
            next_code += 1

        created, profiled, skipped = 0, 0, 0
        pwd = hash_password(SHARED_PASSWORD)
        joined_base = date(2023, 1, 9)

        for code, spec in WORKFORCE.items():
            dept = depts.get(code)
            if dept is None:
                print(f"  ! no department with code {code}; skipping")
                continue

            roster = [(spec["head"][0], spec["head"][1], UserRole.DEPT_HEAD.value, [])]
            for i, (name, title, skills) in enumerate(spec["people"]):
                role = (
                    UserRole.MANAGER.value
                    if "Manager" in title or "Lead" in title or "Supervisor" in title
                    else UserRole.EMPLOYEE.value
                )
                roster.append((name, title, role, skills))

            head_user = None
            for idx, (name, title, role, skills) in enumerate(roster):
                email = _email(name)
                user = by_name.get(name.strip().lower()) or by_email.get(email)
                if user is None:
                    user = User(
                        org_id=org_id,
                        dept_id=dept.id,
                        email=email,
                        username=_username(name),
                        full_name=name,
                        hashed_password=pwd,
                        role=role,
                        job_title=title,
                        is_active=True,
                        is_verified=True,
                    )
                    if apply:
                        db.add(user)
                        await db.flush()
                    created += 1
                else:
                    skipped += 1
                    # Keep an existing person where they are, but make sure the
                    # department and title match this roster.
                    if apply:
                        user.dept_id = dept.id
                        user.job_title = user.job_title or title

                if idx == 0:
                    head_user = user

                if apply and user.id:
                    has = (
                        await db.execute(
                            select(EmployeeProfileDetail).where(
                                EmployeeProfileDetail.user_id == user.id
                            )
                        )
                    ).scalar_one_or_none()
                    if has is None:
                        db.add(
                            EmployeeProfileDetail(
                                org_id=org_id,
                                user_id=user.id,
                                employee_code=f"EMP{next_code}",
                                designation=title,
                                joining_date=joined_base + timedelta(days=37 * (next_code - 1001)),
                                reporting_head_id=(
                                    head_user.id if head_user and user.id != head_user.id else None
                                ),
                                skills={"primary": skills} if skills else {"primary": []},
                                current_projects={"names": spec["projects"][:2]},
                                completed_projects={"names": spec["projects"][2:]},
                                is_trainee="Associate" in title,
                            )
                        )
                        next_code += 1
                        profiled += 1

        if apply:
            await db.commit()

        total = (
            await db.execute(
                select(User).where(User.org_id == org_id, User.is_active.is_(True))
            )
        ).scalars().all()
        print(f"\n  created  : {created}")
        print(f"  profiled : {profiled}")
        print(f"  existing : {skipped}")
        print(f"  active users in org now: {len(total)}  (target 61)")


if __name__ == "__main__":
    asyncio.run(main(apply="--apply" in sys.argv))
