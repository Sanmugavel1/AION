"""
AION Graph Repository
All Organizational Memory Graph operations, backed by the embedded GraphStore
(NetworkX) instead of Neo4j. Method signatures and return shapes are preserved
so callers (API endpoints, LangGraph agents) are unaffected by the swap.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.graph_store import graph_store, now_iso
from app.core.logging import get_logger

logger = get_logger(__name__)


class GraphRepository:
    """Repository for all graph operations (Person/Knowledge/Project/Department)."""

    # ─── Node Operations ──────────────────────────────────────────────────────

    async def create_person_node(
        self,
        user_id: str,
        org_id: str,
        name: str,
        email: str,
        department: Optional[str] = None,
        role: Optional[str] = None,
        expertise: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return graph_store.upsert_node(
            user_id, "Person",
            org_id=org_id, name=name, email=email, department=department,
            role=role, expertise=expertise or [],
            created_at=now_iso(), updated_at=now_iso(),
        )

    async def create_knowledge_node(
        self,
        knowledge_id: str,
        org_id: str,
        title: str,
        domain: str,
        source_type: str,
        summary: Optional[str] = None,
        tags: Optional[List[str]] = None,
        department: Optional[str] = None,
    ) -> Dict[str, Any]:
        existing = graph_store.get_node(knowledge_id)
        access_count = existing.get("access_count", 0) if existing else 0
        return graph_store.upsert_node(
            knowledge_id, "Knowledge",
            org_id=org_id, title=title, domain=domain, source_type=source_type,
            summary=summary, tags=tags or [], access_count=access_count, department=department,
            relevance_score=1.0, created_at=now_iso(), last_accessed_at=now_iso(),
        )

    async def create_project_node(
        self,
        project_id: str,
        org_id: str,
        name: str,
        status: str,
        priority: str,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return graph_store.upsert_node(
            project_id, "Project",
            org_id=org_id, name=name, status=status, priority=priority,
            owner_id=owner_id, created_at=now_iso(), updated_at=now_iso(),
        )

    async def create_department_node(self, dept_id: str, org_id: str, name: str) -> Dict[str, Any]:
        return graph_store.upsert_node(dept_id, "Department", org_id=org_id, name=name, created_at=now_iso())

    async def list_departments(self, org_id: str) -> List[Dict[str, Any]]:
        departments = graph_store.nodes_by_label("Department", org_id=org_id)
        people = graph_store.nodes_by_label("Person", org_id=org_id)
        knowledge = graph_store.nodes_by_label("Knowledge", org_id=org_id)

        result = []
        for dept in departments:
            dept_people = [p for p in people if p.get("department") == dept.get("name")]
            person_ids = {p["id"] for p in dept_people}
            dept_knowledge = sum(
                1 for k in knowledge
                if any(owner_id in person_ids for owner_id, _, _ in graph_store.in_edges(k["id"], "KNOWS"))
            )
            dept_policies = sum(
                1 for k in knowledge
                if k.get("domain") == "policy" and k.get("department") == dept.get("name")
            )
            result.append({
                "id": dept["id"],
                "name": dept.get("name"),
                "headcount": len(dept_people),
                "knowledge_items": dept_knowledge,
                "policy_count": dept_policies,
                "created_at": dept.get("created_at"),
            })
        result.sort(key=lambda d: d["name"] or "")
        return result

    async def list_policies(self, org_id: str, department: Optional[str] = None) -> List[Dict[str, Any]]:
        knowledge = graph_store.nodes_by_label("Knowledge", org_id=org_id)
        policies = [k for k in knowledge if k.get("domain") == "policy"]
        if department:
            policies = [p for p in policies if p.get("department") == department]
        policies.sort(key=lambda p: p.get("created_at") or "", reverse=True)
        return policies

    # ─── Relationship Operations ───────────────────────────────────────────────

    async def create_knows_relationship(
        self,
        person_id: str,
        knowledge_id: str,
        strength: float = 0.5,
        role: str = "contributor",
    ) -> bool:
        result = graph_store.upsert_edge(
            person_id, knowledge_id, "KNOWS",
            strength=strength, role=role, since=now_iso(), last_accessed=now_iso(),
        )
        return result is not None

    async def create_contributes_to_relationship(
        self,
        person_id: str,
        project_id: str,
        role: str = "member",
        contribution_score: float = 0.5,
    ) -> bool:
        result = graph_store.upsert_edge(
            person_id, project_id, "CONTRIBUTES_TO",
            role=role, contribution_score=contribution_score, since=now_iso(),
        )
        return result is not None

    async def create_collaborates_with_relationship(
        self,
        person_a_id: str,
        person_b_id: str,
        frequency: int = 1,
        channel: str = "unknown",
    ) -> bool:
        existing = graph_store.get_edge(person_a_id, person_b_id, "COLLABORATES_WITH")
        current_frequency = existing.get("frequency", 0) if existing else 0
        result = graph_store.upsert_edge(
            person_a_id, person_b_id, "COLLABORATES_WITH",
            frequency=current_frequency + frequency, channel=channel, last_interaction=now_iso(),
        )
        return result is not None

    async def create_depends_on_relationship(
        self,
        knowledge_a_id: str,
        knowledge_b_id: str,
        criticality: str = "medium",
    ) -> bool:
        result = graph_store.upsert_edge(
            knowledge_a_id, knowledge_b_id, "DEPENDS_ON",
            criticality=criticality, created_at=now_iso(),
        )
        return result is not None

    # ─── Graph Queries ─────────────────────────────────────────────────────────

    async def get_person_knowledge_graph(self, person_id: str, max_depth: int = 2) -> Dict[str, Any]:
        person = graph_store.get_node(person_id)
        if not person:
            return {}
        knowledge_items = []
        for k, _, edge_data in graph_store.out_edges(person_id, "KNOWS"):
            knowledge_node = graph_store.get_node(k)
            knowledge_items.append({
                "knowledge": knowledge_node,
                "strength": edge_data.get("strength"),
                "role": edge_data.get("role"),
            })
        return {"p": person, "knowledge_items": knowledge_items}

    async def get_knowledge_owners(self, knowledge_id: str) -> List[Dict[str, Any]]:
        owners = []
        for person_id, _, edge_data in graph_store.in_edges(knowledge_id, "KNOWS"):
            person = graph_store.get_node(person_id)
            if not person:
                continue
            owners.append({
                "person_id": person.get("id"),
                "name": person.get("name"),
                "email": person.get("email"),
                "strength": edge_data.get("strength"),
                "role": edge_data.get("role"),
            })
        owners.sort(key=lambda o: o.get("strength") or 0, reverse=True)
        return owners

    async def find_isolated_knowledge(self, org_id: str) -> List[Dict[str, Any]]:
        result = []
        for k in graph_store.nodes_by_label("Knowledge", org_id=org_id):
            kid = k["id"]
            has_owner = len(graph_store.in_edges(kid, "KNOWS")) > 0
            has_relation = graph_store.undirected_neighbors(kid, "RELATES_TO")
            used_by_project = len(graph_store.in_edges(kid, "USES")) > 0
            if not has_owner and not has_relation and not used_by_project:
                result.append({
                    "id": k["id"], "title": k.get("title"), "domain": k.get("domain"),
                    "created_at": k.get("created_at"),
                })
            if len(result) >= 100:
                break
        return result

    async def find_single_owner_critical_knowledge(self, org_id: str) -> List[Dict[str, Any]]:
        result = []
        for k in graph_store.nodes_by_label("Knowledge", org_id=org_id):
            kid = k["id"]
            owners = graph_store.in_edges(kid, "KNOWS")
            if len(owners) == 1:
                result.append({
                    "id": k["id"], "title": k.get("title"), "domain": k.get("domain"),
                    "owner_count": 1, "owner_ids": [owners[0][0]],
                })
        result.sort(key=lambda r: r["id"])
        return result[:200]

    async def get_department_communication_graph(self, org_id: str, days: int = 30) -> List[Dict[str, Any]]:
        people = {p["id"]: p for p in graph_store.nodes_by_label("Person", org_id=org_id)}
        pairs: Dict[tuple, Dict[str, Any]] = {}

        def _accumulate(a_id: str, b_id: str, frequency: int) -> None:
            a, b = people.get(a_id), people.get(b_id)
            if not a or not b:
                return
            dept_a, dept_b = a.get("department"), b.get("department")
            if dept_a == dept_b:
                return
            key = (dept_a, dept_b)
            bucket = pairs.setdefault(key, {"total": 0, "from_people": set(), "to_people": set()})
            bucket["total"] += frequency
            bucket["from_people"].add(a_id)
            bucket["to_people"].add(b_id)

        for u, v, _, data in graph_store.all_edges("COLLABORATES_WITH"):
            if u not in people or v not in people:
                continue
            freq = data.get("frequency", 0)
            _accumulate(u, v, freq)
            _accumulate(v, u, freq)

        return [
            {
                "from_dept": k[0], "to_dept": k[1],
                "total_interactions": v["total"],
                "from_people": len(v["from_people"]),
                "to_people": len(v["to_people"]),
            }
            for k, v in pairs.items()
        ]

    async def get_knowledge_dependency_chain(self, knowledge_id: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        def _dfs(current: str, path: List[Dict[str, Any]], depth: int) -> None:
            if depth >= max_depth:
                return
            for dep_id, _, _ in graph_store.out_edges(current, "DEPENDS_ON"):
                node = graph_store.get_node(dep_id)
                if not node:
                    continue
                new_path = path + [{"id": node["id"], "title": node.get("title")}]
                results.append({"chain": new_path, "depth": len(new_path)})
                _dfs(dep_id, new_path, depth + 1)

        start = graph_store.get_node(knowledge_id)
        if start:
            _dfs(knowledge_id, [{"id": start["id"], "title": start.get("title")}], 0)
        results.sort(key=lambda r: r["depth"])
        return results

    async def find_knowledge_clusters(self, org_id: str) -> List[Dict[str, Any]]:
        result = []
        for k in graph_store.nodes_by_label("Knowledge", org_id=org_id):
            neighbors = graph_store.undirected_neighbors(k["id"], "RELATES_TO")
            if len(neighbors) >= 3:
                result.append({
                    "center_id": k["id"], "title": k.get("title"), "domain": k.get("domain"),
                    "connection_count": len(neighbors),
                    "related_ids": [n[0] for n in neighbors],
                })
        result.sort(key=lambda r: r["connection_count"], reverse=True)
        return result[:20]

    async def get_person_full_profile(self, person_id: str) -> Dict[str, Any]:
        person = graph_store.get_node(person_id)
        if not person:
            return {}

        knowledge = []
        for k, _, edge_data in graph_store.out_edges(person_id, "KNOWS"):
            node = graph_store.get_node(k)
            if node:
                knowledge.append({
                    "id": node["id"], "title": node.get("title"), "domain": node.get("domain"),
                    "strength": edge_data.get("strength"), "role": edge_data.get("role"),
                })

        projects = []
        for proj_id, _, edge_data in graph_store.out_edges(person_id, "CONTRIBUTES_TO"):
            node = graph_store.get_node(proj_id)
            if node:
                projects.append({
                    "id": node["id"], "name": node.get("name"), "status": node.get("status"),
                    "role": edge_data.get("role"),
                })

        collaborators = []
        for colleague_id, edge_data in graph_store.undirected_neighbors(person_id, "COLLABORATES_WITH"):
            node = graph_store.get_node(colleague_id)
            if node:
                collaborators.append({
                    "id": node["id"], "name": node.get("name"),
                    "frequency": edge_data.get("frequency"),
                })

        return {"p": person, "knowledge": knowledge, "projects": projects, "collaborators": collaborators}

    async def simulate_person_departure(self, person_id: str, org_id: str) -> Dict[str, Any]:
        person = graph_store.get_node(person_id)
        if not person:
            return {}

        orphaned_knowledge = []
        for k, _, _ in graph_store.out_edges(person_id, "KNOWS"):
            other_owners = [pid for pid, _, _ in graph_store.in_edges(k, "KNOWS") if pid != person_id]
            if not other_owners:
                node = graph_store.get_node(k)
                if node:
                    orphaned_knowledge.append({"id": node["id"], "title": node.get("title"), "domain": node.get("domain")})

        affected_projects = []
        for proj_id, _, _ in graph_store.out_edges(person_id, "CONTRIBUTES_TO"):
            node = graph_store.get_node(proj_id)
            if node:
                affected_projects.append({"id": node["id"], "name": node.get("name"), "status": node.get("status")})

        return {
            "person_id": person.get("id"),
            "person_name": person.get("name"),
            "orphaned_knowledge_count": len(orphaned_knowledge),
            "orphaned_knowledge": orphaned_knowledge,
            "affected_projects": affected_projects,
        }

    async def get_org_brain_map(self, org_id: str) -> Dict[str, Any]:
        display_field = {"Person": "name", "Knowledge": "title", "Project": "name", "Department": "name"}
        nodes = []
        for label in ("Person", "Knowledge", "Project", "Department"):
            for n in graph_store.nodes_by_label(label, org_id=org_id):
                nodes.append({
                    "type": label,
                    "id": n["id"],
                    "label": n.get(display_field[label]),
                    "domain": n.get("domain"),
                    "connection_count": graph_store.degree(n["id"]),
                })
                if len(nodes) >= 500:
                    break

        node_types = {n["id"]: n["type"] for n in nodes}
        edges = []
        for u, v, rel_type, data in graph_store.all_edges():
            if u not in node_types or v not in node_types:
                continue
            if node_types[u] not in ("Person", "Knowledge", "Project") or node_types[v] not in ("Person", "Knowledge", "Project"):
                continue
            edges.append({
                "source": u, "target": v, "relationship": rel_type,
                "weight": data.get("strength", data.get("frequency", 1)),
            })
            if len(edges) >= 2000:
                break

        return {"nodes": nodes, "edges": edges}

    async def update_knowledge_access(self, knowledge_id: str) -> None:
        node = graph_store.get_node(knowledge_id)
        if not node:
            return
        graph_store.update_node(
            knowledge_id,
            access_count=(node.get("access_count") or 0) + 1,
            last_accessed_at=now_iso(),
        )

    async def count_knowledge(self, org_id: str) -> int:
        return len(graph_store.nodes_by_label("Knowledge", org_id=org_id))

    async def list_knowledge_items_for_analysis(self, org_id: str) -> List[Dict[str, Any]]:
        """
        Real per-item knowledge metadata shaped for the disease-classifier /
        entropy algorithms (which were previously fed hardcoded sample data).
        owner_count/is_isolated are derived from actual graph edges;
        is_documented is approximated from source_type/summary presence since
        the graph schema has no explicit documentation flag.
        """
        items = []
        for k in graph_store.nodes_by_label("Knowledge", org_id=org_id):
            kid = k["id"]
            owners = graph_store.in_edges(kid, "KNOWS")
            has_relation = graph_store.undirected_neighbors(kid, "RELATES_TO")
            used_by_project = graph_store.in_edges(kid, "USES")
            is_isolated = not owners and not has_relation and not used_by_project
            items.append({
                "id": kid,
                "domain": k.get("domain") or "general",
                "dept_id": k.get("department"),
                "owner_count": len(owners),
                "is_documented": bool(k.get("summary")) or k.get("source_type") in ("document", "wiki"),
                "is_isolated": is_isolated,
                "created_at": k.get("created_at"),
                "access_count": k.get("access_count", 0),
                "last_accessed_at": k.get("last_accessed_at"),
                "source_type": k.get("source_type"),
            })
        return items

    async def build_disease_scan_inputs(self, org_id: str) -> Dict[str, Any]:
        """
        Assemble real-data kwargs for `disease_classifier.run_full_disease_scan`.
        Two of the five diseases (memory_alzheimers, innovation_paralysis) need
        employee-departure and idea-tracking history that the current graph
        schema doesn't capture at all — those inputs stay empty on purpose, and
        the classifier already reports "insufficient data" (healthy/0) for them
        rather than fabricating a score. The other three are wired to real data:
        - knowledge_obesity: real created_at/access_count per item
        - communication_stroke: real cross-department COLLABORATES_WITH edges
        - knowledge_cancer: needs embedding similarity (not wired yet) → empty
        """
        knowledge_items = await self.list_knowledge_items_for_analysis(org_id)
        departments = await self.list_departments(org_id)

        access_events = [
            {"knowledge_id": item["id"], "access_date": item["last_accessed_at"]}
            for item in knowledge_items
            if item["access_count"] and item["last_accessed_at"]
        ]

        dept_comms = await self.get_department_communication_graph(org_id)
        now = now_iso()
        collaboration_events = [
            {"from_dept_id": pair["from_dept"], "to_dept_id": pair["to_dept"], "event_date": now}
            for pair in dept_comms
        ]

        return {
            "knowledge_items": knowledge_items,
            "similarity_pairs": [],  # no embedding-similarity pipeline wired yet
            "employee_departures": [],  # no departure tracking in the graph schema yet
            "collaboration_events": collaboration_events,
            "departments": [{"id": d["id"], "name": d["name"]} for d in departments],
            "access_events": access_events,
            "ideas": [],  # no idea/innovation tracking in the graph schema yet
            "projects": [],
        }

    async def search_knowledge(
        self,
        org_id: str,
        query_text: str,
        domain: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        q = query_text.lower()
        result = []
        for k in graph_store.nodes_by_label("Knowledge", org_id=org_id):
            title = (k.get("title") or "").lower()
            summary = (k.get("summary") or "").lower()
            if q not in title and q not in summary:
                continue
            if domain and k.get("domain") != domain:
                continue
            result.append({
                "id": k["id"], "title": k.get("title"), "domain": k.get("domain"),
                "summary": k.get("summary"), "source_type": k.get("source_type"),
                "relevance_score": k.get("relevance_score"),
            })
        result.sort(key=lambda r: r.get("relevance_score") or 0, reverse=True)
        return result[:limit]
