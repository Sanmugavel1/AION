"use client";
import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bug, RefreshCw, Dna, BrainCog, Radio, Archive, Lightbulb,
  Activity, ChevronDown, AlertTriangle, ShieldCheck, ListChecks, DatabaseZap,
} from "lucide-react";
import { useDiseaseScan } from "@/lib/hooks/use-diseases";
import { DiseaseResult, DiseaseType } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import { toast } from "sonner";
import { SeverityGauge } from "./severity-gauge";

const EASE = [0.16, 1, 0.3, 1] as const;

const DISEASE_META: Record<DiseaseType, { label: string; icon: React.ComponentType<{ className?: string }>; desc: string }> = {
  knowledge_cancer: {
    label: "Knowledge Cancer",
    icon: Dna,
    desc: "Duplicate SOPs across teams, near-identical documents, version confusion",
  },
  memory_alzheimers: {
    label: "Memory Alzheimer's",
    icon: BrainCog,
    desc: "Senior employees leaving with no documentation of how work was actually done",
  },
  communication_stroke: {
    label: "Communication Stroke",
    icon: Radio,
    desc: "Departments stop sharing information with each other",
  },
  knowledge_obesity: {
    label: "Knowledge Obesity",
    icon: Archive,
    desc: "Too much information accumulated over time, nobody can find what they need",
  },
  innovation_paralysis: {
    label: "Innovation Paralysis",
    icon: Lightbulb,
    desc: "Same ideas repeated across teams and time, no genuinely new solutions emerging",
  },
};

const SEVERITY_CONFIG = {
  critical: {
    text: "text-health-red",
    hex: "#F45B5B",
    border: "border-health-red-border",
    bg: "bg-health-red-tint",
    dot: "bg-health-red",
    badge: "danger" as const,
  },
  warning: {
    text: "text-health-yellow",
    hex: "#F5A623",
    border: "border-health-yellow-border",
    bg: "bg-health-yellow-tint",
    dot: "bg-health-yellow",
    badge: "warning" as const,
  },
  healthy: {
    text: "text-health-green",
    hex: "#3FCF8E",
    border: "border-health-green-border",
    bg: "bg-health-green-tint",
    dot: "bg-health-green",
    badge: "success" as const,
  },
  no_data: {
    text: "text-aion-ink-faint",
    hex: "#94A3B8",
    border: "border-aion-border-strong",
    bg: "bg-aion-surface2",
    dot: "bg-aion-ink-faint",
    badge: "secondary" as const,
  },
};

/**
 * The backend has no distinct "insufficient data" severity enum — diseases
 * without a data source report severity="healthy", severity_score=0,
 * confidence=0 to avoid fabricating a score. Surfacing those as a plain
 * green "Healthy" badge would misleadingly imply the org was measured and
 * found fine, so detect that signature and render a neutral "no data" state
 * instead.
 */
function isInsufficientData(disease: DiseaseResult): boolean {
  return disease.confidence === 0 && /insufficient data/i.test(disease.description ?? "");
}

function EvidencePanel({ evidence }: { evidence: Record<string, unknown> }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(evidence);
  if (entries.length === 0) return null;

  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between text-xs text-aion-ink-muted cursor-pointer hover:text-aion-ink transition-colors duration-200"
      >
        <span className="flex items-center gap-1.5">
          <ListChecks className="h-3.5 w-3.5" />
          View evidence
        </span>
        <ChevronDown className={cn("h-3.5 w-3.5 transition-transform duration-300", open && "rotate-180")} />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: EASE }}
            className="overflow-hidden"
          >
            <div className="mt-2 space-y-1.5 rounded-md border border-aion-border bg-aion-bg p-3">
              {entries.map(([k, v]) => (
                <div key={k} className="flex items-center justify-between gap-3 text-xs">
                  <span className="text-aion-ink-muted capitalize">{k.replace(/_/g, " ")}</span>
                  <span className="truncate text-aion-ink font-mono">{String(v)}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/** Compact row treatment for non-featured diseases — a scannable triage list, not another box in a card farm. */
function DiseaseRow({ disease, type, i }: { disease: DiseaseResult; type: DiseaseType; i: number }) {
  const meta = DISEASE_META[type];
  const noData = isInsufficientData(disease);
  const cfg = noData ? SEVERITY_CONFIG.no_data : SEVERITY_CONFIG[disease.severity];
  const Icon = meta.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, ease: EASE, delay: 0.15 + i * 0.05 }}
      className={cn("flex items-center gap-4 border-l-[3px] bg-aion-surface px-4 py-3.5", cfg.border)}
      style={{ borderLeftColor: cfg.hex }}
    >
      <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg", cfg.bg)}>
        <Icon className={cn("h-4 w-4", cfg.text)} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-semibold text-aion-ink">{meta.label}</p>
          <Badge variant={cfg.badge}>{noData ? "No data" : disease.severity}</Badge>
        </div>
        <p className="text-2xs text-aion-ink-muted truncate mt-0.5">{meta.desc}</p>
      </div>
      {!noData ? (
        <div className="hidden shrink-0 items-center gap-2 sm:flex">
          <div className="h-1.5 w-24 overflow-hidden rounded-full bg-aion-surface2">
            <motion.div
              className={cn("h-full rounded-full", cfg.dot)}
              initial={{ width: 0 }}
              animate={{ width: `${disease.severity_score}%` }}
              transition={{ duration: 0.6, delay: 0.3 + i * 0.05, ease: EASE }}
            />
          </div>
          <span className={cn("w-10 text-right text-xs font-bold tabular-nums", cfg.text)}>{disease.severity_score.toFixed(0)}%</span>
        </div>
      ) : (
        <span className="hidden shrink-0 text-2xs text-aion-ink-faint sm:inline">Missing input</span>
      )}
    </motion.div>
  );
}

