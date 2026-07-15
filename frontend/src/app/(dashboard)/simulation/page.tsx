"use client";
import { motion } from "framer-motion";
import {
  FlaskConical, Play, DollarSign, Clock, AlertTriangle, Users,
  UserMinus, Building2, ClipboardX, ServerCrash, TrendingDown, type LucideIcon,
} from "lucide-react";
import { useSimulationScenarios, useRunSimulation } from "@/lib/hooks/use-simulation";
import { useUIStore } from "@/lib/stores/ui.store";
import { PredefinedScenario, SimulationResult } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import { formatCurrency } from "@/lib/utils/format";
import { CascadeChain } from "./cascade-chain";

const EASE = [0.16, 1, 0.3, 1] as const;

const SCENARIO_META: Record<string, { icon: LucideIcon; text: string; bg: string; border: string; solid: string }> = {
  employee_departure: { icon: UserMinus, text: "text-aion-accent", bg: "bg-aion-accent-tint", border: "border-aion-accent-border", solid: "bg-aion-accent" },
  mass_resignation: { icon: Users, text: "text-health-red", bg: "bg-health-red-tint", border: "border-health-red-border", solid: "bg-health-red" },
  department_closure: { icon: Building2, text: "text-aion-insight", bg: "bg-aion-insight-tint", border: "border-aion-border", solid: "bg-aion-insight" },
  project_delay: { icon: ClipboardX, text: "text-health-yellow", bg: "bg-health-yellow-tint", border: "border-health-yellow-border", solid: "bg-health-yellow" },
  system_failure: { icon: ServerCrash, text: "text-health-red", bg: "bg-health-red-tint", border: "border-health-red-border", solid: "bg-health-red" },
};
const DEFAULT_META = { icon: FlaskConical, text: "text-aion-accent", bg: "bg-aion-accent-tint", border: "border-aion-accent-border", solid: "bg-aion-accent" };

/** Wide, prominent treatment for the first (most common) scenario — an entry point, not one of a farm of equal choices. */
function FeaturedScenarioCard({ scenario, onRun, isRunning }: { scenario: PredefinedScenario; onRun: () => void; isRunning: boolean }) {
  const meta = SCENARIO_META[scenario.scenario_type] || DEFAULT_META;
  const Icon = meta.icon;
  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, ease: EASE }}>
      <Card className="relative overflow-hidden shadow-glow-violet">
        <div className={cn("absolute inset-x-0 top-0 h-1", meta.solid)} />
        <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
          <div className={cn("flex h-14 w-14 shrink-0 items-center justify-center rounded-xl border", meta.bg, meta.border)}>
            <Icon className={cn("h-6 w-6", meta.text)} aria-hidden="true" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <p className="text-base font-semibold text-aion-ink">{scenario.name}</p>
              <Badge variant="secondary" className="text-2xs">Most common</Badge>
            </div>
            <p className="mt-0.5 text-xs text-aion-ink-muted leading-relaxed">{scenario.description}</p>
          </div>
          <Button
            onClick={onRun}
            loading={isRunning}
            className="shrink-0 sm:w-auto w-full border-0 bg-aion-insight text-white shadow-glow-violet hover:bg-aion-insight hover:brightness-110 hover:-translate-y-0.5 transition-[filter,transform] duration-300"
          >
            <Play className="h-3.5 w-3.5" />
            Run Simulation
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
}

/** Compact row for the remaining scenarios — a pick-list, not another grid of squares. */
function ScenarioRow({ scenario, onRun, isRunning, i }: { scenario: PredefinedScenario; onRun: () => void; isRunning: boolean; i: number }) {
  const meta = SCENARIO_META[scenario.scenario_type] || DEFAULT_META;
  const Icon = meta.icon;
  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, ease: EASE, delay: 0.1 + i * 0.05 }}
      className="group flex items-center gap-3.5 border-b border-aion-border py-3 last:border-b-0"
    >
      <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg", meta.bg)}>
        <Icon className={cn("h-4 w-4", meta.text)} aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-aion-ink">{scenario.name}</p>
        <p className="text-2xs text-aion-ink-muted truncate">{scenario.description}</p>
      </div>
      <Button
        onClick={onRun}
        loading={isRunning}
        size="sm"
        variant="outline"
        className="shrink-0 opacity-70 group-hover:opacity-100 transition-opacity"
      >
        <Play className="h-3.5 w-3.5" />
        Run
      </Button>
    </motion.div>
  );
}

