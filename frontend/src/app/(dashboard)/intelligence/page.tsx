"use client";
import { motion } from "framer-motion";
import {
  Brain, TrendingUp, TrendingDown, Minus, Activity,
  Zap, LayoutGrid, Award, Wind, Users, Lightbulb,
  Target, Shield, Unlock, Layers, Archive, RefreshCw,
  type LucideIcon,
} from "lucide-react";
import { useIntelligenceIndex, useIntelligenceHistory, useIntelligenceTrends } from "@/lib/hooks/use-intelligence";
import { OIIHealthGauge } from "@/components/dashboard/oii-health-gauge";
import { OIIRadarChart } from "@/components/charts/oii-radar-chart";
import { TrendLineChart } from "@/components/charts/trend-line-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import { formatRelativeTime } from "@/lib/utils/format";
import { OIIDimensions, OIISnapshot } from "@/types";

const EASE = [0.16, 1, 0.3, 1] as const;

const DIMENSION_META: Record<keyof OIIDimensions, { label: string; icon: LucideIcon; hint: string }> = {
  knowledge_velocity: { label: "Knowledge Velocity", icon: Zap, hint: "How fast new knowledge is captured and shared across the org" },
  knowledge_coverage: { label: "Knowledge Coverage", icon: LayoutGrid, hint: "Share of critical domains that have documented knowledge" },
  knowledge_quality: { label: "Knowledge Quality", icon: Award, hint: "Completeness and reliability of documented knowledge" },
  learning_agility: { label: "Learning Agility", icon: Wind, hint: "How quickly the org absorbs and applies new information" },
  collaboration_density: { label: "Collaboration Density", icon: Users, hint: "How interconnected people and teams are when sharing knowledge" },
  innovation_index: { label: "Innovation Index", icon: Lightbulb, hint: "Rate of new ideas and knowledge creation" },
  decision_intelligence: { label: "Decision Intelligence", icon: Target, hint: "How well decisions are backed by available knowledge" },
  cognitive_resilience: { label: "Cognitive Resilience", icon: Shield, hint: "Ability to absorb the loss of a key person without losing knowledge" },
  knowledge_accessibility: { label: "Accessibility", icon: Unlock, hint: "How easily people can find and reach the knowledge they need" },
  expertise_depth: { label: "Expertise Depth", icon: Layers, hint: "Depth of specialist knowledge held per domain" },
  knowledge_retention: { label: "Knowledge Retention", icon: Archive, hint: "How well knowledge is preserved over time rather than lost" },
  adaptability_score: { label: "Adaptability", icon: RefreshCw, hint: "How readily the org's knowledge base adjusts to change" },
};

function severity(pct: number) {
  if (pct >= 75) return { text: "text-health-green", bg: "bg-health-green", border: "border-l-health-green", soft: "bg-health-green-tint", ring: "border-health-green-border" };
  if (pct >= 50) return { text: "text-health-yellow", bg: "bg-health-yellow", border: "border-l-health-yellow", soft: "bg-health-yellow-tint", ring: "border-health-yellow-border" };
  return { text: "text-health-red", bg: "bg-health-red", border: "border-l-health-red", soft: "bg-health-red-tint", ring: "border-health-red-border" };
}

