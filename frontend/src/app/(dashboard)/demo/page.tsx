"use client";
import { useEffect, useRef } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import {
  Bot, Brain, Building2, Bug, Clock, Dna, GitBranch, Loader2, PlayCircle,
  Sparkles, TrendingUp, Users,
} from "lucide-react";
import { useIntelligenceIndex } from "@/lib/hooks/use-intelligence";
import { useDiseaseScan } from "@/lib/hooks/use-diseases";
import { useDecayReport, useDecayEntropy } from "@/lib/hooks/use-decay";
import { useDepartments } from "@/lib/hooks/use-graph";
import { useBoardBriefing, useAdvisorChat } from "@/lib/hooks/use-board";
import { graphApi } from "@/lib/api";
import { GraphNode, OIISnapshot, DiseaseResult, DiseaseType } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { OIIHealthGauge } from "@/components/dashboard/oii-health-gauge";
import { cn } from "@/lib/utils/cn";

const DISEASE_LABELS: Record<DiseaseType, string> = {
  knowledge_cancer: "Knowledge Cancer",
  memory_alzheimers: "Memory Alzheimer's",
  communication_stroke: "Communication Stroke",
  knowledge_obesity: "Knowledge Obesity",
  innovation_paralysis: "Innovation Paralysis",
};

const EXPLORE_LINKS = [
  { label: "Intelligence Index", href: "/dashboard/intelligence", icon: Brain, tint: "accent" },
  { label: "Org MRI", href: "/dashboard/mri", icon: Brain, tint: "violet" },
  { label: "Disease Panel", href: "/dashboard/diseases", icon: Bug, tint: "rose" },
  { label: "Decay Engine", href: "/dashboard/decay", icon: Clock, tint: "warning" },
  { label: "OCSIE Succession", href: "/dashboard/ocsie", icon: Dna, tint: "rose" },
  { label: "Board Advisor", href: "/dashboard/board", icon: TrendingUp, tint: "accent" },
  { label: "Memory Graph", href: "/dashboard/graph", icon: GitBranch, tint: "teal" },
  { label: "Ask Axon", href: "/dashboard/advisor", icon: Bot, tint: "insight" },
] as const;

const EXPLORE_TINT: Record<string, { icon: string; hoverBorder: string; hoverBg: string }> = {
  accent: { icon: "text-aion-accent", hoverBorder: "hover:border-aion-accent-border", hoverBg: "hover:bg-aion-accent-tint" },
  violet: { icon: "text-aion-violet", hoverBorder: "hover:border-aion-violet-border", hoverBg: "hover:bg-aion-violet-tint" },
  teal: { icon: "text-aion-teal", hoverBorder: "hover:border-aion-teal-border", hoverBg: "hover:bg-aion-teal-tint" },
  rose: { icon: "text-aion-rose", hoverBorder: "hover:border-aion-rose-border", hoverBg: "hover:bg-aion-rose-tint" },
  insight: { icon: "text-aion-insight", hoverBorder: "hover:border-aion-insight", hoverBg: "hover:bg-aion-insight-tint" },
  warning: { icon: "text-health-yellow", hoverBorder: "hover:border-health-yellow-border", hoverBg: "hover:bg-health-yellow-tint" },
};

const DEMO_PROMPT =
  "Give me a complete executive analysis of this company right now: overall health, " +
  "the biggest risks, what's decaying, and your top 3 recommendations. Be specific with numbers.";

