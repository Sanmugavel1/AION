"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import { BarChart3, Shield, TrendingUp, AlertCircle, ChevronDown, AlertOctagon, AlertTriangle, Info, Quote } from "lucide-react";
import { useBoardBriefing, useBoardRisks, useBoardOpportunities } from "@/lib/hooks/use-board";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import { formatRelativeTime } from "@/lib/utils/format";
import { OIIHealthGauge } from "@/components/dashboard/oii-health-gauge";

function CountUp({ value, decimals = 0 }: { value: number; decimals?: number }) {
  const [display, setDisplay] = useState(0);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    let raf: number;
    const duration = 700;
    const step = (ts: number) => {
      if (startRef.current === null) startRef.current = ts;
      const progress = Math.min(1, (ts - startRef.current) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(value * eased);
      if (progress < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [value]);

  return <>{display.toFixed(decimals)}</>;
}

const RISK_ICON = { critical: AlertOctagon, high: AlertTriangle, medium: AlertCircle, low: Info } as const;

function RiskCard({ risk, i }: { risk: any; i: number }) {
  const [open, setOpen] = useState(false);
  const sv = (risk.severity ?? risk.impact_level ?? "low") as keyof typeof RISK_ICON;
  const severityConfig = {
    critical: "border-l-health-red bg-health-red-tint",
    high: "border-l-health-red/60 bg-health-red-tint/60",
    medium: "border-l-health-yellow bg-health-yellow-tint",
    low: "border-l-aion-border-strong bg-aion-surface2",
  }[sv] ?? "border-l-aion-border-strong bg-aion-surface2";
  const iconColor = {
    critical: "text-health-red", high: "text-health-red", medium: "text-health-yellow", low: "text-aion-ink-faint",
  }[sv] ?? "text-aion-ink-faint";
  const RiskIcon = RISK_ICON[sv] ?? Info;

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
      <div className={cn("rounded-lg border border-l-4 border-aion-border px-4 py-3 cursor-pointer transition-colors duration-150", severityConfig)}
        onClick={() => setOpen((o) => !o)}>
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-2.5 flex-1 min-w-0">
            <RiskIcon className={cn("h-4 w-4 mt-0.5 shrink-0", iconColor)} aria-hidden="true" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-aion-ink">{risk.title}</p>
              <p className="text-xs text-aion-ink-muted mt-0.5 line-clamp-1">{risk.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 ml-3 shrink-0">
            <Badge variant={sv === "critical" ? "critical" : sv === "high" ? "danger" : sv === "medium" ? "warning" : "secondary"}>
              {sv}
            </Badge>
            <ChevronDown className={cn("h-4 w-4 text-aion-ink-faint transition-transform", open && "rotate-180")} />
          </div>
        </div>
        <AnimatePresence>
          {open && risk.mitigation_strategy && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}>
              <div className="mt-3 border-t border-aion-border pt-3">
                <p className="text-2xs font-medium text-aion-ink-faint uppercase tracking-wider mb-1">Mitigation Strategy</p>
                <p className="text-xs text-aion-ink leading-relaxed">{risk.mitigation_strategy}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

function OpportunityCard({ opp, i }: { opp: any; i: number }) {
  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
      <div className="rounded-lg border border-l-4 border-aion-border border-l-health-green bg-health-green-tint px-4 py-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-2.5 flex-1 min-w-0">
            <TrendingUp className="h-4 w-4 mt-0.5 shrink-0 text-health-green" aria-hidden="true" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-aion-ink">{opp.title}</p>
              <p className="text-xs text-aion-ink-muted mt-0.5">{opp.description}</p>
            </div>
          </div>
          <Badge variant="success" className="ml-3 shrink-0">{opp.potential_value ?? "High Value"}</Badge>
        </div>
      </div>
    </motion.div>
  );
}

export default function BoardPage() {
  const { data: briefing, isLoading } = useBoardBriefing();
  const { data: risks } = useBoardRisks();
  const { data: opportunities } = useBoardOpportunities();

  const kpiEntries = briefing?.key_metrics
    ? Object.entries(briefing.key_metrics).filter(([k]) => k !== "overall_oii_score" && k !== "health_score").slice(0, 4)
    : [];

  return (
    <div className="space-y-10">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-aion-accent" />
            Board Advisor Intelligence
          </h1>
          <p className="page-subtitle mt-1">Executive-level organizational intelligence briefing, written by Axon for strategic decision making</p>
        </div>
        {briefing?.briefing_date && (
          <span className="text-xs text-aion-ink-faint shrink-0">Generated {formatRelativeTime(briefing.briefing_date)}</span>
        )}
      </motion.div>

      {/* Executive Summary — pull-quote, no card chrome. This is Axon's own words.
          Glow moment 1 of 2: the one place the full brand gradient appears on this page. */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }} className="relative -mx-6 overflow-hidden bg-aion-insight-tint px-6 py-8 sm:-mx-8 sm:px-8">
        <div className="absolute inset-x-0 top-0 h-[2px] bg-brand-gradient" />
        <Quote className="h-7 w-7 text-aion-insight/40" />
        <p className="mb-3 mt-2 text-xs font-semibold uppercase tracking-wide text-aion-insight">Executive summary — Axon</p>
        {isLoading ? (
          <div className="max-w-3xl space-y-2.5">
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-4/5" />
            <Skeleton className="h-5 w-3/5" />
          </div>
        ) : briefing?.executive_summary ? (
          <p className="max-w-3xl text-xl leading-relaxed text-aion-ink" style={{ fontFamily: "var(--font-head, ui-serif, Georgia, serif)" }}>
            {briefing.executive_summary}
          </p>
        ) : (
          <p className="text-sm text-aion-ink-muted">No briefing available.</p>
        )}
      </motion.div>

      {/* OII Score (bare hero) + KPI rows — asymmetric, not 4 equal boxes */}
      {briefing?.key_metrics && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }} className="grid grid-cols-1 gap-6 lg:grid-cols-12 lg:items-center">
          <div className="flex flex-col items-center gap-2 lg:col-span-3">
            <p
              className="text-xs font-medium text-aion-ink-muted uppercase tracking-wider cursor-help"
              title="12-dimension composite score (0-100) of your organization's knowledge health and continuity readiness"
            >
              OII Score
            </p>
            {/* Glow moment 2 of 2: the score every board member looks at first. */}
            <div className="rounded-full shadow-glow-accent"><OIIHealthGauge value={briefing.key_metrics.overall_oii_score ?? 0} size="md" /></div>
          </div>
          <div className="grid grid-cols-2 gap-x-8 gap-y-5 border-t border-aion-border pt-6 lg:col-span-9 lg:grid-cols-4 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0">
            {kpiEntries.map(([key, value]) => (
              <div key={key}>
                <p className="text-2xs font-medium text-aion-ink-faint uppercase tracking-wider capitalize cursor-help" title={`Metric: ${key.replace(/_/g, " ")}`}>{key.replace(/_/g, " ")}</p>
                <p className="mt-1 text-2xl font-bold text-aion-ink tabular-nums">
                  {typeof value === "number" ? (
                    <CountUp value={value} decimals={value % 1 !== 0 ? 2 : 0} />
                  ) : String(value)}
                </p>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Risks + Opportunities */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.16 }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-health-red" />
                Strategic Risks
                {risks?.length != null && <Badge variant="danger">{risks.length}</Badge>}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 max-h-96 overflow-y-auto no-scrollbar">
              {risks?.length ? (
                (risks as any[]).map((r: any, i: number) => <RiskCard key={r.id ?? i} risk={r} i={i} />)
              ) : (
                <div className="flex flex-col items-center gap-2 py-6 text-center">
                  <Shield className="h-5 w-5 text-health-green" />
                  <p className="text-sm text-aion-ink-muted">No strategic risks identified — organization looks stable</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-health-green" />
                Strategic Opportunities
                {opportunities?.length != null && <Badge variant="success">{opportunities.length}</Badge>}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 max-h-96 overflow-y-auto no-scrollbar">
              {opportunities?.length ? (
                (opportunities as any[]).map((o: any, i: number) => <OpportunityCard key={o.id ?? i} opp={o} i={i} />)
              ) : (
                <div className="flex flex-col items-center gap-2 py-6 text-center">
                  <TrendingUp className="h-5 w-5 text-aion-ink-faint" />
                  <p className="text-sm text-aion-ink-muted">No opportunities identified yet — check back after the next scan</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Board Recommendations — Axon narrative, pull-quote treatment */}
      {!!(briefing?.recommendations?.length) && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.24 }} className="relative -mx-6 bg-aion-surface2 px-6 py-7 sm:-mx-8 sm:px-8">
          <p className="mb-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-aion-insight">
            <Shield className="h-3.5 w-3.5" />
            Board recommendations — Axon
          </p>
          <div className="space-y-4">
            {briefing?.recommendations?.map((rec: any, i: number) => (
              <div key={i} className="flex items-start gap-3">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-aion-insight-tint text-xs font-bold text-aion-insight">
                  {i + 1}
                </div>
                <div>
                  {rec.title && <p className="text-sm font-semibold text-aion-ink mb-0.5">{rec.title}</p>}
                  <p className="text-sm text-aion-ink-muted leading-relaxed">{rec.description ?? rec}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
