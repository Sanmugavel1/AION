"""
AION Embedded Graph Store
Lightweight in-process graph engine (NetworkX) that replaces Neo4j for local
and single-node deployments. Same node/relationship model (typed nodes with
properties, typed relationships with properties), persisted to a local JSON
file so data survives restarts. No server, no network, no install beyond a
pure-Python library.
"""
from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class GraphStore:
    """Embedded property-graph store backed by an in-memory NetworkX MultiDiGraph."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._graph = nx.MultiDiGraph()
        self._lock = threading.Lock()
        # Single background worker so file writes stay strictly ordered (no
        # torn/interleaved writes) while the request-handling thread never
        # blocks on graph serialization + disk I/O — see _save().
        self._save_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="graph-store-save")
        self._load()

    # ─── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8"))
                self._graph = nx.node_link_graph(raw, directed=True, multigraph=True, edges="links")
                logger.info(f"Graph store loaded: {self._graph.number_of_nodes()} nodes, "
                            f"{self._graph.number_of_edges()} edges")
            except Exception as e:
                logger.warning(f"Graph store load warning (starting fresh): {e}")
                self._graph = nx.MultiDiGraph()
        else:
            logger.info("Graph store: no existing file, starting fresh")

    def _save(self) -> None:
        # Called from every upsert_node/update_node/upsert_edge/clear, all of
        # which are plain sync methods invoked directly from `async def`
        # FastAPI/repository code with no await — so the full JSON
        # serialize + disk write used to run straight on the event loop
        # thread, freezing every other in-flight request (any user, any
        # endpoint) until it finished. Snapshotting is cheap (structural
        # copy, done here under the caller's lock for consistency); the
        # actual serialize+write is dispatched to a background thread so it
        # never blocks request handling.
        graph_snapshot = self._graph.copy()
        self._save_executor.submit(self._write_snapshot, graph_snapshot)

    def _write_snapshot(self, graph_snapshot: "nx.MultiDiGraph") -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = nx.node_link_data(graph_snapshot, edges="links")
        self._path.write_text(json.dumps(data, default=str), encoding="utf-8")

    # ─── Node Operations ──────────────────────────────────────────────────────

    # NOTE: "id" is never stored inside a node's attribute dict — NetworkX's
    # node_link_data/node_link_graph round-trip reserves the "id" key to mean
    # "this is the node's graph key" and silently drops it as a data attribute
    # on reload if present. It's always derived from the node key on read.

    def upsert_node(self, node_id: str, label: str, **props: Any) -> Dict[str, Any]:
        with self._lock:
            existing = dict(self._graph.nodes[node_id]) if self._graph.has_node(node_id) else {}
            existing.update(props)
            existing.pop("id", None)
            existing["label"] = label
            self._graph.add_node(node_id, **existing)
            self._save()
            return {**{k: v for k, v in existing.items() if k != "label"}, "id": node_id}

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        if not self._graph.has_node(node_id):
            return None
        data = self._graph.nodes[node_id]
        return {**{k: v for k, v in data.items() if k != "label"}, "id": node_id}

    def nodes_by_label(self, label: str, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
        result = []
        for n, data in self._graph.nodes(data=True):
            if data.get("label") != label:
                continue
            if org_id is not None and data.get("org_id") != org_id:
                continue
            result.append({**{k: v for k, v in data.items() if k != "label"}, "id": n})
        return result

    def update_node(self, node_id: str, **props: Any) -> None:
        with self._lock:
            if not self._graph.has_node(node_id):
                return
            self._graph.nodes[node_id].update(props)
            self._save()

    # ─── Edge Operations ───────────────────────────────────────────────────────

    def upsert_edge(self, source: str, target: str, rel_type: str, **props: Any) -> Optional[Dict[str, Any]]:
        with self._lock:
            if not self._graph.has_node(source) or not self._graph.has_node(target):
                return None
            existing = {}
            if self._graph.has_edge(source, target, key=rel_type):
                existing = dict(self._graph[source][target][rel_type])
            existing.update(props)
            self._graph.add_edge(source, target, key=rel_type, **existing)
            self._save()
            return existing

    def get_edge(self, source: str, target: str, rel_type: str) -> Optional[Dict[str, Any]]:
        if self._graph.has_edge(source, target, key=rel_type):
            return dict(self._graph[source][target][rel_type])
        return None

    def out_edges(self, node_id: str, rel_type: Optional[str] = None) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Returns (target_id, rel_type, data) for each outgoing edge."""
        if not self._graph.has_node(node_id):
            return []
        return [
            (v, k, d) for u, v, k, d in self._graph.out_edges(node_id, keys=True, data=True)
            if rel_type is None or k == rel_type
        ]

    def in_edges(self, node_id: str, rel_type: Optional[str] = None) -> List[Tuple[str, str, Dict[str, Any]]]:
        if not self._graph.has_node(node_id):
            return []
        return [
            (u, k, d) for u, v, k, d in self._graph.in_edges(node_id, keys=True, data=True)
            if rel_type is None or k == rel_type
        ]

    def has_edge_either_direction(self, a: str, b: str, rel_type: str) -> bool:
        return self._graph.has_edge(a, b, key=rel_type) or self._graph.has_edge(b, a, key=rel_type)

    def undirected_neighbors(self, node_id: str, rel_type: str) -> List[Tuple[str, Dict[str, Any]]]:
        """All neighbors connected via rel_type, either direction, deduplicated by neighbor id."""
        seen: Dict[str, Dict[str, Any]] = {}
        for u, v, k, d in self._graph.out_edges(node_id, keys=True, data=True):
            if k == rel_type:
                seen[v] = d
        for u, v, k, d in self._graph.in_edges(node_id, keys=True, data=True):
            if k == rel_type and u not in seen:
                seen[u] = d
        return list(seen.items())

    def degree(self, node_id: str) -> int:
        if not self._graph.has_node(node_id):
            return 0
        return self._graph.in_degree(node_id) + self._graph.out_degree(node_id)

    def all_edges(self, rel_type: Optional[str] = None) -> List[Tuple[str, str, str, Dict[str, Any]]]:
        return [
            (u, v, k, d) for u, v, k, d in self._graph.edges(keys=True, data=True)
            if rel_type is None or k == rel_type
        ]

    def clear(self) -> None:
        with self._lock:
            self._graph = nx.MultiDiGraph()
            self._save()


graph_store = GraphStore(settings.GRAPH_STORE_PATH)
