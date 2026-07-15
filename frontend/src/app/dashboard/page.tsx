"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { Brain, Bone as Bottleneck, EyeOff, Wrench, ArrowRight, Activity, Quote } from "lucide-react";
import { useIntelligenceIndex } from "@/lib/hooks/use-intelligence";
import { useDiseaseScan } from "@/lib/hooks/use-diseases";
import { useDecayReport } from "@/lib/hooks/use-decay";
import { useHealingRecommendations } from "@/lib/hooks/use-healing";
import { useAuthStore } from "@/lib/stores/auth.store";
import { OIIHealthGauge } from "@/components/dashboard/oii-health-gauge";
import { DiseaseAlertStrip } from "@/components/dashboard/disease-alert-strip";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";

function StatRow({
  href, icon: Icon, label, value, loading, tone = "default",
}: {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number | string;
  loading?: boolean;
  tone?: "default" | "danger" | "warning" | "insight";
}) {
  const toneText =
    tone === "danger" ? "text-health-red"
    : tone === "warning" ? "text-health-yellow"
    : tone === "insight" ? "text-aion-insight"
    : "text-aion-ink";
  const toneIconBg =
    tone === "danger" ? "bg-health-red-tint"
    : tone === "warning" ? "bg-health-yellow-tint"
    : tone === "insight" ? "bg-aion-insight-tint"
    : "bg-aion-accent-tint";
  return (
    <Link
      href={href}
      className="group flex items-center gap-3 py-3 first:pt-0 last:pb-0 border-b border-aion-border last:border-0"
    >
      <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-md", toneIconBg, toneText)}>
        <Icon className="h-3.5 w-3.5" />
      </div>
      <p className="flex-1 text-sm text-aion-ink-muted group-hover:text-aion-ink transition-colors">{label}</p>
      {loading ? (
        <Skeleton className="h-6 w-8" />
      ) : (
        <span className={cn("text-lg font-bold tabular-nums", toneText)}>{value}</span>
      )}
      <ArrowRight className="h-3.5 w-3.5 text-aion-ink-faint opacity-0 transition-opacity group-hover:opacity-100" />
    </Link>
  );
}

