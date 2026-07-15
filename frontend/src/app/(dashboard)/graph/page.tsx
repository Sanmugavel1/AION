"use client";
import { useState, useCallback, useRef, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import {
  Network, Search, ZoomIn, ZoomOut, Maximize2, Plus,
  User, BookOpen, Briefcase, Building2, X,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { mriApi } from "@/lib/api";
import { GraphNode, GraphEdge } from "@/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";

const HEALTH_HEX: Record<string, string> = {
  green: "#3FCF8E",
  yellow: "#F5A623",
  red: "#F45B5B",
};

const NODE_RADIUS: Record<string, number> = {
  Person: 11,
  Knowledge: 7,
  Project: 9,
  Department: 15,
};

const TYPE_META: Record<string, { icon: typeof User; label: string }> = {
  Person: { icon: User, label: "People" },
  Knowledge: { icon: BookOpen, label: "Knowledge" },
  Project: { icon: Briefcase, label: "Projects" },
  Department: { icon: Building2, label: "Departments" },
};

const TYPE_FILTERS = ["all", "Person", "Knowledge", "Project", "Department"];

// Force-simulation cooling — without this the physics pass ran forever at
// 60fps for as long as this page stayed mounted (same bug found and fixed
// on the Org MRI canvas), an ongoing O(n²) cost with no reason to keep
// running once the layout has visibly settled.
const ALPHA_DECAY = 0.02;
const ALPHA_MIN = 0.005;

interface SimNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

export default function GraphPage() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<string>("all");
  const [selectedNode, setSelectedNode] = useState<SimNode | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [isPanning, setIsPanning] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<SimNode[]>([]);
  const rafRef = useRef<number>(0);
  // Alpha persists across effect re-runs (zoom/pan/hover/selection all
  // redefine this effect's closures) so panning or hovering a node doesn't
  // re-trigger the full physics pass — only a genuinely new layout should.
  const alphaRef = useRef(1);
  const dragRef = useRef<{ dragging: boolean; startX: number; startY: number; origin: { x: number; y: number } }>({
    dragging: false, startX: 0, startY: 0, origin: { x: 0, y: 0 },
  });

  const { data, isLoading } = useQuery({
    queryKey: ["mri", "brain-map"],
    queryFn: () => mriApi.getBrainMap(),
    staleTime: 5 * 60 * 1000,
  });

  const allNodes: GraphNode[] = data?.nodes ?? [];
  const allEdges: GraphEdge[] = data?.edges ?? [];

  const nodes = useMemo(() => allNodes.filter((n) => {
    const matchesFilter = filter === "all" || n.type === filter;
    const matchesSearch = !search || n.label?.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  }), [allNodes, filter, search]);

  const visibleIds = useMemo(() => new Set(nodes.map((n) => n.id)), [nodes]);
  const edges = useMemo(
    () => allEdges.filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target)),
    [allEdges, visibleIds],
  );

  const connectedTo = useMemo(() => {
    const activeId = selectedNode?.id ?? hoveredId;
    if (!activeId) return null;
    const set = new Set<string>();
    edges.forEach((e) => {
      if (e.source === activeId) set.add(e.target);
      if (e.target === activeId) set.add(e.source);
    });
    return set;
  }, [edges, selectedNode, hoveredId]);

  const initSim = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const W = canvas.width;
    const H = canvas.height;
    const prev = new Map(nodesRef.current.map((n) => [n.id, n]));
    let hasNewNode = false;
    nodesRef.current = nodes.map((n) => {
      const existing = prev.get(n.id);
      if (existing) return { ...n, x: existing.x, y: existing.y, vx: existing.vx, vy: existing.vy };
      hasNewNode = true;
      return { ...n, x: W / 2 + (Math.random() - 0.5) * W * 0.7, y: H / 2 + (Math.random() - 0.5) * H * 0.7, vx: 0, vy: 0 };
    });
    // Only nodes actually new to the canvas need the physics pass to run
    // again — re-settling on every zoom/pan/hover would make the graph
    // visibly jiggle each time, which is worse than just staying still.
    if (hasNewNode) alphaRef.current = 1;
  }, [nodes]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || nodes.length === 0) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const ro = new ResizeObserver(() => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      initSim();
      alphaRef.current = 1; // canvas size changed — re-settle
      if (!rafRef.current) rafRef.current = requestAnimationFrame(tick);
    });
    ro.observe(canvas);
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    initSim();

    const nodeMap = new Map<string, SimNode>();
    const activeId = selectedNode?.id ?? hoveredId;

    function tick() {
      const ns = nodesRef.current;
      const W = canvas!.width;
      const H = canvas!.height;
      const alpha = alphaRef.current;
      ns.forEach((n) => nodeMap.set(n.id, n));

      ns.forEach((a) => {
        a.vx += (W / 2 - a.x) * 0.0006 * alpha;
        a.vy += (H / 2 - a.y) * 0.0006 * alpha;
        ns.forEach((b) => {
          if (a === b) return;
          const dx = a.x - b.x, dy = a.y - b.y;
          const d = Math.sqrt(dx * dx + dy * dy) || 1;
          const f = (750 / (d * d)) * alpha;
          a.vx += (dx / d) * f;
          a.vy += (dy / d) * f;
        });
        edges.forEach((e) => {
          const s = nodeMap.get(e.source), t = nodeMap.get(e.target);
          if (!s || !t) return;
          const dx = t.x - s.x, dy = t.y - s.y;
          const d = Math.sqrt(dx * dx + dy * dy) || 1;
          const f = (d - 110) * 0.004 * alpha;
          if (a === s) { a.vx += (dx / d) * f; a.vy += (dy / d) * f; }
          if (a === t) { a.vx -= (dx / d) * f; a.vy -= (dy / d) * f; }
        });
        a.vx *= 0.86; a.vy *= 0.86;
        a.x += a.vx; a.y += a.vy;
        a.x = Math.max(20, Math.min(W - 20, a.x));
        a.y = Math.max(20, Math.min(H - 20, a.y));
      });

      ctx!.clearRect(0, 0, W, H);
      ctx!.save();
      ctx!.translate(offset.x, offset.y);
      ctx!.scale(zoom, zoom);

      // Edges — thickness/opacity by weight, accent color for edges touching the active node
      edges.forEach((e) => {
        const s = nodeMap.get(e.source), t = nodeMap.get(e.target);
        if (!s || !t) return;
        const touchesActive = activeId != null && (e.source === activeId || e.target === activeId);
        const w = e.weight ?? 1;
        ctx!.beginPath();
        ctx!.moveTo(s.x, s.y);
        ctx!.lineTo(t.x, t.y);
        if (touchesActive) {
          ctx!.strokeStyle = "rgba(232,184,75,0.65)";
          ctx!.lineWidth = 1.6 + Math.min(w, 4) * 0.4;
        } else {
          ctx!.strokeStyle = `rgba(100,116,139,${0.10 + Math.min(w, 5) * 0.035})`;
          ctx!.lineWidth = 0.7 + Math.min(w, 4) * 0.25;
        }
        ctx!.stroke();
      });

      ns.forEach((n) => {
        const r = NODE_RADIUS[n.type] || 8;
        const color = HEALTH_HEX[n.health_color] || "#64748B";
        const isSelected = selectedNode?.id === n.id;
        const isHovered = hoveredId === n.id;
        const isDimmed = activeId != null && activeId !== n.id && !connectedTo?.has(n.id);

        ctx!.globalAlpha = isDimmed ? 0.25 : 1;

        // Selection/hover ring — precise, no blur halo
        if (isSelected || isHovered) {
          ctx!.beginPath();
          ctx!.arc(n.x, n.y, r + 5, 0, Math.PI * 2);
          ctx!.strokeStyle = isSelected ? "rgba(232,184,75,0.55)" : "rgba(232,184,75,0.32)";
          ctx!.lineWidth = 2;
          ctx!.stroke();
        }

        // Node body — flat fill with a light tint, solid stroke for definition on white
        ctx!.beginPath();
        ctx!.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx!.fillStyle = `${color}20`;
        ctx!.fill();
        ctx!.strokeStyle = isSelected ? "#E8B84B" : isHovered ? "#E8B84B" : color;
        ctx!.lineWidth = isSelected ? 2.5 : isHovered ? 2 : 1.5;
        ctx!.stroke();

        if (zoom > 0.65 && (r >= 9 || isSelected || isHovered)) {
          ctx!.fillStyle = "rgba(15,23,42,0.72)";
          ctx!.font = `${Math.max(9, 10.5 / zoom)}px Inter, sans-serif`;
          ctx!.textAlign = "center";
          ctx!.fillText(n.label?.slice(0, 16) ?? "", n.x, n.y + r + 13);
        }
        ctx!.globalAlpha = 1;
      });

      ctx!.restore();

      alphaRef.current -= ALPHA_DECAY * alpha;
      if (alphaRef.current > ALPHA_MIN) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        alphaRef.current = 0;
        rafRef.current = 0;
      }
    }

    rafRef.current = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(rafRef.current); rafRef.current = 0; ro.disconnect(); };
  }, [data, filter, search, zoom, offset, initSim, selectedNode, hoveredId, connectedTo, nodes, edges]);

  const nodeAtPoint = useCallback((clientX: number, clientY: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const mx = (clientX - rect.left - offset.x) / zoom;
    const my = (clientY - rect.top - offset.y) / zoom;
    return nodesRef.current.find((n) => {
      const r = (NODE_RADIUS[n.type] || 8) + 4;
      return Math.sqrt((n.x - mx) ** 2 + (n.y - my) ** 2) <= r;
    }) ?? null;
  }, [zoom, offset]);

  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    dragRef.current = { dragging: true, startX: e.clientX, startY: e.clientY, origin: offset };
    setIsPanning(true);
  }, [offset]);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (dragRef.current.dragging) {
      const dx = e.clientX - dragRef.current.startX;
      const dy = e.clientY - dragRef.current.startY;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
        setOffset({ x: dragRef.current.origin.x + dx, y: dragRef.current.origin.y + dy });
      }
      return;
    }
    const hit = nodeAtPoint(e.clientX, e.clientY);
    setHoveredId(hit?.id ?? null);
  }, [nodeAtPoint]);

  const handleMouseUp = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const dx = e.clientX - dragRef.current.startX;
    const dy = e.clientY - dragRef.current.startY;
    const wasDrag = Math.abs(dx) > 3 || Math.abs(dy) > 3;
    dragRef.current.dragging = false;
    setIsPanning(false);
    if (!wasDrag) {
      const hit = nodeAtPoint(e.clientX, e.clientY);
      setSelectedNode(hit);
    }
  }, [nodeAtPoint]);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    setZoom((z) => Math.max(0.3, Math.min(3, z - e.deltaY * 0.001)));
  }, []);

  const typeCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    allNodes.forEach((n) => { counts[n.type] = (counts[n.type] ?? 0) + 1; });
    return counts;
  }, [allNodes]);

  return (
    <div className="space-y-4">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-aion-teal-tint text-aion-teal">
              <Network className="h-4 w-4" />
            </span>
            Knowledge Graph Explorer
          </h1>
          <p className="page-subtitle mt-1">Interactive organizational memory graph — drag to pan, scroll to zoom, click a node to inspect it</p>
        </div>
        <Link href="/dashboard/setup">
          <Button size="sm">
            <Plus className="h-4 w-4" /> Add Data
          </Button>
        </Link>
      </motion.div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
        {/* Control sidebar */}
        <motion.div initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.05 }}>
          <div className="card-surface space-y-5 p-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-aion-ink-faint" />
              <Input
                placeholder="Search nodes…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="h-9 pl-9 text-xs"
              />
            </div>

            <div>
              <p className="mb-2 text-2xs font-semibold uppercase tracking-wider text-aion-ink-faint">Node Type</p>
              <div className="space-y-1">
                {TYPE_FILTERS.map((t) => {
                  const meta = t === "all" ? { icon: Network, label: "All Types" } : TYPE_META[t];
                  const Icon = meta.icon;
                  const active = filter === t;
                  return (
                    <button
                      key={t}
                      onClick={() => setFilter(t)}
                      className={cn(
                        "flex w-full cursor-pointer items-center justify-between rounded-md px-3 py-2 text-xs font-medium transition-colors duration-150",
                        active ? "bg-aion-teal-tint text-aion-teal" : "text-aion-ink-muted hover:bg-aion-surface2 hover:text-aion-ink",
                      )}
                    >
                      <span className="flex items-center gap-2">
                        <Icon className="h-3.5 w-3.5" />
                        {meta.label}
                      </span>
                      <span className="tabular-nums opacity-70">{t === "all" ? allNodes.length : typeCounts[t] ?? 0}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <p className="mb-2 text-2xs font-semibold uppercase tracking-wider text-aion-ink-faint">Health Legend</p>
              <div className="space-y-1.5">
                {Object.entries(HEALTH_HEX).map(([k, v]) => (
                  <div key={k} className="flex items-center gap-2 px-3 py-1 text-xs text-aion-ink-muted">
                    <span className="h-2.5 w-2.5 rounded-full border border-black/5" style={{ background: v }} />
                    <span className="capitalize">{k === "green" ? "Healthy" : k === "yellow" ? "Warning" : "Critical"}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-aion-border bg-aion-surface2 p-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-aion-ink-muted">Visible nodes</span>
                <span className="font-semibold tabular-nums text-aion-ink">{nodes.length}</span>
              </div>
              <div className="mt-1.5 flex items-center justify-between text-xs">
                <span className="text-aion-ink-muted">Visible edges</span>
                <span className="font-semibold tabular-nums text-aion-ink">{edges.length}</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Canvas */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
          <Card className="relative overflow-hidden p-0 shadow-glow-teal" style={{ height: 620 }}>
            {isLoading ? (
              <div className="flex h-full items-center justify-center">
                <Network className="h-12 w-12 animate-pulse text-aion-accent" />
              </div>
            ) : nodes.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
                <Network className="h-10 w-10 text-aion-ink-faint" />
                <p className="text-sm text-aion-ink-muted">
                  {search || filter !== "all" ? "No nodes match your filters" : "No graph data available yet"}
                </p>
              </div>
            ) : (
              <canvas
                ref={canvasRef}
                className={cn("h-full w-full bg-aion-bg", isPanning ? "cursor-grabbing" : "cursor-grab")}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={() => { dragRef.current.dragging = false; setIsPanning(false); setHoveredId(null); }}
                onWheel={handleWheel}
              />
            )}

            {/* Zoom toolbar */}
            <div className="absolute right-4 top-4 flex flex-col gap-1 rounded-lg border border-aion-border bg-aion-surface p-1 shadow-card">
              <Button variant="ghost" size="icon-sm" onClick={() => setZoom((z) => Math.min(3, z * 1.2))} aria-label="Zoom in">
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon-sm" onClick={() => setZoom((z) => Math.max(0.3, z / 1.2))} aria-label="Zoom out">
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon-sm" onClick={() => { setZoom(1); setOffset({ x: 0, y: 0 }); }} aria-label="Reset view">
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>

            {/* Node tooltip / inspector */}
            <AnimatePresence>
              {selectedNode && (
                <motion.div
                  initial={{ opacity: 0, y: 6, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 6, scale: 0.98 }}
                  transition={{ duration: 0.15 }}
                  className="absolute bottom-4 left-4 min-w-64 max-w-72 rounded-lg border border-aion-border bg-aion-surface p-4 shadow-card-lg"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <Badge variant="secondary">{selectedNode.type}</Badge>
                    <div className="flex items-center gap-2">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ background: HEALTH_HEX[selectedNode.health_color] ?? "#64748B" }}
                      />
                      <button
                        onClick={() => setSelectedNode(null)}
                        className="cursor-pointer text-aion-ink-faint transition-colors hover:text-aion-ink"
                        aria-label="Dismiss"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                  <p className="mb-1 text-sm font-semibold text-aion-ink">{selectedNode.label}</p>
                  {selectedNode.tooltip && <p className="text-xs text-aion-ink-muted">{selectedNode.tooltip}</p>}
                  <div className="mt-3 flex items-center justify-between border-t border-aion-border pt-2 text-xs">
                    <span className="text-aion-ink-muted">Connections</span>
                    <span className="font-semibold tabular-nums text-aion-teal">{selectedNode.connection_count}</span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
