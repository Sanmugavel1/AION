"""
Sync every active user into the Organizational Memory Graph.

`seed_demo_data.py` only creates graph `Person` nodes (and matching `KNOWS`
knowledge ownership) for the original ~13-person starter org. `seed_enterprise`,
`seed_workforce`, and `seed_workplace_data` add the remaining people needed to
reach 61 (6 departments x 10 + 1 admin) purely in SQL — they never touch the
graph. Net effect: roughly 48 of 61 people were invisible to every graph-backed
feature (the memory graph, bottleneck detection, department knowledge counts,
and the "what if this person leaves" simulator), which made those people
unselectable, and the ones who *were* selectable but never owned any knowledge
(e.g. the admin, or anyone who only ever co-owned an item) produced an
all-zero simulation result.

This script closes all four gaps:
  0. Creates a `Department` graph node for each of the real 6 departments and
     removes the 5 long-dead starter-org ones (Engineering/Product/Sales/
     Operations/Security) — /graph/departments, and the dashboard's
     "Departments" panel that reads it, was showing that stale 5-department
     list with near-zero headcounts instead of the real org.
  1. Creates (or refreshes) a `Person` graph node for every active user, so
     department and role always match the current org chart — fixes stale
     nodes too (e.g. someone reassigned by seed_enterprise whose graph node
     still says their old department).
  2. Tops every person up to a real, sole-owned Knowledge item count for
     their role tier, derived from their actual skills
     (`employee_profile_details.skills`) or job title — so a departure
     simulation for *any* of the 61 people returns a real, non-zero result,
     scaled consistently by seniority (heads/executives lose more than an
     associate), not by how the original random demo seed happened to land.
  3. Removes graph `Person` nodes left behind for anyone reconcile_workforce
     has since deactivated (e.g. "Tom Fitzgerald", a starter-org employee who
     never made it onto the final department roster) — otherwise they persist
     as a selectable ghost with a guaranteed-zero simulation result.

Idempotent: re-running only fills gaps, never duplicates. Runs automatically
on every backend startup (see app/main.py lifespan), same as the other
seed/reconcile steps.

    python scripts/sync_graph_people.py            # report
    python scripts/sync_graph_people.py --apply    # write
"""
from __future__ import annotations

import asyncio
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionFactory
from app.core.graph_store import graph_store
from app.core.security import UserRole
from app.models.knowledge import KnowledgeItem
from app.models.organization import Department, Organization
from app.models.user import User
from app.models.workplace import EmployeeProfileDetail
from app.repositories.graph_repository import GraphRepository

ANCHOR_EMAIL = "demo@aion.ai"

# Department code -> primary knowledge domain (mirrors seed_enterprise.DEPARTMENTS,
# duplicated here rather than imported so this script has no dependency on the
# enterprise seeder's internal layout).
DEPT_DOMAIN = {
    "HR": "hr", "RND": "engineering", "FIN": "finance",
    "MFG": "operations", "SLS": "sales", "IT": "security",
}

# How many sole-owned knowledge items a departure simulation should find per
# role tier — a head walking out the door should look meaningfully worse than
# an associate, the same way it would at a real company.
ITEMS_BY_ROLE = {
    UserRole.ORG_ADMIN.value: 3,
    UserRole.EXECUTIVE.value: 3,
    UserRole.DEPT_HEAD.value: 3,
    UserRole.MANAGER.value: 2,
}
DEFAULT_ITEMS = 1


def _title_case_skill(skill: str) -> str:
    return skill.replace("-", " ").replace("_", " ").title()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sole_owned_knowledge_count(person_id: str) -> int:
    """How many items would actually orphan if this person left.

    Merely having a KNOWS edge isn't enough — `simulate_person_departure`
    (graph_repository.py) only counts an item as orphaned if no *other*
    person also knows it. Someone who only ever co-owns shared items (e.g.
    picked as the random second owner in the original demo seed) has KNOWS
    edges but a guaranteed-zero simulation result, which is the exact bug
    this script exists to close.
    """
    count = 0
    for knowledge_id, _, _ in graph_store.out_edges(person_id, "KNOWS"):
        other_owners = [pid for pid, _, _ in graph_store.in_edges(knowledge_id, "KNOWS") if pid != person_id]
        if not other_owners:
            count += 1
    return count