function DiseaseCard({ disease, type, featured, i }: { disease: DiseaseResult; type: DiseaseType; featured?: boolean; i: number }) {
  const meta = DISEASE_META[type];
  const noData = isInsufficientData(disease);
  const cfg = noData ? SEVERITY_CONFIG.no_data : SEVERITY_CONFIG[disease.severity];
  const Icon = meta.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ duration: 0.4, ease: EASE, delay: i * 0.06 }}
      className="h-full"
    >
      <Card
        className={cn(
          "relative h-full overflow-hidden border",
          cfg.border,
          cfg.bg,
          featured && !noData && disease.severity === "critical" && "shadow-glow-rose",
        )}
      >
        {featured && !noData && (
          <div className={cn("absolute inset-x-0 top-0 h-1", cfg.dot)} />
        )}
        <CardHeader className={cn("pb-3", featured && "sm:pb-4")}>
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className={cn("flex shrink-0 items-center justify-center rounded-lg border bg-aion-surface", cfg.border, featured ? "h-11 w-11" : "h-9 w-9")}>
                <Icon className={cn(featured ? "h-5 w-5" : "h-4 w-4", cfg.text)} />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className={cn("h-1.5 w-1.5 rounded-full", cfg.dot)} />
                  <CardTitle className={cn(featured ? "text-base" : "text-sm")}>{meta.label}</CardTitle>
                </div>
                <p className={cn("text-2xs text-aion-ink-muted mt-0.5", featured ? "max-w-md" : "max-w-[15rem]")}>{meta.desc}</p>
              </div>
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              <Badge variant={cfg.badge}>{noData ? "No data source" : disease.severity}</Badge>
              {!noData && (
                <span className="text-2xs text-aion-ink-faint">{(disease.confidence * 100).toFixed(0)}% confidence</span>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {noData ? (
            <div className="flex items-center gap-3 rounded-md border border-dashed border-aion-border-strong bg-aion-surface px-3 py-3">
              <DatabaseZap className="h-4 w-4 shrink-0 text-aion-ink-faint" />
              <p className="text-xs leading-relaxed text-aion-ink-muted">
                Not yet detectable — AION doesn&rsquo;t have the data source for this pattern in your graph yet
                (this isn&rsquo;t a health reading, it&rsquo;s a missing input).
              </p>
            </div>
          ) : (
            <div className="flex items-center gap-4">
              <SeverityGauge value={disease.severity_score} colorClass={cfg.text} colorHex={cfg.hex} size={featured ? 76 : 60} delay={i * 0.06 + 0.1} />
              <div className="flex-1 space-y-1.5">
                <p className="text-2xs uppercase tracking-wider text-aion-ink-faint">Severity Score</p>
                <p className={cn("text-xs leading-relaxed text-aion-ink-muted", featured ? "line-clamp-3" : "line-clamp-2")}>{disease.description}</p>
              </div>
            </div>
          )}

          {disease.days_until_critical !== null && (
            <div className={cn("flex items-center gap-2.5 rounded-md border px-3 py-2 bg-aion-surface", cfg.border)}>
              <AlertTriangle className={cn("h-3.5 w-3.5 shrink-0", cfg.text)} />
              <div className="flex-1">
                <p className="text-2xs text-aion-ink-muted">Days until critical</p>
              </div>
              <p className={cn("text-base font-bold tabular-nums", cfg.text)}>
                {disease.days_until_critical}
                <span className="ml-1 text-2xs font-normal text-aion-ink-muted">days</span>
              </p>
            </div>
          )}

          {disease.recommended_action && (
            <div className="rounded-md border border-aion-border bg-aion-surface2 px-3 py-2">
              <p className="text-2xs text-aion-ink-faint uppercase tracking-wider">Recommended Action</p>
              <p className="text-xs text-aion-ink mt-0.5 font-medium capitalize">
                {disease.recommended_action.replace(/_/g, " ")}
              </p>
            </div>
          )}

          <EvidencePanel evidence={disease.evidence} />
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default function DiseasesPage() {
  const { data, isLoading, refetch } = useDiseaseScan();
  const [scanning, setScanning] = useState(false);

  const handleRescan = async () => {
    setScanning(true);
    try {
      await refetch();
      toast.success("Disease scan completed");
    } catch {
      toast.error("Scan failed");
    } finally {
      setScanning(false);
    }
  };

  const ordered = useMemo(() => {
    if (!data) return [];
    const entries = Object.entries(data.diseases) as [DiseaseType, DiseaseResult][];
    return entries.sort((a, b) => b[1].severity_score - a[1].severity_score);
  }, [data]);

  const [featured, ...rest] = ordered;

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Bug className="h-5 w-5 text-aion-accent" />
            Disease Detection
          </h1>
          <p className="page-subtitle mt-1 flex items-center gap-1.5">
            <Activity className="h-3.5 w-3.5 text-aion-ink-faint" />
            Organizational health diagnostics — 5 disease patterns
          </p>
        </div>
        <div className="flex items-center gap-3">
          {data && (
            <div className="flex items-center gap-2 rounded-md border border-aion-border bg-aion-surface px-4 py-1.5">
              <span
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  data.overall_health_score >= 75 ? "bg-health-green" : data.overall_health_score >= 50 ? "bg-health-yellow" : "bg-health-red",
                )}
              />
              <span className="text-xs text-aion-ink-muted">Org Health</span>
              <span className={cn(
                "text-sm font-bold tabular-nums",
                data.overall_health_score >= 75 ? "text-health-green" :
                  data.overall_health_score >= 50 ? "text-health-yellow" : "text-health-red",
              )}>
                {data.overall_health_score}%
              </span>
            </div>
          )}
          <Button
            onClick={handleRescan}
            loading={scanning}
            size="sm"
            className="relative overflow-hidden border-0 bg-brand-gradient bg-[length:160%_100%] bg-left text-white shadow-glow-accent transition-[background-position,transform] duration-300 hover:bg-right hover:-translate-y-0.5"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", scanning && "animate-spin")} />
            {scanning ? "Scanning…" : "Run Scan"}
          </Button>
        </div>
      </motion.div>

      {/* Summary strip — plain typography, no card chrome; this is a glance-and-go readout, not content that needs its own boxes */}
      {data && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className="flex items-center gap-8 border-y border-aion-border py-4">
          {[
            { label: "Critical", value: data.critical_diseases, color: "text-health-red" },
            { label: "Warning", value: data.warning_diseases, color: "text-health-yellow" },
            { label: "Healthy", value: data.healthy_dimensions, color: "text-health-green" },
          ].map((item, idx) => (
            <div key={item.label} className={cn("flex items-baseline gap-2.5", idx > 0 && "border-l border-aion-border pl-8")}>
              <span className={cn("text-3xl font-bold tabular-nums", item.color)}>{item.value}</span>
              <span className="text-xs text-aion-ink-muted uppercase tracking-wide">{item.label}</span>
            </div>
          ))}
        </motion.div>
      )}

      {/* Disease scan — featured (highest severity) as a full diagnostic card, the rest as a compact triage list */}
      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-56 rounded-lg" />
          <div className="space-y-px">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-16 rounded-lg" />)}
          </div>
        </div>
      ) : data && featured ? (
        <div className="space-y-4">
          <DiseaseCard disease={featured[1]} type={featured[0]} featured i={0} />
          <div className="overflow-hidden rounded-lg border border-aion-border divide-y divide-aion-border">
            {rest.map(([type, disease], i) => (
              <DiseaseRow key={type} disease={disease} type={type} i={i} />
            ))}
          </div>
        </div>
      ) : (
        <Card className="p-10 text-center">
          <Bug className="h-10 w-10 text-aion-ink-faint mx-auto mb-3" />
          <p className="text-sm text-aion-ink-muted">No scan data available. Click &ldquo;Run Scan&rdquo; to start.</p>
        </Card>
      )}

      {data && (
        <p className="flex items-center justify-center gap-1.5 text-xs text-aion-ink-faint">
          <ShieldCheck className="h-3.5 w-3.5" />
          Last scanned: {new Date(data.scan_timestamp).toLocaleString()}
        </p>
      )}
    </div>
  );
}