export default function DashboardOverviewPage() {
  const user = useAuthStore((s) => s.user);
  const { data: oiiData, isLoading: oiiLoading } = useIntelligenceIndex();
  const oii = oiiData && "overall_health" in oiiData ? oiiData : undefined;
  const { data: diseases, isLoading: diseasesLoading } = useDiseaseScan();
  const { data: decay, isLoading: decayLoading } = useDecayReport();
  const { data: healing, isLoading: healingLoading } = useHealingRecommendations("pending");

  const greeting = user?.role === "org_admin" ? "Executive Overview" : "Organizational Overview";

  return (
    <div className="space-y-10">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Activity className="h-5 w-5 text-aion-accent" />
            {greeting}
          </h1>
          <p className="page-subtitle mt-1">
            Real-time pulse on your organization&apos;s knowledge health, risks, and continuity.
          </p>
        </div>
        <span className="flex shrink-0 items-center gap-1.5 rounded-md border border-health-green-border bg-health-green-tint px-2.5 py-1">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-health-green opacity-75" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-health-green" />
          </span>
          <span className="text-xs font-medium text-health-green">Live</span>
        </span>
      </motion.div>

      {/* Hero band — full-bleed tinted section, no card border. The OII score is the
          most important number on the page; it earns bare typography, not a box. */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="relative -mx-6 overflow-hidden bg-aion-surface2 px-6 py-8 sm:-mx-8 sm:px-8"
      >
        {/* Glow moment 1 of 2: a faint drifting brand mesh behind the org's headline number — this is the one number every visitor looks at first. */}
        <div className="pointer-events-none absolute inset-0 animate-aurora bg-brand-mesh opacity-40" />
        <div className="absolute inset-x-0 top-0 h-[2px] bg-brand-gradient" />
        <div className="relative grid grid-cols-1 gap-8 lg:grid-cols-12 lg:items-center">
          <div className="flex items-center gap-6 lg:col-span-7">
            {oiiLoading ? (
              <Skeleton className="h-24 w-24 rounded-full shrink-0" />
            ) : oii ? (
              <div className="shrink-0 rounded-full shadow-glow-accent"><OIIHealthGauge value={oii.overall_health} size="lg" /></div>
            ) : (
              <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-full border border-dashed border-aion-border-strong px-2 text-center text-2xs text-aion-ink-faint">
                No OII data yet
              </div>
            )}
            <div>
              <p
                className="text-xs font-semibold uppercase tracking-wider text-aion-ink-muted cursor-help"
                title="OII: a 12-dimension composite score (0-100) measuring how well your organization captures, retains, and shares knowledge."
              >
                Organizational Intelligence Index
              </p>
              <div className="mt-1 font-serif text-5xl font-medium tabular-nums text-aion-ink" style={{ fontFamily: "var(--font-head, ui-serif, Georgia, serif)" }}>
                {oiiLoading ? <Skeleton className="h-12 w-24" /> : oii ? `${oii.overall_health.toFixed(0)}` : "—"}
                {oii && <span className="text-xl text-aion-ink-faint font-sans">/100</span>}
              </div>
              <Link
                href="/dashboard/intelligence"
                className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-aion-accent hover:text-aion-accent-hover"
              >
                View full breakdown <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
          <div className="flex gap-8 border-t border-aion-border-strong pt-6 lg:col-span-5 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0">
            <div title="Diseases currently at critical severity — needs immediate attention">
              <p className="text-2xs font-medium uppercase tracking-wide text-aion-ink-faint cursor-help">Critical</p>
              <div className="text-3xl font-bold tabular-nums text-health-red">
                {diseasesLoading ? <Skeleton className="h-8 w-8" /> : diseases?.critical_diseases ?? 0}
              </div>
            </div>
            <div title="Diseases showing early warning signs">
              <p className="text-2xs font-medium uppercase tracking-wide text-aion-ink-faint cursor-help">Warning</p>
              <div className="text-3xl font-bold tabular-nums text-health-yellow">
                {diseasesLoading ? <Skeleton className="h-8 w-8" /> : diseases?.warning_diseases ?? 0}
              </div>
            </div>
            <div title="Dimensions with no detected issues">
              <p className="text-2xs font-medium uppercase tracking-wide text-aion-ink-faint cursor-help">Healthy</p>
              <div className="text-3xl font-bold tabular-nums text-health-green">
                {diseasesLoading ? <Skeleton className="h-8 w-8" /> : diseases?.healthy_dimensions ?? 0}
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Disease strip */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-aion-ink">5 Organizational Diseases</h2>
          <Link href="/dashboard/diseases" className="text-xs text-aion-ink-muted hover:text-aion-ink">
            View disease panel &rarr;
          </Link>
        </div>
        {diseasesLoading ? (
          <div className="grid grid-cols-5 gap-3">
            {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-lg" />)}
          </div>
        ) : diseases ? (
          <DiseaseAlertStrip data={diseases} />
        ) : (
          <Card className="flex flex-col items-center gap-2 p-8 text-center">
            <Bottleneck className="h-5 w-5 text-aion-ink-faint" />
            <p className="text-sm text-aion-ink-muted">No disease scan has run yet</p>
            <Link href="/dashboard/diseases" className="text-xs font-medium text-aion-accent hover:text-aion-accent-hover">
              Run a scan &rarr;
            </Link>
          </Card>
        )}
      </motion.div>

      {/* Asymmetric row: grouped stat list (5 cols) + Axon's recommendations as a pull-quote (7 cols) */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        <Card className="p-5 lg:col-span-5">
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-aion-ink-faint">Needs attention</h3>
          <StatRow
            href="/dashboard/decay"
            icon={Bottleneck}
            label="Single-owner critical knowledge"
            value={decay?.summary.single_owner_critical ?? 0}
            loading={decayLoading}
            tone={(decay?.summary.single_owner_critical ?? 0) > 0 ? "danger" : "default"}
          />
          <StatRow
            href="/dashboard/decay"
            icon={EyeOff}
            label="Isolated knowledge items"
            value={decay?.summary.isolated_items ?? 0}
            loading={decayLoading}
            tone={(decay?.summary.isolated_items ?? 0) > 0 ? "warning" : "default"}
          />
          <StatRow
            href="/dashboard/healing"
            icon={Wrench}
            label="Pending healing recommendations"
            value={healing?.total ?? 0}
            loading={healingLoading}
            tone="insight"
          />
        </Card>

        {decay?.recommendations && decay.recommendations.length > 0 ? (
          // Glow moment 2 of 2: Axon's own words get the brand-gradient treatment — the one place it's earned, since this literally is the AI feature.
          <div className="relative overflow-hidden rounded-lg bg-aion-insight-tint p-6 lg:col-span-7">
            <div className="absolute inset-x-0 top-0 h-[2px] bg-brand-gradient" />
            <Quote className="h-6 w-6 text-aion-violet/50" />
            <p className="mb-3 mt-2 text-xs font-semibold uppercase tracking-wide text-aion-insight">Axon recommends</p>
            <div className="space-y-3">
              {decay.recommendations.map((rec, i) => (
                <p key={i} className="border-l-2 border-aion-insight/30 pl-3 text-base leading-relaxed text-aion-ink">
                  {rec}
                </p>
              ))}
            </div>
            <Link
              href="/dashboard/advisor"
              className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-aion-insight hover:opacity-80"
            >
              Ask Axon to explain <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        ) : (
          <Card className="flex flex-col items-center justify-center gap-2 p-6 text-center lg:col-span-7">
            <Brain className="h-5 w-5 text-aion-ink-faint" />
            <p className="text-sm text-aion-ink-muted">No open recommendations right now — Axon will surface new ones as it senses changes in your knowledge graph.</p>
          </Card>
        )}
      </motion.div>
    </div>
  );
}