async def main(apply: bool) -> None:
    graph_repo = GraphRepository()

    async with AsyncSessionFactory() as db:
        anchor = (await db.execute(select(User).where(User.email == ANCHOR_EMAIL))).scalar_one()
        org = (await db.execute(select(Organization).where(Organization.id == anchor.org_id))).scalar_one()

        depts = {d.id: d for d in (
            await db.execute(select(Department).where(Department.org_id == org.id))
        ).scalars().all()}

        # seed_demo_data() creates graph Department nodes for its own 5-department
        # starter layout (Engineering/Product/Sales/Operations/Security) and never
        # touches the graph again; seed_enterprise() only deactivates the matching
        # SQL rows. The real 6-department org (HR/RND/FIN/MFG/SLS/IT) never got
        # graph nodes at all, so /graph/departments — and the dashboard's
        # "Departments" panel, which reads it directly — showed the wrong,
        # long-dead department list. Replace: create a node per active department,
        # drop every Department node that isn't one of them.
        dept_nodes_created, dept_nodes_removed = 0, 0
        active_dept_ids = {str(d.id) for d in depts.values() if d.is_active}
        for d in depts.values():
            if not d.is_active:
                continue
            node = graph_store.get_node(str(d.id))
            if node is None or node.get("name") != d.name:
                dept_nodes_created += 1
                if apply:
                    await graph_repo.create_department_node(str(d.id), str(org.id), d.name)
        for node in graph_store.nodes_by_label("Department", org_id=str(org.id)):
            if node["id"] not in active_dept_ids:
                dept_nodes_removed += 1
                if apply:
                    graph_store.remove_node(node["id"])

        users = (await db.execute(
            select(User).where(User.org_id == org.id, User.is_active.is_(True))
        )).scalars().all()

        # seed_demo_data() unconditionally creates a Person node for every one of
        # its starter-org employees; reconcile_workforce() later deactivates
        # whoever isn't on the final department roster (e.g. "Tom Fitzgerald",
        # who never made it onto the Sales & Marketing roster). Nothing has ever
        # removed *their* graph node, so they persist as a selectable "ghost" in
        # every graph-backed feature (including this simulator) with a guaranteed
        # zero result — happens on every fresh boot, not just stale local data.
        inactive_users = (await db.execute(
            select(User).where(User.org_id == org.id, User.is_active.is_(False))
        )).scalars().all()
        ghost_nodes_removed = 0
        for u in inactive_users:
            if apply and graph_store.get_node(str(u.id)) is not None:
                await graph_repo.delete_person_node(str(u.id))
                ghost_nodes_removed += 1
            elif not apply and graph_store.get_node(str(u.id)) is not None:
                ghost_nodes_removed += 1

        profiles = {
            p.user_id: p for p in (
                await db.execute(select(EmployeeProfileDetail).where(EmployeeProfileDetail.org_id == org.id))
            ).scalars().all()
        }

        nodes_created, nodes_refreshed = 0, 0
        items_created, people_covered = 0, 0

        for user in users:
            dept = depts.get(user.dept_id) if user.dept_id else None
            dept_name = dept.name if dept else None
            profile = profiles.get(user.id)
            skills = list((profile.skills or {}).get("primary", [])) if profile else []
            expertise = skills or (["leadership", "strategy"] if not dept else [])

            existing_node = graph_store.get_node(str(user.id))
            needs_refresh = existing_node is not None and (
                existing_node.get("department") != dept_name
                or existing_node.get("role") != user.job_title
            )
            if existing_node is None:
                nodes_created += 1
            elif needs_refresh:
                nodes_refreshed += 1

            if apply and (existing_node is None or needs_refresh):
                await graph_repo.create_person_node(
                    str(user.id), str(org.id), user.full_name, user.email,
                    department=dept_name, role=user.job_title, expertise=expertise,
                )

            # --- knowledge coverage -----------------------------------------
            # Top up to the role's target rather than a plain "has any" check —
            # see _sole_owned_knowledge_count for why a raw edge count isn't
            # enough. Without topping up, a head who happened to get one item
            # from the original random seed would show less departure impact
            # than a head who got none and was fully backfilled — an
            # inconsistency driven by seed luck, not seniority.
            target = ITEMS_BY_ROLE.get(user.role, DEFAULT_ITEMS)
            existing = _sole_owned_knowledge_count(str(user.id))
            item_count = target - existing
            if item_count <= 0:
                continue
            people_covered += 1

            domain = DEPT_DOMAIN.get(dept.code, "strategy") if dept else "strategy"
            topics = skills[:item_count] or [user.job_title or "role"] * item_count

            for i in range(item_count):
                topic = topics[i % len(topics)] if topics else (user.job_title or "General")
                label = _title_case_skill(topic)
                title = f"{label} — {user.job_title}" if user.job_title else label
                summary = (
                    f"Working knowledge built up by {user.full_name} "
                    f"({user.job_title or 'team member'}{', ' + dept_name if dept_name else ''}) "
                    f"covering {label.lower()}."
                )
                items_created += 1
                if not apply:
                    continue

                item = KnowledgeItem(
                    org_id=org.id, dept_id=user.dept_id, creator_id=user.id,
                    title=title, summary=summary, domain=domain, source_type="tacit_expertise",
                    relevance_score=round(random.uniform(0.65, 0.95), 2),
                    last_accessed_at=_now() - timedelta(days=random.randint(1, 90)),
                    access_count=random.randint(1, 40),
                )
                db.add(item)
                await db.flush()

                await graph_repo.create_knowledge_node(
                    str(item.id), str(org.id), title, domain, "tacit_expertise",
                    summary=summary, department=dept_name,
                )
                await graph_repo.create_knows_relationship(
                    str(user.id), str(item.id),
                    strength=round(random.uniform(0.75, 0.97), 2), role="owner",
                )

        if apply:
            await db.commit()

        print(f"  department nodes fixed : {dept_nodes_created} created, {dept_nodes_removed} stale removed")
        print(f"  person nodes created   : {nodes_created}")
        print(f"  person nodes refreshed : {nodes_refreshed}")
        print(f"  ghost nodes removed    : {ghost_nodes_removed}")
        print(f"  people newly covered   : {people_covered}")
        print(f"  knowledge items added  : {items_created}")
        print(f"  active users total     : {len(users)}")
        if not apply:
            print("  (dry run — pass --apply to write)")


if __name__ == "__main__":
    asyncio.run(main(apply="--apply" in sys.argv))