function renderLiteMarkdown(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="font-semibold text-aion-ink">{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
}

function MetricTile({ icon: Icon, label, value }: { icon: any; label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-aion-border bg-aion-surface2 px-3 py-2.5">
      <div className="flex items-center gap-1.5 text-2xs text-aion-ink-faint uppercase tracking-wider">
        <Icon className="h-3 w-3" /> {label}
      </div>
      <p className="mt-1 text-2xl font-bold text-aion-ink tabular-nums">{value}</p>
    </div>
  );
}

function SectionCard({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-aion-accent" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export default function LiveDemoPage() {
  const { data: oiiData, isLoading: oiiLoading } = useIntelligenceIndex();
  const oii = oiiData as OIISnapshot | undefined;
  const { data: diseaseData, isLoading: diseaseLoading } = useDiseaseScan();
  const { data: decayReport, isLoading: decayLoading } = useDecayReport();
  const { data: entropy } = useDecayEntropy();
  const { data: deptData, isLoading: deptLoading } = useDepartments();
  const { data: briefing, isLoading: briefingLoading } = useBoardBriefing();

  const { data: peopleData } = useQuery({
    queryKey: ["graph", "nodes", "Person", "demo"],
    queryFn: () => graphApi.getNodes({ node_type: "Person", limit: 100 }),
    staleTime: 5 * 60 * 1000,
  });
  const topRisk: GraphNode[] = (peopleData?.nodes ?? [])
    .slice()
    .sort((a, b) => (a.health_score ?? 1) - (b.health_score ?? 1))
    .slice(0, 3);

  const advisorChat = useAdvisorChat();
  const askedRef = useRef(false);
  useEffect(() => {
    if (askedRef.current) return;
    askedRef.current = true;
    setTimeout(() => {
      advisorChat.mutate({ message: DEMO_PROMPT, history: [] });
    }, 300);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalPeople = deptData?.departments.reduce((sum, d) => sum + d.headcount, 0) ?? 0;
  const totalPolicies = deptData?.departments.reduce((sum, d) => sum + d.policy_count, 0) ?? 0;

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <Badge variant="default">
              <PlayCircle className="h-3 w-3" /> LIVE DEMO
            </Badge>
            <span className="text-xs text-aion-ink-faint">Real seeded company · Nova Robotics</span>
          </div>
          <h1 className="page-title flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-aion-accent" />
            Complete Company Analysis
          </h1>
          <p className="page-subtitle mt-1">
            Every module, running on real data, with Axon&apos;s own analysis below — exactly what AION shows a live customer, in one place.
          </p>
        </div>
      </motion.div>

      {/* Executive Snapshot */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
        {/* Glow moment 1 of 2: this is the first number a prospect sees on the whole demo. */}
        <Card className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 h-1 bg-brand-gradient" />
          <CardContent className="flex flex-wrap items-center gap-8 p-6">
            {oiiLoading ? (
              <Skeleton className="h-32 w-32 rounded-full" />
            ) : oii ? (
              <div className="rounded-full shadow-glow-accent"><OIIHealthGauge value={oii.overall_health} size="lg" /></div>
            ) : null}
            <div className="grid flex-1 grid-cols-2 gap-3 sm:grid-cols-4">
              <MetricTile icon={Building2} label="Departments" value={deptData?.departments.length ?? "—"} />
              <MetricTile icon={Users} label="People" value={totalPeople || "—"} />
              <MetricTile icon={Sparkles} label="Policies" value={totalPolicies || "—"} />
              <MetricTile icon={Bug} label="Critical Diseases" value={diseaseData?.critical_diseases ?? "—"} />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Axon's live analysis — the reason this page exists, so it leads, not trails.
          Glow moment 2 of 2: Axon's own generated words, the AI feature earning the full gradient. */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }} className="relative -mx-6 overflow-hidden bg-aion-insight-tint px-6 py-8 sm:-mx-8 sm:px-8">
        <div className="absolute inset-x-0 top-0 h-[2px] bg-brand-gradient" />
        <div className="mb-3 flex items-center gap-2">
          <Bot className="h-5 w-5 text-aion-insight" />
          <p className="text-xs font-semibold uppercase tracking-wide text-aion-insight">Axon&apos;s live analysis</p>
        </div>
        {advisorChat.isPending ? (
          <div className="flex items-center gap-2 text-sm text-aion-ink-muted">
            <Loader2 className="h-4 w-4 animate-spin" /> Axon is analyzing the organization…
          </div>
        ) : advisorChat.data ? (
          <p className="max-w-3xl whitespace-pre-wrap text-lg leading-relaxed text-aion-ink" style={{ fontFamily: "var(--font-head, ui-serif, Georgia, serif)" }}>
            {renderLiteMarkdown(advisorChat.data.answer)}
          </p>
        ) : (
          <p className="text-sm text-aion-ink-muted">Analysis unavailable right now.</p>
        )}
        <Link href="/dashboard/advisor" className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-aion-insight hover:opacity-80">
          Continue the conversation with Axon &rarr;
        </Link>
      </motion.div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* Disease scan */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <SectionCard title="Disease Detection" icon={Bug}>
            {diseaseLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : diseaseData ? (
              <div className="space-y-2">
                {(Object.entries(diseaseData.diseases) as [DiseaseType, DiseaseResult][]).map(([type, d]) => (
                  <div key={type} className="flex items-center justify-between rounded-lg border border-aion-border bg-aion-surface2 px-3 py-2">
                    <span className="text-xs text-aion-ink">{DISEASE_LABELS[type]}</span>
                    <Badge variant={d.severity === "critical" ? "danger" : d.severity === "warning" ? "warning" : "success"}>
                      {d.severity} · {d.severity_score}%
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 py-6 text-center">
                <Bug className="h-5 w-5 text-aion-ink-faint" />
                <p className="text-sm text-aion-ink-muted">No scan data yet</p>
              </div>
            )}
          </SectionCard>
        </motion.div>

        {/* Decay */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <SectionCard title="Knowledge Decay" icon={Clock}>
            {decayLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : (
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-aion-border bg-aion-surface2 px-3 py-2.5">
                  <p className="text-2xs text-aion-ink-faint uppercase tracking-wider">Isolated Items</p>
                  <p className="text-xl font-bold text-aion-ink tabular-nums mt-1">{decayReport?.summary.isolated_items ?? "—"}</p>
                </div>
                <div className="rounded-lg border border-aion-border bg-aion-surface2 px-3 py-2.5">
                  <p className="text-2xs text-aion-ink-faint uppercase tracking-wider">Single-Owner Critical</p>
                  <p className="text-xl font-bold text-health-yellow tabular-nums mt-1">{decayReport?.summary.single_owner_critical ?? "—"}</p>
                </div>
                <div className="rounded-lg border border-aion-border bg-aion-surface2 px-3 py-2.5">
                  <p className="text-2xs text-aion-ink-faint uppercase tracking-wider">Entropy Score</p>
                  <p className="text-xl font-bold text-aion-ink tabular-nums mt-1">
                    {entropy ? (entropy.composite_entropy_score * 100).toFixed(0) + "%" : "—"}
                  </p>
                </div>
                <div className="rounded-lg border border-aion-border bg-aion-surface2 px-3 py-2.5">
                  <p className="text-2xs text-aion-ink-faint uppercase tracking-wider">Isolation Ratio</p>
                  <p className="text-xl font-bold text-aion-ink tabular-nums mt-1">
                    {entropy ? (entropy.isolation_ratio * 100).toFixed(1) + "%" : "—"}
                  </p>
                </div>
              </div>
            )}
          </SectionCard>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* Succession risk */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <SectionCard title="Highest Succession Risk" icon={Dna}>
            <div className="space-y-2">
              {topRisk.length ? topRisk.map((p) => (
                <Link key={p.id} href={`/dashboard/ocsie/${p.id}`}>
                  <div className="flex items-center justify-between rounded-lg border border-aion-border bg-aion-surface2 px-3 py-2 transition-colors duration-150 hover:border-aion-accent-border cursor-pointer">
                    <div>
                      <p className="text-sm text-aion-ink font-medium">{p.label}</p>
                      <p className="text-2xs text-aion-ink-faint">{p.tooltip}</p>
                    </div>
                    <Badge variant={p.health_color === "red" ? "danger" : p.health_color === "yellow" ? "warning" : "success"}>
                      {Math.round((1 - (p.health_score ?? 0.5)) * 100)}% risk
                    </Badge>
                  </div>
                </Link>
              )) : (
                <p className="text-sm text-aion-ink-muted">No people data</p>
              )}
            </div>
          </SectionCard>
        </motion.div>

        {/* Departments */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
          <SectionCard title="Departments" icon={Building2}>
            {deptLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : (
              <div className="max-h-48 space-y-1.5 overflow-y-auto no-scrollbar">
                {deptData?.departments.map((d) => (
                  <div key={d.id} className="flex items-center justify-between rounded-lg border border-aion-border bg-aion-surface2 px-3 py-2">
                    <span className="text-xs text-aion-ink">{d.name}</span>
                    <span className="text-2xs text-aion-ink-faint">
                      {d.headcount} people · {d.knowledge_items} knowledge · {d.policy_count} policies
                    </span>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </motion.div>
      </div>

      {/* Board Briefing */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
        <SectionCard title="Board Advisor Executive Briefing" icon={TrendingUp}>
          {briefingLoading ? (
            <Skeleton className="h-16 w-full" />
          ) : (
            <p className="text-sm text-aion-ink-muted leading-relaxed">{briefing?.executive_summary}</p>
          )}
        </SectionCard>
      </motion.div>

      {/* Explore live dashboards */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
        <Card>
          <CardHeader>
            <CardTitle>Explore Every Live Dashboard</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {EXPLORE_LINKS.map((l) => {
                const t = EXPLORE_TINT[l.tint];
                return (
                  <Link key={l.href} href={l.href}>
                    <div className={cn(
                      "flex flex-col items-center gap-2 rounded-lg border border-aion-border bg-aion-surface2 px-4 py-5 text-center",
                      "transition-colors duration-150 cursor-pointer", t.hoverBorder, t.hoverBg,
                    )}>
                      <l.icon className={cn("h-5 w-5", t.icon)} />
                      <span className="text-xs font-medium text-aion-ink">{l.label}</span>
                    </div>
                  </Link>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
