"use client";
import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Loader2, PlayCircle } from "lucide-react";
import { useRunDemo } from "@/lib/hooks/use-auth";

/* ============================================================
   AION — "The Nervous System"
   Ported from aion-final.jsx (user-authored design) into the real
   Next.js app. Visuals kept faithful to the source file; every
   link/button below is now wired to a real destination — internal
   route, in-page anchor, mailto, or the live demo mutation — none
   are left as dead `#` placeholders.
   Tokens: bg #0D0B08 · surface #171310 · gold #D4A94E
           copper #C08A6B · diamond #EDE9E0
   Type: Space Grotesk / Outfit / JetBrains Mono (self-hosted via
   next/font — see globals below, no external @import).
   ============================================================ */

type Slice = { id: string; name: string; nodes: number; findings: number; health: number; note: string };

const SLICES: Slice[] = [
  { id: "S1", name: "Engineering", nodes: 42, findings: 1, health: 81, note: "Signal latency nominal · one L4 coverage gap" },
  { id: "S2", name: "Product", nodes: 18, findings: 0, health: 92, note: "All pathways responsive" },
  { id: "S3", name: "Sales — West", nodes: 27, findings: 3, health: 58, note: "Blocked pathway · attrition precursor firing" },
  { id: "S4", name: "Operations", nodes: 23, findings: 1, health: 74, note: "Succession exposure at director level" },
  { id: "S5", name: "Leadership", nodes: 9, findings: 2, health: 66, note: "Single pathway carries 31% of decisions" },
];

const STAGES = [
  { n: "01", t: "Sense", d: "HR records, calendars, org charts and decision logs are ingested. No surveys. Nobody changes how they work." },
  { n: "02", t: "Map", d: "AION grows a nervous system over your organization — every reporting line, relationship and decision path becomes a pathway." },
  { n: "03", t: "Listen", d: "Signals fire continuously. Healthy pathways stay quiet; stressed ones start firing in patterns AION recognizes." },
  { n: "04", t: "Diagnose", d: "Firing patterns are matched against a library of known organizational diseases and ranked by severity." },
  { n: "05", t: "Localize", d: "A specific team, role or relationship is flagged — with the evidence chain behind it, not just a red dot." },
  { n: "06", t: "Respond", d: "A board-ready reflex: the diagnosis plus one simulated intervention, delivered before the risk becomes a resignation." },
];

const MODULES = [
  { n: "01", name: "Knowledge Graph", tag: "Substrate", d: "The living map of who reports to whom, who decides with whom, and where knowledge actually lives.", href: "/dashboard/graph" },
  { n: "02", name: "Org MRI", tag: "Imaging", d: "Full structural scan. Weak points surface here weeks before they surface in exit interviews.", href: "/dashboard/mri" },
  { n: "03", name: "Diseases", tag: "Pathology", d: "Firing patterns matched against known failures: silent attrition, bottlenecks, authority vacuums.", href: "/dashboard/diseases" },
  { n: "04", name: "Decay", tag: "Longitudinal", d: "Cohesion and engagement tracked cohort by cohort — decline becomes a curve you watch, not a shock.", href: "/dashboard/decay" },
  { n: "05", name: "Simulation", tag: "Prognosis", d: "Model a reorg, a departure, a key hire, and watch the signal ripple through the pathways before you commit.", href: "/dashboard/simulation" },
  { n: "06", name: "Successor Intelligence", tag: "Continuity", d: "Who is actually ready to step up — and where one resignation leaves a pathway severed.", href: "/dashboard/ocsie" },
  { n: "07", name: "OCSIE", tag: "Exposure", d: "The cost of losing any one person, quantified today, not discovered the week after they leave.", href: "/dashboard/ocsie" },
  { n: "08", name: "Executive Dashboard", tag: "Reflex", d: "One Monday-morning view: state of the org, the signals that matter this week, and the response.", href: "/dashboard/board" },
];

const FAQS = [
  { q: "What data does AION need access to?", a: "Read-only connections to your HRIS, calendar, and org chart. Optionally, decision logs from tools like Jira or Notion. No message content is read — AION works on metadata and structure, never on what people say." },
  { q: "How long until the first report?", a: "One week from intake to first reading for organizations under 2,000 people. The Monday board briefing runs automatically from then on." },
  { q: "Is this employee surveillance?", a: "No. AION never scores or profiles individuals. Findings are structural — about roles, coverage, and pathways — and reports are aggregated at team level with a minimum group size." },
  { q: "How is this different from an engagement survey?", a: "Surveys measure what people say when asked, twice a year. AION reads how the organization actually functions, continuously — and catches the six-week window between structural damage and visible symptoms." },
];

/* ---------- Full-bleed ambient field reused on every section so the page
   keeps its "spread out" feel past the hero instead of narrowing back to a
   centered column. Static (no animation) for the same GPU-cost reason as
   the dashboard background fix. Each section passes a different `variant`
   so the clusters/shards don't look mechanically copy-pasted while scrolling. ---------- */
type FieldSpec = { clusters: { pos: React.CSSProperties; size: string; rgb: string; peak: number }[]; shards: { pos: React.CSSProperties; size: number; rotate: number; color: string }[] };
/* Every position is anchored within ~20% of a top or bottom edge (never a
   mid-section percentage) — several of these sections are long scrolling
   lists (the Method/Platform steps run for multiple screens), so anything
   placed at e.g. top:55% lands in a dead zone with nothing else around it
   to relate to. Edge-anchoring means the decoration is visible at every
   section transition regardless of how tall the section's content is. */
const FIELD_VARIANTS: FieldSpec[] = [
  { clusters: [
      { pos: { left: "-12%", top: "4%" }, size: "26vw", rgb: "222,178,85", peak: 0.55 },
      { pos: { right: "-11%", bottom: "6%" }, size: "24vw", rgb: "192,138,107", peak: 0.5 },
    ],
    shards: [
      { pos: { top: "12%", left: "3%" }, size: 14, rotate: 15, color: "#DEB255" },
      { pos: { bottom: "10%", left: "5%" }, size: 11, rotate: -22, color: "#C08A6B" },
      { pos: { top: "16%", right: "3%" }, size: 16, rotate: 28, color: "#F3D488" },
    ] },
  { clusters: [
      { pos: { right: "-13%", top: "3%" }, size: "28vw", rgb: "222,178,85", peak: 0.52 },
      { pos: { left: "-10%", bottom: "4%" }, size: "22vw", rgb: "248,231,184", peak: 0.42 },
    ],
    shards: [
      { pos: { top: "9%", right: "4%" }, size: 15, rotate: -18, color: "#F3D488" },
      { pos: { bottom: "14%", left: "2%" }, size: 12, rotate: 30, color: "#DEB255" },
      { pos: { bottom: "6%", right: "6%" }, size: 11, rotate: -8, color: "#C08A6B" },
    ] },
  { clusters: [
      { pos: { left: "-11%", bottom: "8%" }, size: "24vw", rgb: "192,138,107", peak: 0.5 },
      { pos: { right: "-12%", top: "5%" }, size: "22vw", rgb: "222,178,85", peak: 0.55 },
    ],
    shards: [
      { pos: { top: "14%", left: "4%" }, size: 13, rotate: 20, color: "#DEB255" },
      { pos: { bottom: "12%", right: "3%" }, size: 15, rotate: -30, color: "#F3D488" },
    ] },
];

/* Radial-gradient falloff instead of solid-fill + blur(): a blurred solid
   disc still shows a visible silhouette at these sizes (reads as a stock
   "SaaS gradient blob"). A gradient with its own transparent tail has no
   edge to begin with — reads as ambient light, not a shape. */
function clusterGlow(rgb: string, peak: number) {
  return `radial-gradient(circle, rgba(${rgb},${peak}) 0%, rgba(${rgb},${peak * 0.32}) 45%, rgba(${rgb},0) 72%)`;
}

function SectionField({ variant }: { variant: number }) {
  const spec = FIELD_VARIANTS[variant % FIELD_VARIANTS.length];
  return (
    <div className="bg-field" aria-hidden="true">
      {spec.clusters.map((c, i) => (
        <div key={i} className="cluster" style={{ ...c.pos, width: c.size, height: c.size, background: clusterGlow(c.rgb, c.peak) }} />
      ))}
      {spec.shards.map((s, i) => (
        <svg key={i} className="shard" viewBox="0 0 10 10"
          style={{ ...s.pos, width: s.size, height: s.size, transform: `rotate(${s.rotate}deg)` }}>
          <polygon points="5,0 10,10 0,10" fill={s.color} />
        </svg>
      ))}
    </div>
  );
}

/* ---------- Real AION mark — cropped from the brand's own logo artwork,
   not a hand-drawn approximation (public/aion-mark-circle.png). ---------- */
function AionMark({ size = 30 }: { size?: number }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/aion-mark-circle.png"
      alt="AION"
      width={size}
      height={size}
      style={{ width: size, height: size, borderRadius: "50%", boxShadow: "0 0 0 1px rgba(212,169,78,0.35)" }}
      draggable={false}
    />
  );
}