function DimensionRow({ dimKey, value, i, isLast }: { dimKey: keyof OIIDimensions; value: number; i: number; isLast: boolean }) {
  const meta = DIMENSION_META[dimKey] ?? { label: dimKey, icon: Activity };
  const Icon = meta.icon;
  const pct = Math.round(value * 100);
  const sev = severity(pct);

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.2 + i * 0.03, duration: 0.35, ease: EASE }}
      className={cn(
        "flex items-center gap-3.5 px-4 py-3",
        !isLast && "border-b border-aion-border",
      )}
      title={meta.hint}
    >
      <span className="w-5 shrink-0 text-2xs font-semibold tabular-nums text-aion-ink-faint">{i + 1}</span>
      <div className={cn("flex h-7 w-7 shrink-0 items-center justify-center rounded-md", sev.soft)}>
        <Icon className={cn("h-3.5 w-3.5", sev.text)} />
      </div>
      <p className="w-44 shrink-0 truncate text-xs font-medium text-aion-ink cursor-help">{meta.label}</p>
      <div className="h-1.5 flex-1 rounded-full bg-aion-surface2">
        <motion.div
          className={cn("h-full rounded-full", sev.bg)}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.7, delay: 0.25 + i * 0.03, ease: EASE }}
        />
      </div>
      <span className={cn("w-8 shrink-0 text-right text-xs font-bold tabular-nums", sev.text)}>{pct}</span>
    </motion.div>
  );
}

