"""
AION Demo Data Seeder
Populates a realistic small organization ("Nova Robotics") across SQLite
(Organization/Department/User/KnowledgeItem/EmployeeKnowledgeProfile) and the
embedded graph store (Person/Knowledge/Project nodes + relationships), so the
frontend has real, compelling data to render on first run.

Run once from backend/: python scripts/seed_demo_data.py
Idempotent: skips creation if the demo org already exists.
"""
from __future__ import annotations

import asyncio
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.database import AsyncSessionFactory, init_db
from app.core.security import UserRole, hash_password
from app.models.employee_profile import EmployeeKnowledgeProfile
from app.models.knowledge import KnowledgeItem
from app.models.organization import Department, Organization
from app.models.user import User
from app.repositories.graph_repository import GraphRepository

ADMIN_EMAIL = "demo@aion.ai"
ADMIN_PASSWORD = "DemoPass123!"
ORG_NAME = "Nova Robotics"

DEPARTMENTS = ["Engineering", "Product", "Sales", "Operations", "Security"]

EMPLOYEES = [
    ("Alice Chen", "Engineering", "Staff Engineer", ["backend", "distributed-systems", "kubernetes"]),
    ("Marcus Webb", "Engineering", "Senior Engineer", ["frontend", "react", "design-systems"]),
    ("Priya Nair", "Engineering", "Engineering Manager", ["architecture", "leadership", "backend"]),
    ("Sofia Reyes", "Product", "VP Product", ["product-strategy", "roadmapping"]),
    ("Daniel Kim", "Product", "Product Manager", ["analytics", "user-research"]),
    ("Grace Osei", "Sales", "Head of Sales", ["enterprise-sales", "negotiation"]),
    ("Tom Fitzgerald", "Sales", "Account Executive", ["saas-sales", "crm"]),
    ("Elena Petrova", "Operations", "Ops Director", ["logistics", "vendor-management"]),
    ("Wei Zhang", "Security", "CISO", ["security", "compliance", "risk-management"]),
    ("Jordan Lee", "Security", "Security Engineer", ["penetration-testing", "incident-response"]),
    ("Nina Kowalski", "Engineering", "ML Engineer", ["machine-learning", "robotics", "computer-vision"]),
    ("Omar Haddad", "Operations", "Supply Chain Lead", ["procurement", "manufacturing"]),
]

KNOWLEDGE_ITEMS = [
    ("Payment Reconciliation SOP", "finance", "How we reconcile daily payments across gateways", 0.92, False, False),
    ("Kubernetes Cluster Runbook", "engineering", "Incident response runbook for prod k8s clusters", 0.88, False, False),
    ("Robotic Arm Calibration Guide", "engineering", "Step-by-step calibration for the R3 arm assembly", 0.75, False, False),
    ("Q3 Product Roadmap", "product", "Prioritized roadmap for Q3 feature delivery", 0.95, False, False),
    ("Enterprise Sales Playbook", "sales", "Objection handling and pricing tiers for enterprise deals", 0.60, True, False),
    ("Vendor Onboarding Checklist", "operations", "Steps to onboard a new hardware vendor", 0.55, True, False),
    ("SOC2 Compliance Evidence Log", "security", "Ongoing evidence collection for SOC2 Type II audit", 0.90, False, False),
    ("Incident Response Playbook", "security", "Severity classification and escalation paths", 0.85, False, False),
    ("Computer Vision Model Training Notes", "engineering", "Hyperparameters and dataset lineage for CV model v4", 0.70, False, False),
    ("Legacy Billing Migration Notes", "finance", "Notes from the 2025 billing system migration", 0.25, True, True),
    ("Customer Churn Analysis Q2", "product", "Root cause analysis of Q2 churn spike", 0.65, False, False),
    ("Manufacturing Line Safety Protocol", "operations", "Safety checklist for the assembly line", 0.80, False, False),
    ("API Rate Limiting Design Doc", "engineering", "Design for the new tiered rate limiter", 0.78, False, False),
    ("Duplicate: Payment Reconciliation Notes", "finance", "Earlier draft of the payment reconciliation process", 0.30, True, True),
    ("Partner Integration Agreement Template", "sales", "Standard legal template for partner integrations", 0.50, True, False),
    ("Firmware OTA Update Procedure", "engineering", "Over-the-air update rollout process for robot firmware", 0.82, False, False),
    ("Employee Onboarding Guide", "operations", "New hire onboarding checklist and resources", 0.68, False, False),
    ("Pen Test Findings 2026-Q1", "security", "External penetration test findings and remediations", 0.72, False, False),
]