function SimulationResults({ result }: { result: SimulationResult }) {
  const metrics = [
    { label: "Knowledge Loss", value: `${result.results.knowledge_loss_percentage?.toFixed(1) ?? 0}%`, icon: TrendingDown, color: "text-health-red" },
    { label: "Revenue Risk", value: formatCurrency(result.results.revenue_risk_usd ?? 0), icon: DollarSign, color: "text-health-yellow" },
    { label: "Recovery Time", value: `${result.results.recovery_time_days ?? 0} days`, icon: Clock, color: "text-health-yellow" },
    { label: "Affected Projects", value: String(Array.isArray(result.results.affected_projects) ? result.results.affected_projects.length : 0), icon: Users, color: "text-aion-ink" },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ ease: EASE }} className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="h-2 w-2 rounded-full bg-health-green" />
        <h2 className="text-sm font-semibold text-aion-ink">Simulation Complete</h2>
        <Badge variant="secondary" className="font-mono">{result.simulation_id}</Badge>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-3 rounded-lg border border-aion-border bg-aion-surface px-4 py-3.5">
        {metrics.map((m, i) => (
          <motion.div
            key={m.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08, ease: EASE }}
            className={cn("flex items-center gap-2.5", i % 2 === 1 && "border-l border-aion-border pl-4")}
          >
            <m.icon className={cn("h-4 w-4 shrink-0", m.color)} />
            <div className="min-w-0">
              <p className={cn("text-lg font-bold tabular-nums leading-tight", m.color)}>{m.value}</p>
              <p className="text-2xs text-aion-ink-faint truncate">{m.label}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {result.results.business_impact_summary && (
        <Card className="border-aion-insight/20 bg-aion-insight-tint shadow-glow-violet">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-aion-ink">
              Business Impact Summary
              <span className="rounded-full bg-aion-insight/10 px-2 py-0.5 text-2xs font-medium text-aion-insight">AI-generated</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-aion-ink-muted leading-relaxed">{result.results.business_impact_summary}</p>
          </CardContent>
        </Card>
      )}

      {Array.isArray(result.cascade_chain) && result.cascade_chain.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-3.5 w-3.5 text-aion-accent" />
              Cascade Chain
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CascadeChain steps={result.cascade_chain} />
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
}

function RunningState() {
  return (
    <Card className="p-8 text-center">
      <motion.div
        className="relative mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-aion-accent-tint ring-1 ring-aion-accent-border"
        animate={{ opacity: [0.75, 1, 0.75] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
      >
        <FlaskConical className="h-6 w-6 text-aion-accent animate-spin-slow" />
      </motion.div>
      <p className="text-sm font-medium text-aion-ink">Running simulation…</p>
      <p className="text-xs text-aion-ink-muted mt-1">Cascading through the memory graph</p>
      <div className="mx-auto mt-4 h-1 w-40 overflow-hidden rounded-full bg-aion-surface2">
        <motion.div
          className="h-full w-1/3 rounded-full bg-aion-accent"
          animate={{ x: ["-120%", "220%"] }}
          transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
        />
      </div>
    </Card>
  );
}

export default function SimulationPage() {
  const { data: scenariosData, isLoading } = useSimulationScenarios();
  const { mutate: runSim } = useRunSimulation();
  const isRunning = useUIStore((s) => s.isSimulationRunning);
  const result = useUIStore((s) => s.lastSimulationResult);

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <FlaskConical className="h-6 w-6 text-aion-accent" />
            Future Simulation Engine
          </h1>
          <p className="page-subtitle mt-1">What-if scenario modeling — cascade impact through the organizational memory graph</p>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_420px]">
        {/* Scenarios */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-aion-ink">Predefined Scenarios</h2>
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-24 rounded-lg" />
              <Skeleton className="h-40 rounded-lg" />
            </div>
          ) : (() => {
            const scenarios = scenariosData?.scenarios ?? [];
            const [featured, ...rest] = scenarios;
            if (!featured) return null;
            const runFor = (s: PredefinedScenario) => () =>
              runSim({ scenario_type: s.scenario_type, parameters: s.parameters, description: s.description });
            return (
              <div className="space-y-3">
                <FeaturedScenarioCard scenario={featured} isRunning={isRunning} onRun={runFor(featured)} />
                {rest.length > 0 && (
                  <Card className="px-4 py-1">
                    {rest.map((s, i) => (
                      <ScenarioRow key={s.id} scenario={s} isRunning={isRunning} i={i} onRun={runFor(s)} />
                    ))}
                  </Card>
                )}
              </div>
            );
          })()}
        </div>

        {/* Result panel */}
        <div>
          <h2 className="text-sm font-semibold text-aion-ink mb-4">Simulation Results</h2>
          {isRunning && <RunningState />}
          {!isRunning && result && <SimulationResults result={result} />}
          {!isRunning && !result && (
            <Card className="p-8 text-center text-aion-ink-muted">
              <FlaskConical className="h-10 w-10 mx-auto mb-3 text-aion-ink-faint" />
              <p className="text-sm">Select a scenario and run simulation</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
