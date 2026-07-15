"use client";
import { useEffect, useRef, useCallback } from "react";
import { BrainMapResponse, GraphNode, HealthColor } from "@/types";
import { useUIStore } from "@/lib/stores/ui.store";

interface BrainMapCanvasProps {
  data: BrainMapResponse;
}

const HEALTH_COLORS: Record<HealthColor, string> = {
  green: "#3FCF8E",
  yellow: "#F5A623",
  red: "#F45B5B",
};

const NODE_RADIUS: Record<string, number> = {
  Person: 10,
  Knowledge: 7,
  Project: 9,
  Department: 13,
};

interface SimNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

// Standard force-simulation cooling (same idea D3's forceSimulation uses):
// the layout runs at full strength briefly to settle, then alpha decays
// each tick until it crosses a threshold and the RAF loop stops entirely.
// Without this the simulation ran a full O(n²) repulsion pass forever at
// 60fps for as long as the page stayed mounted — real, ongoing CPU cost
// that competed with whatever the user did next, on this page or after
// navigating away during the page-transition overlap.
const ALPHA_DECAY = 0.02;
const ALPHA_MIN = 0.005;

export function BrainMapCanvas({ data }: BrainMapCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<SimNode[]>([]);
  const rafRef = useRef<number>(0);
  const alphaRef = useRef(1);
  const setSelectedNode = useUIStore((s) => s.setSelectedNode);

  const initNodes = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const W = canvas.width;
    const H = canvas.height;

    nodesRef.current = data.nodes.map((n) => ({
      ...n,
      x: W / 2 + (Math.random() - 0.5) * W * 0.8,
      y: H / 2 + (Math.random() - 0.5) * H * 0.8,
      vx: 0,
      vy: 0,
    }));
  }, [data.nodes]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resizeObserver = new ResizeObserver(() => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      initNodes();
      alphaRef.current = 1; // layout changed size — re-settle
      if (!rafRef.current) rafRef.current = requestAnimationFrame(tick);
    });
    resizeObserver.observe(canvas);
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    initNodes();

    const nodeMap = new Map<string, SimNode>();

    function draw() {
      const nodes = nodesRef.current;
      const W = canvas!.width;
      const H = canvas!.height;

      ctx!.clearRect(0, 0, W, H);

      // Edges — muted slate lines, tuned for a light canvas
      data.edges.forEach((e) => {
        const s = nodeMap.get(e.source);
        const t = nodeMap.get(e.target);
        if (!s || !t) return;
        ctx!.beginPath();
        ctx!.moveTo(s.x, s.y);
        ctx!.lineTo(t.x, t.y);
        ctx!.strokeStyle = `rgba(100,116,139,${0.12 + e.weight * 0.08})`;
        ctx!.lineWidth = 0.5 + e.weight * 0.3;
        ctx!.stroke();
      });

      // Nodes
      nodes.forEach((n) => {
        const r = NODE_RADIUS[n.type] || 8;
        const color = HEALTH_COLORS[n.health_color] || "#756B5C";

        // Soft ring for critical nodes — subtle, not a neon glow
        if (n.health_color === "red") {
          ctx!.beginPath();
          ctx!.arc(n.x, n.y, r + 5, 0, Math.PI * 2);
          ctx!.fillStyle = "rgba(244,91,91,0.08)";
          ctx!.fill();
        }

        // Node
        ctx!.beginPath();
        ctx!.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx!.fillStyle = color + "26";
        ctx!.fill();
        ctx!.strokeStyle = color;
        ctx!.lineWidth = 1.5;
        ctx!.stroke();
      });
    }

    function tick() {
      const nodes = nodesRef.current;
      const W = canvas!.width;
      const H = canvas!.height;
      const alpha = alphaRef.current;

      nodes.forEach((n) => nodeMap.set(n.id, n));

      // Force simulation — every force scales with alpha, which decays
      // each tick, so the layout settles instead of running at full
      // strength forever.
      nodes.forEach((a) => {
        // Center gravity
        a.vx += (W / 2 - a.x) * 0.001 * alpha;
        a.vy += (H / 2 - a.y) * 0.001 * alpha;

        // Repulsion
        nodes.forEach((b) => {
          if (a === b) return;
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (600 / (dist * dist)) * alpha;
          a.vx += (dx / dist) * force;
          a.vy += (dy / dist) * force;
        });

        // Edge attraction
        data.edges.forEach((e) => {
          const source = nodeMap.get(e.source);
          const target = nodeMap.get(e.target);
          if (!source || !target) return;
          const dx = target.x - source.x;
          const dy = target.y - source.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (dist - 80) * 0.005 * (e.weight || 1) * alpha;
          if (a === source) { a.vx += (dx / dist) * force; a.vy += (dy / dist) * force; }
          if (a === target) { a.vx -= (dx / dist) * force; a.vy -= (dy / dist) * force; }
        });

        a.vx *= 0.85;
        a.vy *= 0.85;
        a.x += a.vx;
        a.y += a.vy;
        a.x = Math.max(20, Math.min(W - 20, a.x));
        a.y = Math.max(20, Math.min(H - 20, a.y));
      });

      draw();

      alphaRef.current -= ALPHA_DECAY * alpha;
      if (alphaRef.current > ALPHA_MIN) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        // Settled — stop the loop entirely instead of running this O(n²)
        // pass forever. One more draw so the final resting frame is clean.
        alphaRef.current = 0;
        draw();
        rafRef.current = 0;
      }
    }

    alphaRef.current = 1;
    rafRef.current = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = 0;
      resizeObserver.disconnect();
    };
  }, [data, initNodes]);

  // Click handler
  const handleClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const hit = nodesRef.current.find((n) => {
      const r = NODE_RADIUS[n.type] || 8;
      const dx = n.x - mx;
      const dy = n.y - my;
      return Math.sqrt(dx * dx + dy * dy) <= r + 4;
    });

    setSelectedNode(hit ?? null);
  }, [setSelectedNode]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full cursor-crosshair"
      onClick={handleClick}
      aria-label="Organizational brain map visualization"
    />
  );
}