function Wordmark({ h = 20 }: { h?: number }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "0.14em", fontFamily: "var(--disp)", fontWeight: 700, fontSize: h, letterSpacing: "0.14em", color: "var(--ink)" }}>
      AI
      <svg width={h * 0.92} height={h * 0.92} viewBox="0 0 24 24" style={{ margin: "0 0.02em" }} aria-hidden="true">
        <circle cx="12" cy="12" r="10.5" fill="none" stroke="#C08A6B" strokeWidth="2.4" />
        <circle cx="12" cy="12" r="3" fill="#C08A6B" />
        <path d="M12 4.5 v4 M12 15.5 v4 M4.5 12 h4 M15.5 12 h4" stroke="#C08A6B" strokeWidth="1.6" />
      </svg>
      N
    </span>
  );
}

/* ============================================================
   THE INSTRUMENT — one chronometer housing, five complications.
   ============================================================ */

const REDUCE = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// Math.cos/sin can return non-bit-identical floats between server (Node) and
// client (browser) V8 builds — rounding every trig-derived value that lands
// directly in JSX (not just refs mutated post-mount) avoids SSR/CSR hydration
// mismatches on the last float digit.
const rnd = (n: number) => Math.round(n * 1000) / 1000;

/* ---------- S1 · Engineering — orbital gyroscope ---------- */
type Orbit = { rx: number; ry: number; phi: number; speed: number };
const ORBITS: Orbit[] = [
  { rx: 158, ry: 58, phi: -16, speed: 0.05 },
  { rx: 118, ry: 44, phi: 26, speed: -0.075 },
  { rx: 80, ry: 30, phi: -54, speed: 0.11 },
];

function orbitPoint(orbit: Orbit, theta: number, cx = 200, cy = 200) {
  const phi = (orbit.phi * Math.PI) / 180;
  const x = cx + orbit.rx * Math.cos(theta) * Math.cos(phi) - orbit.ry * Math.sin(theta) * Math.sin(phi);
  const y = cy + orbit.rx * Math.cos(theta) * Math.sin(phi) + orbit.ry * Math.sin(theta) * Math.cos(phi);
  const depth = (Math.sin(theta) + 1) / 2;
  return { x, y, depth };
}