export default function IntelligencePage() {
  const { data: oiiData, isLoading } = useIntelligenceIndex();
  const { isLoading: historyLoading } = useIntelligenceHistory();
  const { data: trends } = useIntelligenceTrends();
  const oii = oiiData as OIISnapshot | undefined;

  const TrendIcon = trends?.trend === "improving" ? TrendingUp : trends?.trend === "declining" ? TrendingDown : Minus;
  const trendColor = trends?.trend === "improving" ? "text-health-green" : trends?.trend === "declining" ? "text-health-red" : "text-aion-ink-muted";

  const scorePct = oii ? Math.round(oii.overall_health * 100) : 0;
  const scoreSev = severity(scorePct);

  const rankedDimensions = oii?.dimensions
    ? (Object.entries(oii.dimensions) as [keyof OIIDimensions, number][]).sort((a, b) => a[1] - b[1])
    : [];

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Brain className="h-5 w-5 text-aion-accent" />
            Organizational Intelligence Index
          </h1>
          <p className="page-subtitle mt-1">12-dimension composite score — real-time measure of organizational knowledge health</p>
        </div>
        {oii && (
          <div className="flex items-center gap-2 rounded-md border border-aion-border bg-aion-surface px-3.5 py-2 shadow-card">
            <TrendIcon className={cn("h-4 w-4", trendColor)} />
            <span className="text-sm text-aion-ink-muted capitalize">{trends?.trend ?? "stable"}</span>
            {trends?.delta_30d !== undefined && (
              <Badge variant={trends.delta_30d >= 0 ? "success" : "danger"}>
                {trends.delta_30d >= 0 ? "+" : ""}{(trends.delta_30d * 100).toFixed(1)}%
              </Badge>
            )}
          </div>
        )}
      </motion.div>

      {/* Hero: score + radar */}
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05, duration: 0.5, ease: EASE }}>
        <Card className="relative overflow-hidden p-0 shadow-glow-accent">
          <div className="absolute inset-x-0 top-0 h-1 bg-brand-gradient" />
          <Brain className="pointer-events-none absolute -right-6 -top-6 h-40 w-40 text-aion-ink opacity-[0.03]" />
          <div className="grid grid-cols-1 lg:grid-cols-5">
            <div className="flex flex-col justify-center gap-6 border-b border-aion-border p-8 lg:col-span-2 lg:border-b-0 lg:border-r">
              <div>
                <p
                  className="mb-2 cursor-help text-xs font-semibold uppercase tracking-wide text-aion-ink-faint"
                  title="Composite score across 12 weighted dimensions of organizational knowledge health, 0–100"
                >
                  Overall Intelligence Score
                </p>
                {isLoading ? (
                  <Skeleton className="h-14 w-28" />
                ) : (
                  <div className="flex items-end gap-3">
                    <span className={cn("text-6xl font-bold tabular-nums leading-none", scoreSev.text)}>
                      {oii ? scorePct : "—"}
                    </span>
                    <span className="mb-1.5 text-lg text-aion-ink-faint">/100</span>
                  </div>
                )}
              </div>
              {oii && (
                <div className="grid grid-cols-3 gap-4 border-t border-aion-border pt-5">
                  <div className="cursor-help" title="Estimated days until half of current documented knowledge becomes stale without refresh">
                    <p className="text-2xs font-medium text-aion-ink-faint">Half-Life</p>
                    <p className="text-base font-semibold text-aion-ink tabular-nums">
                      {oii.proprietary_metrics.knowledge_half_life_days}d
                    </p>
                  </div>
                  <div className="cursor-help" title="Shannon entropy of knowledge distribution across domains — higher means more spread out, less concentrated">
                    <p className="text-2xs font-medium text-aion-ink-faint">Entropy</p>
                    <p className="text-base font-semibold text-aion-ink tabular-nums">
                      {oii.proprietary_metrics.knowledge_entropy_bits.toFixed(2)}b
                    </p>
                  </div>
                  <div className="cursor-help" title="How efficiently knowledge is consolidated vs. duplicated across the organization">
                    <p className="text-2xs font-medium text-aion-ink-faint">Compression</p>
                    <p className="text-base font-semibold text-aion-ink tabular-nums">
                      {(oii.proprietary_metrics.memory_compression_ratio * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className="p-6 lg:col-span-3">
              <div className="mb-1 flex items-center justify-between">
                <p className="text-sm font-semibold text-aion-ink">12-Dimension Breakdown</p>
                {isLoading ? null : oii ? <OIIHealthGauge value={oii.overall_health} size="sm" /> : null}
              </div>
              {oii?.dimensions ? (
                <div
                  className="rounded-lg"
                  style={{
                    backgroundImage:
                      "radial-gradient(rgba(15,23,42,0.035) 1px, transparent 1px)",
                    backgroundSize: "16px 16px",
                  }}
                >
                  <OIIRadarChart dimensions={oii.dimensions} />
                </div>
              ) : (
                <Skeleton className="h-60 w-full rounded-lg" />
              )}
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Dimension breakdown — one continuous ranked list, weakest first, not 12 separate boxes */}
      <div className="space-y-3">
        <div className="flex items-baseline justify-between">
          <h2 className="text-sm font-semibold text-aion-ink">Dimension Detail</h2>
          <span className="text-2xs text-aion-ink-faint">Ranked lowest to highest — attention items first</span>
        </div>
        {isLoading ? (
          <Card className="divide-y divide-aion-border p-0">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="px-4 py-3"><Skeleton className="h-5 w-full" /></div>
            ))}
          </Card>
        ) : rankedDimensions.length ? (
          <Card className="overflow-hidden p-0">
            {rankedDimensions.map(([key, value], i) => (
              <DimensionRow key={key} dimKey={key} value={value} i={i} isLast={i === rankedDimensions.length - 1} />
            ))}
          </Card>
        ) : (
          <Card className="p-8 text-center text-aion-ink-muted text-sm">No dimension data available</Card>
        )}
      </div>

      {/* Historical trend */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25, ease: EASE }}>
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle title="Overall Intelligence Score sampled over time" className="cursor-help">Historical Trend</CardTitle>
              <Activity className="h-4 w-4 text-aion-ink-faint" />
            </div>
          </CardHeader>
          <CardContent>
            {historyLoading ? (
              <Skeleton className="h-40 w-full rounded-lg" />
            ) : trends?.history?.length ? (
              <div
                className="rounded-lg"
                style={{
                  backgroundImage:
                    "radial-gradient(rgba(15,23,42,0.035) 1px, transparent 1px)",
                  backgroundSize: "16px 16px",
                }}
              >
                <TrendLineChart data={trends.history} height={220} />
              </div>
            ) : (
              <p className="text-center text-sm text-aion-ink-muted py-10">No historical data</p>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {oii && (
        <p className="text-xs text-aion-ink-faint text-center">
          Last computed: {formatRelativeTime(oii.computed_at)}
        </p>
      )}
    </div>
  );
}