PROJECTS = [
    ("R3 Robotic Arm Launch", "active", "critical"),
    ("SOC2 Type II Audit", "active", "high"),
    ("Billing Platform Migration", "at_risk", "high"),
    ("Enterprise Expansion EMEA", "active", "medium"),
]


def now() -> datetime:
    return datetime.now(timezone.utc)


async def main() -> None:
    await init_db()
    graph_repo = GraphRepository()

    async with AsyncSessionFactory() as db:
        existing = (await db.execute(select(Organization).where(Organization.name == ORG_NAME))).scalar_one_or_none()
        if existing:
            print(f"'{ORG_NAME}' already exists (org_id={existing.id}) — skipping seed. "
                  f"Delete backend/data/aion.db and backend/data/graph_store.json to reseed.")
            return

        org = Organization(name=ORG_NAME, slug="nova-robotics", industry="robotics", size=len(EMPLOYEES))
        db.add(org)
        await db.flush()

        dept_rows = {}
        for dept_name in DEPARTMENTS:
            dept = Department(org_id=org.id, name=dept_name, code=dept_name[:3].upper())
            db.add(dept)
            dept_rows[dept_name] = dept
        await db.flush()

        await graph_repo.create_department_node(str(org.id) + "-root", str(org.id), ORG_NAME)
        for dept_name, dept in dept_rows.items():
            await graph_repo.create_department_node(str(dept.id), str(org.id), dept_name)

        # Admin (login-capable) user
        admin = User(
            org_id=org.id, email=ADMIN_EMAIL, username="demo_admin", full_name="Demo Admin",
            hashed_password=hash_password(ADMIN_PASSWORD), role=UserRole.ORG_ADMIN.value,
            job_title="Founder & CEO", dept_id=dept_rows["Engineering"].id, is_verified=True,
        )
        db.add(admin)
        await db.flush()
        await graph_repo.create_person_node(
            str(admin.id), str(org.id), admin.full_name, admin.email,
            department="Engineering", role="Founder & CEO", expertise=["leadership", "strategy"],
        )

        user_rows = [admin]
        for name, dept_name, title, expertise in EMPLOYEES:
            email = name.lower().replace(" ", ".") + "@novarobotics.ai"
            user = User(
                org_id=org.id, email=email, username=email.split("@")[0],
                full_name=name, hashed_password=hash_password("DemoPass123!"),
                role=UserRole.ANALYST.value, job_title=title, dept_id=dept_rows[dept_name].id,
                is_verified=True,
            )
            db.add(user)
            await db.flush()
            user_rows.append(user)
            await graph_repo.create_person_node(
                str(user.id), str(org.id), name, email,
                department=dept_name, role=title, expertise=expertise,
            )

        # Knowledge items — Postgres/SQLite rows (health/decay stats) + matching graph nodes
        knowledge_ids = []
        for title, domain, summary, relevance, is_outdated, is_duplicate in KNOWLEDGE_ITEMS:
            creator = random.choice(user_rows[1:])
            days_ago = random.randint(1, 150)
            item = KnowledgeItem(
                org_id=org.id, dept_id=creator.dept_id, creator_id=creator.id,
                title=title, summary=summary, domain=domain, source_type="document",
                relevance_score=relevance, is_outdated=is_outdated, is_duplicate=is_duplicate,
                last_accessed_at=now() - timedelta(days=days_ago),
                access_count=random.randint(1, 80),
            )
            db.add(item)
            await db.flush()
            knowledge_ids.append((item.id, title, domain, summary, creator))
            await graph_repo.create_knowledge_node(
                str(item.id), str(org.id), title, domain, "document", summary=summary,
            )

        # Projects
        project_ids = []
        for name, status, priority in PROJECTS:
            pid = str(uuid.uuid4())
            await graph_repo.create_project_node(pid, str(org.id), name, status, priority, owner_id=str(random.choice(user_rows).id))
            project_ids.append(pid)

        # Relationships: KNOWS (weighted so some knowledge has a single critical owner)
        for idx, (kid, title, domain, summary, creator) in enumerate(knowledge_ids):
            owners = [creator]
            # Most items get a second owner; every 4th stays single-owner-critical
            if idx % 4 != 0:
                candidates = [u for u in user_rows if u.id != creator.id]
                owners.append(random.choice(candidates))
            for owner in owners:
                await graph_repo.create_knows_relationship(
                    str(owner.id), str(kid), strength=round(random.uniform(0.5, 0.95), 2), role="owner",
                )

        # CONTRIBUTES_TO
        for user in user_rows:
            for pid in random.sample(project_ids, k=random.randint(1, 2)):
                await graph_repo.create_contributes_to_relationship(
                    str(user.id), pid, role="contributor", contribution_score=round(random.uniform(0.4, 0.9), 2),
                )

        # COLLABORATES_WITH — dense within department, sparse across
        for i, a in enumerate(user_rows):
            for b in user_rows[i + 1:]:
                same_dept = a.dept_id == b.dept_id
                if same_dept and random.random() < 0.7:
                    await graph_repo.create_collaborates_with_relationship(
                        str(a.id), str(b.id), frequency=random.randint(5, 40), channel="slack",
                    )
                elif not same_dept and random.random() < 0.15:
                    await graph_repo.create_collaborates_with_relationship(
                        str(a.id), str(b.id), frequency=random.randint(1, 8), channel="email",
                    )

        # DEPENDS_ON — chain a few knowledge items
        for i in range(0, len(knowledge_ids) - 1, 5):
            await graph_repo.create_depends_on_relationship(
                str(knowledge_ids[i][0]), str(knowledge_ids[i + 1][0]), criticality="high",
            )

        # Employee Knowledge DNA profiles for a few key people (drives OCSIE + healing)
        profile_specs = [
            (user_rows[1], 0.91, 0.88, 0.85, "analytical", "direct", "collaborative"),   # Alice Chen — high risk
            (user_rows[9], 0.86, 0.80, 0.78, "fast", "formal", "analytical"),             # Wei Zhang — CISO
            (user_rows[3], 0.70, 0.55, 0.60, "collaborative", "informal", "intuitive"),   # Sofia Reyes
        ]
        for user, crit, repl, risk, decision_style, comm_style, work_style in profile_specs:
            profile = EmployeeKnowledgeProfile(
                user_id=user.id, org_id=org.id,
                knowledge_criticality_score=crit, replacement_difficulty_score=repl, knowledge_risk_score=risk,
                decision_style=decision_style, communication_style=comm_style, work_style=work_style,
                primary_domains=list({d for _, dept, _, exp in EMPLOYEES if dept == "Engineering" for d in exp})[:4],
                technical_expertise={"depth": "expert", "years": random.randint(4, 12)},
                critical_responsibilities=["On-call escalation lead", "Sole owner of legacy billing migration"],
                last_computed_at=now(),
            )
            db.add(profile)

        await db.commit()

        print(f"Seeded '{ORG_NAME}':")
        print(f"  org_id: {org.id}")
        print(f"  admin login: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print(f"  users: {len(user_rows)}  knowledge_items: {len(knowledge_ids)}  projects: {len(project_ids)}")


if __name__ == "__main__":
    asyncio.run(main())