function OrbitsComplication({ slice }: { slice: Slice }) {
  const nodeRefs = useRef<(SVGGElement | null)[]>([]);
  const nodes = React.useMemo(() => {
    let seed = slice.id.charCodeAt(1) * 48271;
    const rand = () => ((seed = (seed * 16807) % 2147483647), seed / 2147483647);
    const counts = [
      Math.min(9, Math.ceil(slice.nodes * 0.22)),
      Math.min(7, Math.ceil(slice.nodes * 0.16)),
      Math.min(5, Math.ceil(slice.nodes * 0.1)),
    ];
    const out: { orbit: number; base: number; risk: boolean }[] = [];
    let riskLeft = slice.findings;
    counts.forEach((c, oi) => {
      for (let i = 0; i < c; i++) {
        const risk = oi === 0 && riskLeft > 0 && i < slice.findings;
        if (risk) riskLeft--;
        out.push({ orbit: oi, base: rand() * Math.PI * 2, risk });
      }
    });
    return out;
  }, [slice]);

  useEffect(() => {
    let raf: number, t = 0;
    const reduce = REDUCE();
    const tick = () => {
      t += 1;
      nodes.forEach((n, i) => {
        const el = nodeRefs.current[i];
        if (!el) return;
        const theta = n.base + (reduce ? 0 : t * 0.016 * ORBITS[n.orbit].speed * Math.PI);
        const p = orbitPoint(ORBITS[n.orbit], theta);
        const dot = el.querySelector(".od") as SVGCircleElement;
        const halo = el.querySelector(".oh") as SVGCircleElement | null;
        const r = (n.risk ? 3.4 : 2.4) * (0.72 + p.depth * 0.5);
        dot.setAttribute("cx", String(p.x)); dot.setAttribute("cy", String(p.y));
        dot.setAttribute("r", String(r));
        dot.setAttribute("opacity", String(0.35 + p.depth * 0.65));
        if (halo) {
          const fl = 0.5 + 0.5 * Math.sin(t * 0.09 + i);
          halo.setAttribute("cx", String(p.x)); halo.setAttribute("cy", String(p.y));
          halo.setAttribute("r", String(r * 3.6));
          halo.setAttribute("opacity", String((0.12 + fl * 0.16) * (0.5 + p.depth * 0.5)));
        }
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [nodes]);

  return (
    <g>
      {ORBITS.map((o, i) => (
        <ellipse key={i} cx="200" cy="200" rx={o.rx} ry={o.ry}
          transform={`rotate(${o.phi} 200 200)`} fill="none"
          stroke={i === 1 ? "rgba(192,138,107,0.30)" : "rgba(212,169,78,0.26)"} strokeWidth="0.9" />
      ))}
      <DiamondCore />
      {nodes.map((n, i) => (
        <g key={i} ref={(el) => { nodeRefs.current[i] = el; }}>
          {n.risk && <circle className="oh" fill="#C4564A" opacity={0} />}
          <circle className="od" fill={n.risk ? "#C4564A" : "#E9C56B"} />
        </g>
      ))}
    </g>
  );
}

/* ---------- S2 · Product — the prism ---------- */
function PrismComplication() {
  const beamRefs = useRef<(SVGCircleElement | null)[]>([]);
  const OUT = 7;
  const beams = React.useMemo(() =>
    Array.from({ length: OUT }, (_, i) => {
      const a = ((i - (OUT - 1) / 2) / (OUT - 1)) * 1.15;
      return { a, x2: rnd(200 + Math.cos(a) * 150), y2: rnd(200 + Math.sin(a) * 150), phase: i * 0.9 };
    }), []);

  useEffect(() => {
    let raf: number, t = 0;
    const reduce = REDUCE();
    const tick = () => {
      t += 1;
      beams.forEach((b, i) => {
        const el = beamRefs.current[i];
        if (!el) return;
        const q = reduce ? 0.7 : ((t * 0.012 + b.phase) % 1.6) / 1.6;
        const vis = q < 1 ? q : 1;
        const x = 200 + (b.x2 - 200) * vis;
        const y = 200 + (b.y2 - 200) * vis;
        el.setAttribute("cx", String(x)); el.setAttribute("cy", String(y));
        el.setAttribute("opacity", String(q < 1 ? 0.9 * Math.sin(vis * Math.PI) : 0));
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [beams]);

  return (
    <g>
      <line x1="40" y1="200" x2="186" y2="200" stroke="url(#inputBeam)" strokeWidth="1.6" />
      <circle cx="40" cy="200" r="2.6" fill="#EDE9E0" opacity="0.9" />
      {beams.map((b, i) => (
        <g key={i}>
          <line x1="214" y1="200" x2={b.x2} y2={b.y2}
            stroke={i % 2 ? "rgba(192,138,107,0.4)" : "rgba(212,169,78,0.45)"} strokeWidth="1" />
          <circle cx={b.x2} cy={b.y2} r="2.6" fill={i % 2 ? "#C08A6B" : "#E9C56B"} opacity="0.9" />
          <circle ref={(el) => { beamRefs.current[i] = el; }} r="1.8" fill="#EDE9E0" opacity={0} />
        </g>
      ))}
      <DiamondCore big />
      <circle cx="200" cy="200" r="160" fill="none" stroke="rgba(95,168,114,0.25)" strokeWidth="1" strokeDasharray="1 7" />
    </g>
  );
}

/* ---------- S3 · Sales-West — the bottleneck ---------- */
function BottleneckComplication() {
  const dotRefs = useRef<(SVGCircleElement | null)[]>([]);
  const throatRef = useRef<SVGCircleElement | null>(null);
  const IN = [
    "M 48 96 C 130 96, 160 176, 208 196",
    "M 42 148 C 120 148, 165 184, 208 198",
    "M 40 200 C 120 200, 168 200, 208 200",
    "M 42 252 C 120 252, 165 216, 208 202",
    "M 48 304 C 130 304, 160 224, 208 204",
  ];
  const OUTP = "M 216 200 C 268 200, 310 200, 352 200";
  const DOTS = [
    { path: 0, off: 0.05, risk: false }, { path: 0, off: 0.5, risk: true },
    { path: 1, off: 0.25, risk: false }, { path: 1, off: 0.7, risk: false },
    { path: 2, off: 0.4, risk: true }, { path: 2, off: 0.9, risk: false },
    { path: 3, off: 0.15, risk: false }, { path: 3, off: 0.6, risk: true },
    { path: 4, off: 0.35, risk: false }, { path: 4, off: 0.8, risk: false },
  ];

  useEffect(() => {
    const paths = IN.map((d) => {
      const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
      p.setAttribute("d", d);
      return p;
    });
    let raf: number, t = 0;
    const reduce = REDUCE();
    const queueEase = (q: number) => (q < 0.6 ? q * 1.35 : 0.81 + (q - 0.6) * 0.475);
    const tick = () => {
      t += 1;
      DOTS.forEach((d, i) => {
        const el = dotRefs.current[i];
        if (!el) return;
        const raw = reduce ? d.off : (d.off + t * 0.0011) % 1;
        const q = Math.min(queueEase(raw), 0.995);
        const path = paths[d.path];
        const L = path.getTotalLength();
        const pt = path.getPointAtLength(q * L);
        el.setAttribute("cx", String(pt.x)); el.setAttribute("cy", String(pt.y));
        el.setAttribute("opacity", String(0.5 + q * 0.5));
      });
      if (throatRef.current && !reduce) {
        throatRef.current.setAttribute("opacity", String(0.35 + 0.3 * Math.sin(t * 0.07)));
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <g>
      {IN.map((d, i) => (
        <path key={i} d={d} fill="none" stroke="rgba(212,169,78,0.3)" strokeWidth="1" />
      ))}
      <path d={OUTP} fill="none" stroke="rgba(192,138,107,0.35)" strokeWidth="1" strokeDasharray="3 4" />
      <circle ref={throatRef} cx="212" cy="200" r="16" fill="none" stroke="#C4564A" strokeWidth="1.4" opacity="0.5" />
      <circle cx="212" cy="200" r="7" fill="none" stroke="rgba(196,86,74,0.85)" strokeWidth="1.6" />
      <circle cx="212" cy="200" r="2.4" fill="#C4564A" />
      <circle cx="352" cy="200" r="2.6" fill="rgba(233,197,107,0.55)" />
      {DOTS.map((d, i) => (
        <circle key={i} ref={(el) => { dotRefs.current[i] = el; }} r={d.risk ? 3 : 2.2}
          fill={d.risk ? "#C4564A" : "#E9C56B"} opacity={0} />
      ))}
    </g>
  );
}

/* ---------- S4 · Operations — the gear train ---------- */
function gearPath(cx: number, cy: number, r: number, teeth: number, toothH: number) {
  const pts: string[] = [];
  const steps = teeth * 4;
  for (let i = 0; i < steps; i++) {
    const a = (i / steps) * Math.PI * 2;
    const phase = i % 4;
    const rr = phase === 0 || phase === 3 ? r : r + toothH;
    pts.push(`${(cx + Math.cos(a) * rr).toFixed(1)},${(cy + Math.sin(a) * rr).toFixed(1)}`);
  }
  return `M ${pts.join(" L ")} Z`;
}

function GearsComplication() {
  const gearRefs = useRef<(SVGGElement | null)[]>([]);
  const GEARS = [
    { cx: 168, cy: 188, r: 52, teeth: 12, h: 8, speed: 0.22, col: "rgba(212,169,78,0.6)" },
    { cx: 254, cy: 226, r: 36, teeth: 9, h: 7, speed: -0.294, col: "rgba(192,138,107,0.6)" },
    { cx: 214, cy: 118, r: 26, teeth: 7, h: 6, speed: -0.44, col: "rgba(212,169,78,0.45)" },
  ];
  useEffect(() => {
    let raf: number, t = 0;
    const reduce = REDUCE();
    const tick = () => {
      t += 1;
      GEARS.forEach((g, i) => {
        const el = gearRefs.current[i];
        if (el && !reduce) el.setAttribute("transform", `rotate(${(t * g.speed) % 360} ${g.cx} ${g.cy})`);
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <g>
      {GEARS.map((g, i) => (
        <g key={i} ref={(el) => { gearRefs.current[i] = el; }}>
          <path d={gearPath(g.cx, g.cy, g.r, g.teeth, g.h)} fill="none" stroke={g.col} strokeWidth="1.1" />
          <circle cx={g.cx} cy={g.cy} r={g.r * 0.45} fill="none" stroke={g.col} strokeWidth="0.8" />
          <circle cx={g.cx} cy={g.cy} r="3" fill={i === 1 ? "#C08A6B" : "#E9C56B"} />
        </g>
      ))}
      <g opacity="0.85">
        <path d={gearPath(300, 128, 26, 7, 6)} fill="none" stroke="#C4564A" strokeWidth="1.1" strokeDasharray="4 5" />
        <circle cx="300" cy="128" r="11.7" fill="none" stroke="rgba(196,86,74,0.5)" strokeWidth="0.8" strokeDasharray="3 4" />
        <text x="300" y="132" textAnchor="middle" fill="#C4564A" style={{ font: "500 9px 'JetBrains Mono', monospace" }}>?</text>
      </g>
      <text x="300" y="172" textAnchor="middle" fill="rgba(196,86,74,0.8)"
        style={{ font: "400 7px 'JetBrains Mono', monospace", letterSpacing: "0.16em" }}>
        NO SUCCESSOR
      </text>
    </g>
  );
}

/* ---------- S5 · Leadership — hub under load ---------- */
function HubComplication() {
  const pulseRefs = useRef<(SVGCircleElement | null)[]>([]);
  const shockRef = useRef<SVGCircleElement | null>(null);
  const SPOKES = 9;
  const spokes = React.useMemo(() =>
    Array.from({ length: SPOKES }, (_, i) => {
      const a = (i / SPOKES) * Math.PI * 2 - Math.PI / 2;
      return { a, x: rnd(200 + Math.cos(a) * 128), y: rnd(200 + Math.sin(a) * 128), phase: (i * 0.37) % 1 };
    }), []);

  useEffect(() => {
    let raf: number, t = 0;
    const reduce = REDUCE();
    const tick = () => {
      t += 1;
      spokes.forEach((s, i) => {
        const el = pulseRefs.current[i];
        if (!el) return;
        const q = reduce ? 0.5 : (s.phase + t * 0.007) % 1;
        const x = s.x + (200 - s.x) * q;
        const y = s.y + (200 - s.y) * q;
        el.setAttribute("cx", String(x)); el.setAttribute("cy", String(y));
        el.setAttribute("opacity", String(0.85 * Math.sin(q * Math.PI)));
      });
      if (shockRef.current && !reduce) {
        const q = (t * 0.011) % 1;
        shockRef.current.setAttribute("r", String(14 + q * 46));
        shockRef.current.setAttribute("opacity", String(0.4 * (1 - q)));
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [spokes]);

  const arc = (r: number, a0: number, a1: number) => {
    const p0 = [rnd(200 + Math.cos(a0) * r), rnd(200 + Math.sin(a0) * r)];
    const p1 = [rnd(200 + Math.cos(a1) * r), rnd(200 + Math.sin(a1) * r)];
    const large = a1 - a0 > Math.PI ? 1 : 0;
    return `M ${p0[0]} ${p0[1]} A ${r} ${r} 0 ${large} 1 ${p1[0]} ${p1[1]}`;
  };

  return (
    <g>
      {spokes.map((s, i) => (
        <g key={i}>
          <line x1={s.x} y1={s.y} x2="200" y2="200" stroke="rgba(212,169,78,0.24)" strokeWidth="0.9" />
          <circle cx={s.x} cy={s.y} r="2.6" fill="#E9C56B" opacity="0.85" />
        </g>
      ))}
      <path d={arc(150, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * 0.31)}
        fill="none" stroke="#C4564A" strokeWidth="2.4" strokeLinecap="round" opacity="0.85" />
      <path d={arc(150, -Math.PI / 2 + Math.PI * 2 * 0.31, -Math.PI / 2 + Math.PI * 2 * 0.999)}
        fill="none" stroke="rgba(212,169,78,0.18)" strokeWidth="1" />
      <text x="200" y="60" textAnchor="middle" fill="#C4564A"
        style={{ font: "500 8px 'JetBrains Mono', monospace", letterSpacing: "0.14em" }}>
        31% LOAD
      </text>
      <circle ref={shockRef} cx="200" cy="200" r="14" fill="none" stroke="#C4564A" strokeWidth="1" opacity={0} />
      <circle cx="200" cy="200" r="11" fill="none" stroke="rgba(196,86,74,0.8)" strokeWidth="1.4" />
      <DiamondCore small />
      {spokes.map((s, i) => (
        <circle key={i} ref={(el) => { pulseRefs.current[i] = el; }} r="1.9" fill="#E9C56B" opacity={0} />
      ))}
    </g>
  );
}

function DiamondCore({ big, small }: { big?: boolean; small?: boolean }) {
  const s = big ? 13 : small ? 6.5 : 9;
  return (
    <g>
      <circle cx="200" cy="200" r={s * 4.6} fill="url(#coreGlow)" className="core-breathe" />
      <g transform="rotate(45 200 200)">
        <rect x={200 - s} y={200 - s} width={s * 2} height={s * 2}
          fill="url(#diamondFacet)" stroke="rgba(212,169,78,0.9)" strokeWidth="1" />
        <rect x={200 - s / 2} y={200 - s / 2} width={s} height={s}
          fill="none" stroke="rgba(156,124,60,0.55)" strokeWidth="0.7" />
      </g>
    </g>
  );
}

function Instrument({ slice }: { slice: Slice }) {
  const ticks = [];
  for (let i = 0; i < 72; i++) {
    const a = (i / 72) * Math.PI * 2 - Math.PI / 2;
    const major = i % 6 === 0;
    const r1 = major ? 176 : 181, r2 = 187;
    ticks.push(
      <line key={i}
        x1={rnd(200 + Math.cos(a) * r1)} y1={rnd(200 + Math.sin(a) * r1)}
        x2={rnd(200 + Math.cos(a) * r2)} y2={rnd(200 + Math.sin(a) * r2)}
        stroke={major ? "#D4A94E" : "rgba(212,169,78,0.25)"}
        strokeWidth={major ? 1.4 : 0.8} opacity={major ? 0.8 : 1} />
    );
  }

  const complication =
    slice.id === "S1" ? <OrbitsComplication slice={slice} /> :
    slice.id === "S2" ? <PrismComplication /> :
    slice.id === "S3" ? <BottleneckComplication /> :
    slice.id === "S4" ? <GearsComplication /> :
    <HubComplication />;

  return (
    <svg viewBox="0 0 400 400" style={{ width: "100%", height: "100%", display: "block" }} role="img"
      aria-label={`Organizational instrument for ${slice.name}: ${slice.nodes} pathways, ${slice.findings} risk signals`}>
      <defs>
        <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(212,169,78,0.35)" />
          <stop offset="45%" stopColor="rgba(212,169,78,0.10)" />
          <stop offset="100%" stopColor="rgba(212,169,78,0)" />
        </radialGradient>
        <linearGradient id="bezelSheen" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="rgba(233,197,107,0.5)" />
          <stop offset="50%" stopColor="rgba(212,169,78,0.15)" />
          <stop offset="100%" stopColor="rgba(156,124,60,0.45)" />
        </linearGradient>
        <linearGradient id="diamondFacet" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="55%" stopColor="#EDE9E0" />
          <stop offset="100%" stopColor="#C9C2B2" />
        </linearGradient>
        <linearGradient id="inputBeam" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="rgba(237,233,224,0)" />
          <stop offset="100%" stopColor="rgba(237,233,224,0.7)" />
        </linearGradient>
      </defs>

      <circle cx="200" cy="200" r="190" fill="none" stroke="url(#bezelSheen)" strokeWidth="1.6" />
      <circle cx="200" cy="200" r="172" fill="none" stroke="rgba(212,169,78,0.14)" strokeWidth="1" />
      <g>{ticks}</g>
      <circle cx="200" cy="200" r="52" fill="none" stroke="rgba(192,138,107,0.12)" strokeWidth="0.8" />

      <g key={slice.id} className="comp-enter">{complication}</g>

      <text x="200" y="34" textAnchor="middle" fill="rgba(110,104,88,0.9)"
        style={{ font: "500 8.5px 'JetBrains Mono', monospace", letterSpacing: "0.28em" }}>
        {slice.name.toUpperCase()}
      </text>
      <text x="200" y="378" textAnchor="middle" fill="rgba(110,104,88,0.7)"
        style={{ font: "400 7.5px 'JetBrains Mono', monospace", letterSpacing: "0.22em" }}>
        {slice.nodes} PATHWAYS · {slice.findings} SIGNAL{slice.findings !== 1 ? "S" : ""}
      </text>
    </svg>
  );
}

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll("[data-rv]");
    const io = new IntersectionObserver(
      (es) => es.forEach((e) => e.isIntersecting && (e.target.classList.add("rv-in"), io.unobserve(e.target))),
      { threshold: 0.1 }
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);
}

const NAV_ITEMS = [
  { label: "Method", href: "#method" },
  { label: "Platform", href: "#platform" },
  { label: "Sample report", href: "#report" },
  { label: "FAQ", href: "#faq" },
];

export default function AionHome() {
  const [slice, setSlice] = useState(SLICES[0]);
  const [stage, setStage] = useState(0);
  const [openFaq, setOpenFaq] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  const stagesRef = useRef<HTMLDivElement>(null);
  useReveal();
  const runDemo = useRunDemo();

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 24);
      const el = stagesRef.current;
      if (el) {
        const rect = el.getBoundingClientRect();
        const p = Math.min(Math.max((window.innerHeight * 0.6 - rect.top) / rect.height, 0), 0.999);
        setStage(Math.floor(p * STAGES.length));
      }
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const healthColor = (h: number) => (h >= 80 ? "#5FA872" : h >= 65 ? "#D9B25C" : "#C4564A");

  return (
    <div className="an-root">
      <style>{`
        .an-root{
          --bg:#0D0B08; --surface:#171310; --surface2:#1E1913;
          --gold:#DEB255; --gold-hi:#F3D488; --gold-dim:#A9781F; --gold-deep:#8A6420;
          --metal: linear-gradient(120deg, #8A6420 0%, #DEB255 26%, #F8E7B8 50%, #DEB255 74%, #A9781F 100%);
          --copper:#C08A6B; --copper-dim:#8A6350;
          --diamond:#EDE9E0;
          --ink:#EDE8DD; --dim:#A79F8E; --faint:#6E6858;
          --green:#5FA872; --yellow:#D9B25C; --red:#C4564A;
          --hair:rgba(222,178,85,0.16); --hair-c:rgba(192,138,107,0.18); --hair2:rgba(237,232,221,0.07);
          --disp:var(--font-space-grotesk),'Space Grotesk',sans-serif;
          --body:var(--font-outfit),'Outfit',sans-serif;
          --mono:var(--font-jetbrains),'JetBrains Mono',monospace;
          --ease:cubic-bezier(0.16,1,0.3,1);
          background:radial-gradient(ellipse 120% 60% at 50% 0%, #1A140C 0%, var(--bg) 55%), var(--bg); color:var(--ink);
          font-family:var(--body); font-weight:300; line-height:1.65;
          min-height:100vh; overflow-x:hidden;
        }
        .an-root *{ box-sizing:border-box; margin:0; padding:0; }
        .an-root ::selection{ background:var(--gold); color:var(--bg); }
        .an-root a{ color:inherit; text-decoration:none; }
        .an-root :focus-visible{ outline:2px solid var(--gold); outline-offset:3px; }
        .an-root button{ font-family:inherit; cursor:pointer; }
        .an-root h1,.an-root h2,.an-root h3{ font-family:var(--disp); font-weight:600; letter-spacing:-0.02em; text-shadow:0 0 30px rgba(237,232,221,0.14); }
        .g{ background:var(--metal); -webkit-background-clip:text; background-clip:text; color:transparent;
          filter:drop-shadow(0 0 22px rgba(222,178,85,0.5)) drop-shadow(0 0 46px rgba(222,178,85,0.22)); }
        .gold-edge{ border:1px solid transparent; background-origin:border-box; background-clip:padding-box, border-box; }
        .c{ color:var(--copper); text-shadow:0 0 18px rgba(192,138,107,0.5); }

        .wrap{ max-width:1600px; margin:0 auto; padding:0 36px; }
        @media(max-width:720px){ .wrap{ padding:0 20px; } }

        .eyebrow{ font-family:var(--mono); font-size:11px; letter-spacing:0.2em; text-transform:uppercase; color:var(--copper); display:flex; gap:12px; align-items:center; }
        .eyebrow::before{ content:''; width:16px; height:1px; background:var(--copper-dim); }

        [data-rv]{ opacity:0; transform:translateY(16px); transition:opacity .8s var(--ease), transform .8s var(--ease); }
        .rv-in{ opacity:1 !important; transform:none !important; }

        .brushed{ position:relative; }
        .brushed::before{ content:''; position:absolute; inset:auto 0 0 0; height:1px;
          background:linear-gradient(90deg, transparent, var(--gold) 30%, var(--copper) 70%, transparent); opacity:0.5; }

        /* NAV */
        .nav{ position:fixed; inset:0 0 auto 0; z-index:50; transition:all .3s var(--ease);
          background:rgba(13,11,8,0.6); backdrop-filter:blur(14px); border-bottom:1px solid transparent; }
        .nav.sc{ background:rgba(13,11,8,0.9); border-bottom-color:var(--hair2); }
        .nav-in{ max-width:1240px; margin:0 auto; padding:15px 36px; display:flex; align-items:center; justify-content:space-between; gap:20px; }
        @media(max-width:720px){ .nav-in{ padding:12px 20px; } }
        .brand{ display:flex; align-items:center; gap:12px; }
        .nav-links{ display:flex; gap:28px; align-items:center; }
        .nav-links a{ font-family:var(--mono); font-size:12.5px; color:var(--dim); transition:color .25s; white-space:nowrap; }
        .nav-links a:hover{ color:var(--gold); }
        .nav-acct{ font-family:var(--mono); font-size:12.5px; color:var(--dim); transition:color .25s; white-space:nowrap; }
        .nav-acct:hover{ color:var(--gold); }
        .nav-cta{ font-family:var(--mono); font-size:12.5px; padding:10px 20px; font-weight:500; border-radius:2px;
          background:linear-gradient(120deg, var(--gold-hi), var(--gold) 55%, var(--gold-dim)); color:#171208; border:none; transition:all .25s var(--ease); }
        .nav-cta:hover{ box-shadow:0 0 30px rgba(212,169,78,0.4); transform:translateY(-1px); }
        .burger{ display:none; background:none; border:1px solid var(--hair2); color:var(--dim); font-family:var(--mono); font-size:11px; padding:8px 12px; letter-spacing:0.1em; }
        @media(max-width:980px){ .nav-links{ display:none; } .nav-acct{ display:none; } .burger{ display:block; } }
        .mmenu{ border-top:1px solid var(--hair2); padding:18px 20px; display:flex; flex-direction:column; gap:16px; background:rgba(13,11,8,0.97); }
        .mmenu a{ font-family:var(--mono); font-size:13px; color:var(--dim); }

        /* HERO */
        .hero{ padding:150px 36px 60px; max-width:1600px; margin:0 auto; position:relative; z-index:0; }
        /* Real content lives in its own nested grid so the decorative
           .hero-field (absolutely positioned, but still a *grid item* by
           default) can never get auto-placed into a column/row and shove
           the text + instrument panel out of position — it did exactly that
           the first time this was tried: grid-template-rows silently became
           a 2-row grid instead of 1, and the reveal-on-scroll animation
           frontend for the text block never triggered because it landed
           far outside the initial viewport. */
        .hero-grid{ display:grid; grid-template-columns:1fr 1fr; gap:60px; align-items:center; position:relative; }
        @media(max-width:980px){ .hero-grid{ grid-template-columns:1fr; gap:40px; } }
        @media(max-width:980px){ .hero{ padding:125px 20px 40px; } }
        /* Full-bleed decorative field — breaks out of .hero's own max-width so the
           wide-viewport gutters get clusters/shards instead of sitting empty.
           Static, not animated (same reasoning as the dashboard background fix:
           filter:blur at this size is expensive per-frame; a one-time paint is fine). */
        .bg-field{ position:absolute; top:0; left:50%; width:100vw; height:100%;
          transform:translateX(-50%); z-index:-1; pointer-events:none; overflow:hidden; }
        /* Radial-gradient falloff, not solid-fill + blur(): a blurred solid
           disc still has a visible silhouette at these sizes (reads as a
           cheap "SaaS gradient blob" sticker) — a gradient that fades to
           transparent on its own has no edge to begin with, so it reads as
           actual ambient light instead of a shape someone dropped in. */
        .bg-field .cluster{ position:absolute; border-radius:50%; }
        .bg-field .shard{ position:absolute; opacity:0.4; }
        .hero-field{ min-height:900px; z-index:-2; }
        @media(max-width:980px){ .bg-field{ display:none; } }
        /* Static ambient glow so the glass panels below have something to refract —
           deliberately not animated: a hero mounts once per page view, not on every
           dashboard route, but a continuous filter:blur loop still isn't worth the
           GPU cost for a one-off decorative glow. */
        .hero::before{ content:''; position:absolute; z-index:-1; pointer-events:none;
          inset:-60px -8% auto -8%; height:640px;
          background:
            radial-gradient(ellipse 48% 62% at 18% 20%, rgba(222,178,85,0.22), transparent 65%),
            radial-gradient(ellipse 42% 54% at 88% 38%, rgba(192,138,107,0.14), transparent 65%),
            radial-gradient(ellipse 30% 40% at 55% 6%, rgba(248,231,184,0.10), transparent 70%);
          filter:blur(70px); }
        .tagline{ font-family:var(--mono); font-size:10.5px; letter-spacing:0.28em; text-transform:uppercase; color:var(--gold-hi);
          margin-bottom:28px; display:inline-flex; align-items:center; gap:12px; padding:9px 16px 9px 14px; border-radius:3px;
          border:1px solid transparent; background-origin:border-box; background-clip:padding-box, border-box;
          background-image:linear-gradient(rgba(23,19,16,0.88),rgba(23,19,16,0.88)), var(--metal);
          backdrop-filter:blur(12px) saturate(140%); -webkit-backdrop-filter:blur(12px) saturate(140%);
          box-shadow:inset 0 1px 0 rgba(255,255,255,0.06); }
        .tagline .dia{ width:7px; height:7px; background:var(--gold-hi); transform:rotate(45deg); box-shadow:0 0 10px rgba(248,231,184,0.8); flex-shrink:0; }
        .hero h1{ font-size:clamp(40px,5vw,68px); line-height:1.04; margin-bottom:22px; }
        .hero h1 .u{ position:relative; white-space:nowrap; }
        .hero h1 .u::after{ content:''; position:absolute; left:0; right:0; bottom:4px; height:2px;
          background:var(--metal); opacity:0.85; }
        .hero-sub{ color:var(--dim); font-size:16.5px; max-width:490px; margin-bottom:34px; }
        .hero-sub a{ color:var(--gold-hi); border-bottom:1px solid var(--hair); text-shadow:0 0 16px rgba(222,178,85,0.45); }
        .hero-ctas{ display:flex; gap:14px; flex-wrap:wrap; margin-bottom:18px; }
        .cta-solid{ position:relative; overflow:hidden; font-family:var(--mono); font-size:13px; padding:15px 28px; font-weight:600; border-radius:3px; border:none;
          background:var(--metal); background-size:220% 100%; background-position:0% 0%; color:#171208; transition:background-position .5s var(--ease), box-shadow .25s var(--ease), transform .25s var(--ease);
          display:inline-flex; align-items:center; gap:10px; box-shadow:0 10px 30px rgba(154,110,20,0.28), inset 0 1px 0 rgba(255,255,255,0.35); }
        .cta-solid:hover{ background-position:100% 0%; box-shadow:0 0 42px rgba(222,178,85,0.55), inset 0 1px 0 rgba(255,255,255,0.4); transform:translateY(-1px); }
        .cta-solid:disabled{ opacity:0.65; cursor:default; transform:none; }
        .cta-line{ position:relative; font-family:var(--mono); font-size:13px; color:var(--ink); padding:15px 28px; border-radius:3px;
          border:1px solid transparent; background-origin:border-box; background-clip:padding-box, border-box;
          background-image:linear-gradient(rgba(20,17,13,0.55),rgba(20,17,13,0.55)), linear-gradient(135deg, rgba(222,178,85,0.5), rgba(192,138,107,0.28) 60%, rgba(222,178,85,0.4));
          backdrop-filter:blur(16px) saturate(160%); -webkit-backdrop-filter:blur(16px) saturate(160%);
          box-shadow:inset 0 1px 0 rgba(255,255,255,0.07), 0 8px 24px rgba(0,0,0,0.25);
          transition:all .25s var(--ease); display:inline-flex; align-items:center; gap:10px; }
        .cta-line:hover{ color:var(--gold-hi); background-image:linear-gradient(rgba(20,17,13,0.6),rgba(20,17,13,0.6)), var(--metal); }
        .demo-line{ font-family:var(--mono); font-size:11.5px; color:var(--faint); margin-bottom:28px; display:flex; align-items:center; gap:8px; }
        .demo-line button{ background:none; border:none; padding:0; color:var(--gold); text-decoration:underline; text-underline-offset:3px; font-family:inherit; font-size:inherit; display:inline-flex; align-items:center; gap:6px; }
        .demo-line button:disabled{ color:var(--faint); cursor:default; }
        .senses{ display:flex; gap:10px; border-top:1px solid var(--hair2); padding-top:22px; flex-wrap:wrap; }
        .senses-label{ width:100%; font-family:var(--mono); font-size:9.5px; letter-spacing:0.18em; text-transform:uppercase; color:var(--faint); margin-bottom:6px; }
        .sense-chip{ font-family:var(--mono); font-size:11px; color:var(--dim); padding:7px 13px; border-radius:3px;
          background:rgba(237,232,221,0.03); backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
          border:1px solid var(--hair2); white-space:nowrap; }

        /* nerve panel — glass instrument bezel */
        .nerve{ border:1px solid transparent; background-origin:border-box; background-clip:padding-box, border-box;
          background-image:linear-gradient(160deg, rgba(23,19,16,0.82), rgba(30,25,19,0.68)),
            linear-gradient(155deg, rgba(222,178,85,0.55), rgba(138,100,32,0.2) 45%, rgba(222,178,85,0.4) 75%, rgba(248,231,184,0.5));
          backdrop-filter:blur(22px) saturate(150%); -webkit-backdrop-filter:blur(22px) saturate(150%);
          padding:20px; border-radius:6px; position:relative; overflow:hidden;
          box-shadow:inset 0 1px 0 rgba(255,255,255,0.06), 0 20px 60px rgba(0,0,0,0.4); }
        .nerve::before,.nerve::after{ content:''; position:absolute; width:16px; height:16px; border:1px solid rgba(222,178,85,0.4); pointer-events:none; z-index:2; }
        .nerve::before{ top:-1px; left:-1px; border-right:none; border-bottom:none; }
        .nerve::after{ bottom:-1px; right:-1px; border-left:none; border-top:none; }
        .nerve-sheen{ position:absolute; inset:0; pointer-events:none;
          background:linear-gradient(115deg, rgba(255,255,255,0.08) 0%, transparent 24%, transparent 76%, rgba(222,178,85,0.08) 100%); }
        .nerve-head{ display:flex; justify-content:space-between; margin-bottom:10px; flex-wrap:wrap; gap:8px; font-family:var(--mono); font-size:10.5px; letter-spacing:0.16em; text-transform:uppercase; color:var(--faint); }
        .nerve-head b{ color:var(--gold); font-weight:500; }
        .nerve-cv{ position:relative; aspect-ratio:1; }
        .nerve-cv svg{ filter:drop-shadow(0 6px 30px rgba(212,169,78,0.10)); }
        .comp-enter{ animation:compIn .6s var(--ease); transform-origin:200px 200px; }
        @keyframes compIn{ from{ opacity:0; transform:scale(0.96); } to{ opacity:1; transform:scale(1); } }
        .core-breathe{ animation:coreB 4s ease-in-out infinite; }
        @keyframes coreB{ 0%,100%{ opacity:0.75; } 50%{ opacity:1; } }
        .slice-tabs{ display:flex; gap:6px; margin:14px 0 13px; flex-wrap:wrap; }
        .slice-tab{ font-family:var(--mono); font-size:11px; padding:7px 12px; border:1px solid var(--hair2); background:transparent; color:var(--dim); transition:all .22s var(--ease); border-radius:2px; }
        .slice-tab:hover{ border-color:var(--copper); color:var(--copper); }
        .slice-tab.on{ background:rgba(192,138,107,0.1); border-color:var(--copper); color:var(--copper); }
        .nerve-read{ display:grid; grid-template-columns:1fr auto; gap:10px; align-items:end; }
        .nerve-note{ font-family:var(--mono); font-size:11.5px; color:var(--dim); line-height:1.7; }
        .nerve-note em{ font-style:normal; color:var(--yellow); }
        .health{ font-family:var(--mono); font-size:30px; line-height:1; text-align:right; }
        .health small{ display:block; font-size:9px; letter-spacing:0.16em; color:var(--faint); margin-top:5px; }

        /* METHOD */
        .method{ padding:130px 0; position:relative; z-index:0; }
        .m-grid{ display:grid; grid-template-columns:0.85fr 1.15fr; gap:70px; }
        @media(max-width:960px){ .m-grid{ grid-template-columns:1fr; gap:40px; } }
        .method h2{ font-size:clamp(28px,3.2vw,44px); margin-top:20px; line-height:1.12; }
        .method .lede{ color:var(--dim); margin-top:18px; max-width:380px; font-size:15px; }
        .sticky-l{ position:sticky; top:110px; align-self:start; }
        @media(max-width:960px){ .sticky-l{ position:static; } }
        .stage-row{ display:grid; grid-template-columns:60px 1fr; gap:24px; padding:32px 0; border-bottom:1px solid var(--hair2); }
        .stage-row .sn{ font-family:var(--mono); font-size:12px; color:var(--faint); padding-top:6px; transition:color .4s; }
        .stage-row .st{ font-family:var(--disp); font-weight:500; font-size:23px; margin-bottom:8px; color:var(--dim); transition:color .4s; }
        .stage-row .sd{ font-size:14.5px; color:var(--faint); max-width:480px; transition:color .4s; }
        .stage-row.on .sn{ color:var(--copper); }
        .stage-row.on .st{ color:var(--ink); }
        .stage-row.on .sd{ color:var(--dim); }
        .stage-bar{ width:100%; height:2px; background:var(--hair2); margin-top:26px; position:relative; overflow:hidden; }
        .stage-bar i{ position:absolute; inset:0 auto 0 0; background:linear-gradient(90deg, var(--gold), var(--copper)); transition:width .5s var(--ease); }

        /* MODULES */
        .mods{ padding:20px 0 120px; position:relative; z-index:0; }
        .mods-head{ display:flex; justify-content:space-between; align-items:end; margin-bottom:46px; gap:24px; flex-wrap:wrap; }
        .mods-head h2{ font-size:clamp(28px,3.2vw,44px); margin-top:20px; line-height:1.12; }
        .mods-head .side{ font-size:14px; color:var(--faint); max-width:300px; }
        .mods-head .side a{ color:var(--gold); }
        .mod-row{ display:grid; grid-template-columns:52px 1fr 300px; gap:26px; align-items:center; padding:24px 0; border-bottom:1px solid var(--hair2); cursor:pointer; transition:background .3s var(--ease); }
        @media(max-width:900px){ .mod-row{ grid-template-columns:42px 1fr; } .mod-row .mod-d{ display:none; } }
        .mod-row:hover{ background:rgba(212,169,78,0.035); }
        .mod-n{ font-family:var(--mono); font-size:12px; color:var(--faint); transition:color .3s; }
        .mod-row:hover .mod-n{ color:var(--copper); }
        .mod-name{ font-family:var(--disp); font-weight:500; font-size:clamp(19px,2vw,26px); color:var(--dim); transition:color .3s; display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
        .mod-row:hover .mod-name{ color:var(--ink); }
        .mod-tag{ font-family:var(--mono); font-size:9.5px; letter-spacing:0.14em; text-transform:uppercase; color:var(--copper); border:1px solid var(--hair-c); padding:3px 9px; border-radius:20px; }
        .mod-d{ font-size:13px; color:var(--faint); transition:all .3s var(--ease); opacity:0.55; transform:translateX(-6px); }
        .mod-row:hover .mod-d{ opacity:1; transform:none; color:var(--dim); }

        /* REPORT */
        .rep-sec{ padding:0 0 130px; position:relative; z-index:0; }
        .rep-grid{ display:grid; grid-template-columns:0.8fr 1.2fr; gap:64px; align-items:start; }
        @media(max-width:960px){ .rep-grid{ grid-template-columns:1fr; gap:40px; } }
        .rep-grid h2{ font-size:clamp(28px,3.2vw,44px); margin-top:20px; line-height:1.12; }
        .rep-grid .lede{ color:var(--dim); margin-top:18px; font-size:15px; }
        .rep-points{ margin-top:30px; display:flex; flex-direction:column; gap:16px; }
        .rep-point{ display:flex; gap:14px; font-size:14px; color:var(--dim); }
        .rep-point b{ font-family:var(--mono); font-size:11px; color:var(--copper); font-weight:500; padding-top:3px; letter-spacing:0.08em; }
        .report{ background:var(--surface); border:1px solid var(--hair); padding:44px 46px; border-radius:5px;
          box-shadow:0 60px 120px -50px rgba(212,169,78,0.16), 0 30px 80px rgba(0,0,0,0.55); position:relative; }
        .report::before{ content:''; position:absolute; inset:0 0 auto 0; height:2px;
          background:linear-gradient(90deg, var(--gold), var(--copper)); opacity:0.6; border-radius:5px 5px 0 0; }
        @media(max-width:720px){ .report{ padding:28px 22px; } }
        .rep-head{ display:flex; justify-content:space-between; border-bottom:1px solid var(--hair2); padding-bottom:20px; margin-bottom:26px; flex-wrap:wrap; gap:12px; }
        .rep-head h3{ font-size:24px; font-weight:600; }
        .rep-label{ font-family:var(--mono); font-size:9.5px; letter-spacing:0.2em; text-transform:uppercase; color:var(--faint); margin-bottom:9px; }
        .rep-meta{ font-family:var(--mono); font-size:10px; color:var(--faint); text-align:right; line-height:2; letter-spacing:0.06em; }
        .rep-body{ font-size:14.5px; color:var(--dim); }
        .rep-body strong{ color:var(--ink); font-weight:500; }
        .rep-block{ margin-bottom:24px; }
        .finding{ display:grid; grid-template-columns:12px 1fr auto; gap:13px; align-items:baseline; padding:12px 0; border-bottom:1px dashed var(--hair2); }
        .f-dot{ width:8px; height:8px; border-radius:50%; position:relative; top:1px; }
        .f-sev{ font-family:var(--mono); font-size:10px; letter-spacing:0.1em; }
        .rep-rx{ background:rgba(212,169,78,0.06); border-left:2px solid var(--gold); padding:16px 20px; font-size:14px; color:var(--ink); }
        .rep-sig{ display:flex; justify-content:space-between; align-items:center; margin-top:28px; padding-top:20px; border-top:1px solid var(--hair2); }
        .rep-sig .mono{ font-family:var(--mono); font-size:9.5px; color:var(--faint); letter-spacing:0.12em; }

        /* QUOTE */
        .quote{ border-top:1px solid var(--hair2); border-bottom:1px solid var(--hair2); background:var(--surface); padding:90px 0; }
        .quote blockquote{ font-family:var(--disp); font-weight:500; font-size:clamp(22px,2.8vw,34px); line-height:1.35; max-width:860px; letter-spacing:-0.01em; }
        .quote blockquote em{ font-style:normal; color:var(--gold); }
        .quote-by{ margin-top:26px; display:flex; gap:16px; align-items:center; }
        .quote-av{ width:42px; height:42px; border-radius:50%; background:linear-gradient(135deg, var(--copper), var(--surface2)); border:1px solid var(--hair-c); }
        .quote-by .n{ font-family:var(--mono); font-size:13px; color:var(--ink); }
        .quote-by .r{ font-family:var(--mono); font-size:11px; color:var(--faint); }

        /* FAQ */
        .faq{ padding:120px 0; position:relative; z-index:0; }
        .faq-grid{ display:grid; grid-template-columns:0.8fr 1.2fr; gap:64px; }
        @media(max-width:960px){ .faq-grid{ grid-template-columns:1fr; gap:36px; } }
        .faq h2{ font-size:clamp(28px,3.2vw,44px); margin-top:20px; line-height:1.12; }
        .faq-item{ border-bottom:1px solid var(--hair2); }
        .faq-q{ width:100%; background:none; border:none; text-align:left; padding:24px 0; display:flex; justify-content:space-between; align-items:center; gap:20px; color:var(--ink); font-family:var(--disp); font-weight:500; font-size:17px; transition:color .25s; }
        .faq-q:hover{ color:var(--gold); }
        .faq-q .pm{ font-family:var(--mono); color:var(--copper); font-size:16px; flex-shrink:0; }
        .faq-a{ overflow:hidden; transition:max-height .45s var(--ease), opacity .45s var(--ease); max-height:0; opacity:0; }
        .faq-a.open{ max-height:220px; opacity:1; }
        .faq-a p{ padding:0 0 24px; color:var(--dim); font-size:14.5px; max-width:560px; }

        /* CTA */
        .final{ padding:140px 0; text-align:center; position:relative; z-index:0; overflow:hidden; }
        .final .halo{ position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:640px; height:640px;
          background:radial-gradient(circle, rgba(212,169,78,0.09), transparent 65%); pointer-events:none; }
        .final h2{ font-size:clamp(30px,4.2vw,54px); max-width:760px; margin:26px auto 18px; line-height:1.08; }
        .final p{ color:var(--dim); max-width:440px; margin:0 auto 36px; }

        /* FOOTER */
        .foot{ border-top:1px solid var(--hair2); padding:64px 0 40px; background:var(--surface); }
        .foot-grid{ display:grid; grid-template-columns:1.5fr repeat(3,1fr); gap:44px; padding-bottom:46px; border-bottom:1px solid var(--hair2); margin-bottom:28px; }
        @media(max-width:760px){ .foot-grid{ grid-template-columns:1fr 1fr; } }
        .foot-brand p{ color:var(--faint); font-size:13px; max-width:260px; margin-top:16px; }
        .foot-tag{ font-family:var(--mono); font-size:9.5px; letter-spacing:0.24em; text-transform:uppercase; color:var(--copper); margin-top:10px; }
        .foot-col h4{ font-family:var(--mono); font-size:10.5px; text-transform:uppercase; letter-spacing:0.16em; color:var(--faint); margin-bottom:16px; font-weight:400; }
        .foot-col a{ display:block; font-size:13.5px; color:var(--dim); margin-bottom:11px; transition:color .25s; }
        .foot-col a:hover{ color:var(--gold); }
        .foot-btm{ display:flex; justify-content:space-between; font-family:var(--mono); font-size:10.5px; color:var(--faint); flex-wrap:wrap; gap:12px; letter-spacing:0.06em; }

        @media (prefers-reduced-motion: reduce){
          .an-root *{ animation-duration:0.001ms !important; transition-duration:0.001ms !important; }
        }
      `}</style>

      {/* NAV */}
      <header className={`nav ${scrolled ? "sc" : ""}`}>
        <div className="nav-in">
          <Link href="/" className="brand"><AionMark size={30} /><Wordmark h={18} /></Link>
          <nav className="nav-links">
            {NAV_ITEMS.map((l) => <a key={l.href} href={l.href}>{l.label}</a>)}
          </nav>
          <div style={{ display: "flex", gap: 18, alignItems: "center" }}>
            <Link href="/dashboard" className="nav-acct">Dashboard</Link>
            <Link href="/login" className="nav-acct">Sign in</Link>
            <Link href="/register"><button className="nav-cta">Book a scan</button></Link>
            <button className="burger" onClick={() => setMenuOpen(!menuOpen)} aria-expanded={menuOpen} aria-label="Toggle menu">MENU</button>
          </div>
        </div>
        {menuOpen && (
          <div className="mmenu">
            {NAV_ITEMS.map((l) => (
              <a key={l.href} href={l.href} onClick={() => setMenuOpen(false)}>{l.label}</a>
            ))}
            <Link href="/dashboard" onClick={() => setMenuOpen(false)}>Dashboard</Link>
            <Link href="/login" onClick={() => setMenuOpen(false)}>Sign in</Link>
          </div>
        )}
      </header>

      {/* HERO */}
      <section className="hero">
        <div className="bg-field hero-field" aria-hidden="true">
          <div className="cluster" style={{ left: "-12%", top: "8%", width: "30vw", height: "30vw", background: "radial-gradient(circle, rgba(222,178,85,0.55) 0%, rgba(222,178,85,0.18) 45%, rgba(222,178,85,0) 72%)" }} />
          <div className="cluster" style={{ right: "-14%", top: "22%", width: "26vw", height: "26vw", background: "radial-gradient(circle, rgba(192,138,107,0.5) 0%, rgba(192,138,107,0.16) 45%, rgba(192,138,107,0) 72%)" }} />
          <div className="cluster" style={{ left: "-4%", bottom: "4%", width: "20vw", height: "20vw", background: "radial-gradient(circle, rgba(248,231,184,0.42) 0%, rgba(248,231,184,0.12) 45%, rgba(248,231,184,0) 72%)" }} />
          <div className="cluster" style={{ right: "-2%", bottom: "0%", width: "18vw", height: "18vw", background: "radial-gradient(circle, rgba(222,178,85,0.45) 0%, rgba(222,178,85,0.14) 45%, rgba(222,178,85,0) 72%)" }} />
          {[
            { top: "14%", left: "4%", size: 14, rotate: 12, color: "#DEB255" },
            { top: "34%", left: "1.5%", size: 10, rotate: -25, color: "#F3D488" },
            { top: "62%", left: "6%", size: 12, rotate: 40, color: "#C08A6B" },
            { top: "82%", left: "3%", size: 9, rotate: -10, color: "#DEB255" },
            { top: "10%", right: "3%", size: 11, rotate: 20, color: "#F3D488" },
            { top: "40%", right: "1.5%", size: 15, rotate: -35, color: "#DEB255" },
            { top: "68%", right: "5%", size: 10, rotate: 8, color: "#C08A6B" },
            { top: "88%", right: "2%", size: 12, rotate: -18, color: "#F3D488" },
          ].map((s, i) => (
            <svg key={i} className="shard" viewBox="0 0 10 10"
              style={{ top: s.top, left: s.left, right: s.right, width: s.size, height: s.size, transform: `rotate(${s.rotate}deg)` }}>
              <polygon points="5,0 10,10 0,10" fill={s.color} />
            </svg>
          ))}
        </div>
        <div className="hero-grid">
        <div data-rv>
          <div className="tagline"><span className="dia" />The AI Nervous System for the Enterprise</div>
          <h1>Organizations don't have a nervous system. <span className="u g">We built them one.</span></h1>
          <p className="hero-sub">
            A body registers damage in milliseconds. An organization takes months — the bottleneck no one named,
            the quiet resignation, the succession gap everyone saw coming. AION maps your company as a living
            knowledge graph, reads its health the way a lab reads bloodwork, and tells you{" "}
            <a href="#report">precisely where it's failing</a> while there's still time to intervene.
          </p>
          <div className="hero-ctas">
            <Link href="/register"><button className="cta-solid">Start a diagnostic scan</button></Link>
            <a href="#report"><button className="cta-line">See how it reads an org</button></a>
          </div>
          <p className="demo-line">
            No signup required —{" "}
            <button onClick={() => runDemo.mutate()} disabled={runDemo.isPending}>
              {runDemo.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <PlayCircle className="h-3 w-3" />}
              {runDemo.isPending ? "loading demo…" : "run a live diagnostic scan now"}
            </button>
          </p>
          <div className="senses">
            <div className="senses-label">Continuously sensing for</div>
            <span className="sense-chip">Knowledge Cancer</span>
            <span className="sense-chip">Memory Decay</span>
            <span className="sense-chip">Communication Stroke</span>
            <span className="sense-chip">Bus-Factor Risk</span>
            <span className="sense-chip">Succession Gaps</span>
          </div>
        </div>

        {/* SIGNATURE: the Instrument — chronometer orrery */}
        <div className="nerve" data-rv>
          <div className="nerve-sheen" />
          <div className="nerve-head">
            <span><b>The Instrument</b> · sample reading</span>
            <span>{slice.id} / {SLICES.length}</span>
          </div>
          <div className="nerve-cv"><Instrument slice={slice} /></div>
          <div className="slice-tabs" role="tablist" aria-label="Department pathways">
            {SLICES.map((s) => (
              <button key={s.id} role="tab" aria-selected={slice.id === s.id}
                className={`slice-tab ${slice.id === s.id ? "on" : ""}`}
                onClick={() => setSlice(s)}>
                {s.id} · {s.name}
              </button>
            ))}
          </div>
          <div className="nerve-read">
            <div className="nerve-note">
              {slice.nodes} pathways · {slice.findings} risk signal{slice.findings !== 1 ? "s" : ""}<br />
              <em>{slice.note}</em>
            </div>
            <div className="health" style={{ color: healthColor(slice.health), textShadow: `0 0 18px ${healthColor(slice.health)}88` }}>
              {slice.health}<small>Health index</small>
            </div>
          </div>
        </div>
        </div>
      </section>

      {/* METHOD */}
      <section className="method" id="method">
        <SectionField variant={0} />
        <div className="wrap m-grid">
          <div className="sticky-l" data-rv>
            <div className="eyebrow">The method</div>
            <h2>Six reflexes, from raw records to <span className="g">response.</span></h2>
            <p className="lede">No surveys, no consultants embedded for six months. AION senses structure, continuously — like a body does.</p>
            <div className="stage-bar"><i style={{ width: `${((stage + 1) / STAGES.length) * 100}%` }} /></div>
          </div>
          <div ref={stagesRef}>
            {STAGES.map((s, i) => (
              <div key={s.n} className={`stage-row ${i <= stage ? "on" : ""}`}>
                <span className="sn">{s.n} —</span>
                <div>
                  <div className="st">{s.t}</div>
                  <p className="sd">{s.d}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* MODULES */}
      <section className="mods" id="platform">
        <SectionField variant={1} />
        <div className="wrap">
          <div className="mods-head" data-rv>
            <div>
              <div className="eyebrow">The platform</div>
              <h2>Eight instruments. One nervous system.</h2>
            </div>
            <p className="side">Every instrument reads the same pathways — a signal in one traces to its cause in another. <Link href="/dashboard">Explore the platform →</Link></p>
          </div>
          <div style={{ borderTop: "1px solid var(--hair2)" }}>
            {MODULES.map((m) => (
              <Link key={m.n} href={m.href} className="mod-row" data-rv>
                <span className="mod-n">{m.n}</span>
                <span className="mod-name">{m.name} <span className="mod-tag">{m.tag}</span></span>
                <span className="mod-d">{m.d}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* REPORT */}
      <section className="rep-sec" id="report">
        <SectionField variant={2} />
        <div className="wrap rep-grid">
          <div data-rv>
            <div className="eyebrow">The deliverable</div>
            <h2>What lands on the board table Monday, <span className="g">06:00.</span></h2>
            <p className="lede">Not a dashboard to interpret. A reading with findings, severity, and one recommended response.</p>
            <div className="rep-points">
              <div className="rep-point"><b>AUTO</b><span>Generated every Monday from the live pathways — no analyst hours.</span></div>
              <div className="rep-point"><b>RANKED</b><span>Findings ordered by severity and reversibility, not by volume.</span></div>
              <div className="rep-point"><b>ACTIONABLE</b><span>Each critical finding ships with a simulated intervention and its predicted outcome.</span></div>
            </div>
          </div>

          <div className="report" data-rv>
            <div className="rep-head">
              <div>
                <div className="rep-label">Organizational diagnostic report — illustrative sample</div>
                <h3>Acme Industries — Q3 reading</h3>
              </div>
              <div className="rep-meta">REF AION-2026-0713<br />184 PATHWAYS · 12 SOURCES<br />CONFIDENCE 0.94</div>
            </div>
            <div className="rep-block">
              <div className="rep-label">Impression</div>
              <p className="rep-body">Structurally sound with <strong>three findings requiring intervention this quarter</strong>. Health index 68/100, down 4 points, driven by decision latency in Sales-West and unmitigated succession exposure at director level.</p>
            </div>
            <div className="rep-block">
              <div className="rep-label">Findings</div>
              <div className="finding">
                <span className="f-dot" style={{ background: "#C4564A" }} />
                <span className="rep-body"><strong>Single point of failure — VP Operations.</strong> 31% of cross-team decisions route through one person. No identified successor.</span>
                <span className="f-sev" style={{ color: "#C4564A" }}>CRITICAL</span>
              </div>
              <div className="finding">
                <span className="f-dot" style={{ background: "#D9B25C" }} />
                <span className="rep-body"><strong>Attrition precursor — Sales-West.</strong> Engagement decay matches the pattern preceding three prior regrettable exits.</span>
                <span className="f-sev" style={{ color: "#D9B25C" }}>ELEVATED</span>
              </div>
              <div className="finding" style={{ borderBottom: "none" }}>
                <span className="f-dot" style={{ background: "#D9B25C" }} />
                <span className="rep-body"><strong>Decision bottleneck — product sign-off.</strong> Median approval latency +2.4 days quarter over quarter.</span>
                <span className="f-sev" style={{ color: "#D9B25C" }}>ELEVATED</span>
              </div>
            </div>
            <div className="rep-block">
              <div className="rep-label">Recommended response</div>
              <div className="rep-rx">Nominate and shadow a successor for VP Operations within 30 days; simulation predicts exposure drops from <strong style={{ color: "#C4564A" }}>critical</strong> to <strong style={{ color: "#5FA872" }}>managed</strong> with a single staffing move.</div>
            </div>
            <div className="rep-sig">
              <span style={{ display: "flex", alignItems: "center", gap: 10 }}><AionMark size={22} /><Wordmark h={13} /></span>
              <span className="mono">SAMPLE REPORT · SEE YOUR OWN VIA THE LIVE SCAN ABOVE</span>
            </div>
          </div>
        </div>
      </section>

      {/* QUOTE */}
      <section className="quote">
        <div className="wrap" data-rv>
          <blockquote>
            "We'd have found the Operations gap eventually — in the exit interview. AION felt it
            <em> six weeks earlier</em>, with the fix attached."
          </blockquote>
          <div className="quote-by">
            <span className="quote-av" />
            <div>
              <div className="n">Board member</div>
              <div className="r">Industrial group · 1,400 employees</div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="faq" id="faq">
        <SectionField variant={0} />
        <div className="wrap faq-grid">
          <div data-rv>
            <div className="eyebrow">Questions</div>
            <h2>The ones every board asks <span className="g">first.</span></h2>
          </div>
          <div data-rv>
            {FAQS.map((f, i) => (
              <div key={i} className="faq-item">
                <button className="faq-q" onClick={() => setOpenFaq(openFaq === i ? -1 : i)} aria-expanded={openFaq === i}>
                  {f.q}<span className="pm">{openFaq === i ? "−" : "+"}</span>
                </button>
                <div className={`faq-a ${openFaq === i ? "open" : ""}`}><p>{f.a}</p></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="final">
        <SectionField variant={1} />
        <div className="halo" />
        <div className="wrap" style={{ position: "relative" }}>
          <div data-rv style={{ display: "flex", justifyContent: "center" }}><AionMark size={52} /></div>
          <h2 data-rv>Your organization is sending signals. Connect the <span className="g">nervous system.</span></h2>
          <p data-rv>First diagnostic reading on a live workspace is on us. One week from intake to report.</p>
          <div data-rv style={{ display: "flex", gap: 14, justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/register"><button className="cta-solid">Book a diagnostic scan</button></Link>
            <a href="mailto:hello@aion.ai"><button className="cta-line">Talk to us</button></a>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="foot">
        <div className="wrap">
          <div className="foot-grid">
            <div className="foot-brand">
              <span style={{ display: "flex", alignItems: "center", gap: 12 }}><AionMark size={34} /><Wordmark h={17} /></span>
              <p>Organizational intelligence for boards and executive teams who&apos;d rather know now.</p>
              <div className="foot-tag">Artificial Intelligence · Organizational Nervous System</div>
            </div>
            <div className="foot-col">
              <h4>Platform</h4>
              <Link href="/dashboard/graph">Knowledge Graph</Link>
              <Link href="/dashboard/mri">Org MRI</Link>
              <Link href="/dashboard/diseases">Diseases</Link>
              <Link href="/dashboard/decay">Decay</Link>
              <Link href="/dashboard/simulation">Simulation</Link>
              <Link href="/dashboard/ocsie">OCSIE</Link>
            </div>
            <div className="foot-col">
              <h4>Account</h4>
              <Link href="/dashboard">Dashboard</Link>
              <Link href="/login">Sign in</Link>
              <Link href="/register">Request access</Link>
            </div>
            <div className="foot-col">
              <h4>Company</h4>
              <a href="#method">Methodology</a>
              <a href="#report">Sample report</a>
              <a href="mailto:hello@aion.ai">Contact</a>
            </div>
          </div>
          <div className="foot-btm">
            <span>© 2026 AION INTELLIGENCE, INC.</span>
            <span>BUILT FOR BOARDS THAT ACT EARLY</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
