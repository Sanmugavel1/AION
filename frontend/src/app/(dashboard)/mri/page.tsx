"use client";
import { motion } from "framer-motion";
import {
  Activity, AlertCircle, ArrowRight, Calendar,
  Lightbulb, Network, ScanEye, Eye,
} from "lucide-react";
import {
  useBrainMap, useBottlenecks, useBlackHoles,
  useInnovationCenters, useKnowledgeFlow, useTimelineForecast,
} from "@/lib/hooks/use-mri";
import { useUIStore } from "@/lib/stores/ui.store";
import { BrainMapCanvas } from "@/components/mri/brain-map-canvas";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import { truncate } from "@/lib/utils/format";

const EASE = [0.16, 1, 0.3, 1] as const;

const HEALTH_META = {
  green: { label: "Healthy", dot: "bg-health-green", text: "text-health-green" },
  yellow: { label: "Warning", dot: "bg-health-yellow", text: "text-health-yellow" },
  red: { label: "Critical", dot: "bg-health-red", text: "text-health-red" },
} as const;

export default function MRIPage() {
  const { data: brainMap, isLoading: mapLoading } = useBrainMap();
  const { data: bottlenecks } = useBottlenecks();
  const { data: blackHoles } = useBlackHoles();
  const { data: innovationCenters } = useInnovationCenters();
  const { data: flowData } = useKnowledgeFlow();
  const { data: forecast } = useTimelineForecast();
  const selectedNode = useUIStore((s) => s.selectedNode);

  const summary = brainMap?.summary;
  const maxFlow = flowData?.length ? Math.max(...flowData.map((f) => f.flow_strength)) : 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <ScanEye className="h-5 w-5 text-aion-violet" />
            Organizational MRI
          </h1>
          <p className="page-subtitle mt-1">Force-directed network analysis of organizational knowledge health</p>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-aion-border bg-aion-surface px-3.5 py-1.5 shadow-card">
          <motion.span
            className="h-1.5 w-1.5 rounded-full bg-health-green"
            animate={{ opacity: [1, 0.35, 1] }}
            transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
          />
          <span className="text-2xs font-semibold uppercase tracking-wide text-aion-ink-muted">Live</span>
        </div>
      </motion.div>

      {/* Flagship: network map + summary panel */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        <motion.div
          initial={{ opacity: 0, scale: 0.99 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.05, duration: 0.5, ease: EASE }}
          className="xl:col-span-8"
        >
          <Card
            className="relative overflow-hidden p-0 shadow-glow-violet"
            style={{
              height: 560,
              backgroundImage:
                "radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), radial-gradient(ellipse 70% 60% at 50% 40%, rgba(196,181,253,0.10), transparent)",
              backgroundSize: "20px 20px, 100% 100%",
            }}
          >
            {mapLoading ? (
              <div className="flex h-full items-center justify-center">
                <div className="flex flex-col items-center gap-3">
                  <Network className="h-10 w-10 text-aion-violet animate-pulse" />
                  <p className="text-sm text-aion-ink-muted">Loading network map…</p>
                </div>
              </div>
            ) : brainMap ? (
              <BrainMapCanvas data={brainMap} />
            ) : (
              <div className="flex h-full items-center justify-center text-aion-ink-muted text-sm">
                No graph data available
              </div>
            )}

            {/* Floating legend */}
            <div className="absolute bottom-4 left-4 flex gap-4 rounded-md border border-aion-border bg-aion-surface px-4 py-2.5 shadow-card-lg">
              {(Object.keys(HEALTH_META) as (keyof typeof HEALTH_META)[]).map((c) => (
                <div key={c} className="flex items-center gap-1.5">
                  <span className={cn("h-2 w-2 rounded-full", HEALTH_META[c].dot)} />
                  <span className="text-2xs text-aion-ink-muted">{HEALTH_META[c].label}</span>
                </div>
              ))}
            </div>

            {/* Node inspector */}
            {selectedNode && (
              <motion.div
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute top-4 right-4 rounded-md border border-aion-border bg-aion-surface p-4 max-w-xs shadow-card-lg"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-aion-ink-faint uppercase">{selectedNode.type}</span>
                  <div className={cn(
                    "h-2 w-2 rounded-full",
                    HEALTH_META[selectedNode.health_color]?.dot ?? "bg-aion-ink-faint",
                  )} />
                </div>
                <p className="text-sm font-semibold text-aion-ink">{selectedNode.label}</p>
                <p className="text-xs text-aion-ink-muted mt-1">{selectedNode.tooltip}</p>
                <div className="mt-2 flex items-center justify-between border-t border-aion-border pt-2">
                  <span className="text-xs text-aion-ink-faint">Connections</span>
                  <span className="text-xs font-semibold text-aion-ink">{selectedNode.connection_count}</span>
                </div>
              </motion.div>
            )}
          </Card>
        </motion.div>

        {/* Scan summary — accessible alternative to the canvas graph */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12, duration: 0.5, ease: EASE }}
          className="flex flex-col gap-4 xl:col-span-4"
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Network className="h-4 w-4 text-aion-violet" />
                Network Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              {summary ? (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-2xl font-bold tabular-nums text-aion-ink">{summary.total_nodes}</p>
                      <p className="text-2xs text-aion-ink-faint">Total nodes</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold tabular-nums text-aion-ink">{summary.total_connections}</p>
                      <p className="text-2xs text-aion-ink-faint">Connections</p>
                    </div>
                  </div>

                  <div>
                    <div className="mb-1.5 flex items-center justify-between text-2xs text-aion-ink-muted">
                      <span>Health distribution</span>
                      <span className={cn("font-semibold capitalize", HEALTH_META[summary.overall_health_color]?.text)}>
                        {summary.overall_health_color}
                      </span>
                    </div>
                    <div className="flex h-2 w-full overflow-hidden rounded-full bg-aion-surface2">
                      {(["green", "yellow", "red"] as const).map((c) => {
                        const count = c === "green" ? summary.green_nodes : c === "yellow" ? summary.yellow_nodes : summary.red_nodes;
                        const pct = summary.total_nodes ? (count / summary.total_nodes) * 100 : 0;
                        return (
                          <motion.div
                            key={c}
                            className={HEALTH_META[c].dot}
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 0.8, ease: EASE, delay: 0.2 }}
                          />
                        );
                      })}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { label: "Bottlenecks", count: bottlenecks?.length ?? 0, color: "text-health-red", bg: "bg-health-red-tint border-health-red-border", hint: "Knowledge items with only one owner — a single point of failure" },
                      { label: "Black holes", count: blackHoles?.length ?? 0, color: "text-health-red", bg: "bg-health-red-tint border-health-red-border", hint: "Isolated knowledge with no connections in or out of the graph" },
                      { label: "Innovation", count: innovationCenters?.length ?? 0, color: "text-health-green", bg: "bg-health-green-tint border-health-green-border", hint: "Hubs of high knowledge creation and cross-team collaboration" },
                    ].map((chip) => (
                      <div key={chip.label} className={cn("cursor-help rounded-md border px-2 py-2 text-center", chip.bg)} title={chip.hint}>
                        <p className={cn("text-base font-bold tabular-nums", chip.color)}>{chip.count}</p>
                        <p className="text-2xs leading-tight text-aion-ink-muted">{chip.label}</p>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="space-y-3">
                  <Skeleton className="h-10 w-full rounded-lg" />
                  <Skeleton className="h-2 w-full rounded-full" />
                  <Skeleton className="h-14 w-full rounded-lg" />
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="p-4">
            <p className="text-xs text-aion-ink-muted leading-relaxed">
              Click any node in the network map to inspect its health, type, and connection count. Node
              size reflects graph role — departments are largest, knowledge items smallest.
            </p>
          </Card>
        </motion.div>
      </div>

      {/* Data panels */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.18, ease: EASE }}>
          <Card className="border-l-2 border-l-health-red">
            <CardHeader>
              <CardTitle className="flex cursor-help items-center gap-2" title="Critical knowledge held by a single person — losing them would create an immediate gap">
                <AlertCircle className="h-4 w-4 text-health-red" />
                Knowledge Bottlenecks
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 max-h-52 overflow-y-auto no-scrollbar">
              {bottlenecks?.length ? bottlenecks.slice(0, 8).map((b) => (
                <div key={b.knowledge_id} className="flex items-start justify-between gap-2 rounded-lg bg-aion-bg p-2.5">
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-aion-ink truncate">{b.title}</p>
                    <p className="text-2xs text-aion-ink-faint">{b.domain}</p>
                  </div>
                  <Badge variant="danger" className="shrink-0">single owner</Badge>
                </div>
              )) : (
                <p className="text-sm text-health-green text-center py-4">No critical bottlenecks</p>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.22, ease: EASE }}>
          <Card className="border-l-2 border-l-health-red">
            <CardHeader>
              <CardTitle className="flex cursor-help items-center gap-2" title="Knowledge with no active connections — effectively invisible and at risk of being lost">
                <Eye className="h-4 w-4 text-health-red" />
                Knowledge Black Holes
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 max-h-52 overflow-y-auto no-scrollbar">
              {blackHoles?.length ? blackHoles.slice(0, 8).map((b) => (
                <div key={b.knowledge_id} className="flex items-start justify-between gap-2 rounded-lg bg-aion-bg p-2.5">
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-aion-ink truncate">{b.title}</p>
                    <p className="text-2xs text-aion-ink-faint">{b.domain}</p>
                  </div>
                  <Badge variant="danger" className="shrink-0">isolated</Badge>
                </div>
              )) : (
                <p className="text-sm text-health-green text-center py-4">No black holes detected</p>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.26, ease: EASE }}>
          <Card className="border-l-2 border-l-health-green">
            <CardHeader>
              <CardTitle className="flex cursor-help items-center gap-2" title="Departments or people generating a disproportionate share of new knowledge and ideas">
                <Lightbulb className="h-4 w-4 text-health-yellow" />
                Innovation Centers
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 max-h-52 overflow-y-auto no-scrollbar">
              {innovationCenters?.length ? innovationCenters.slice(0, 8).map((c) => (
                <div key={c.center_id} className="flex items-center justify-between rounded-lg bg-aion-bg p-2.5">
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-aion-ink truncate">{c.title}</p>
                    <p className="text-2xs text-aion-ink-faint">{c.domain}</p>
                  </div>
                  <span className="text-xs font-bold text-health-green tabular-nums">{c.innovation_score}</span>
                </div>
              )) : (
                <p className="text-sm text-aion-ink-muted text-center py-4">No data available</p>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Knowledge Flow + Forecast */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, ease: EASE }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex cursor-help items-center gap-2" title="Strength and health of knowledge exchange between departments">
                <ArrowRight className="h-4 w-4 text-aion-violet" />
                Department Knowledge Flow
              </CardTitle>
            </CardHeader>
            <CardContent className="max-h-64 space-y-2 overflow-y-auto no-scrollbar">
              {flowData?.length ? flowData.map((flow, i) => (
                <div key={i} className="rounded-lg bg-aion-bg p-2.5">
                  <div className="mb-1.5 flex items-center justify-between gap-2 text-xs">
                    <span className="flex min-w-0 items-center gap-1.5 text-aion-ink">
                      <span className="truncate">{truncate(flow.from_department, 14)}</span>
                      <ArrowRight className="h-3 w-3 shrink-0 text-aion-ink-faint" />
                      <span className="truncate">{truncate(flow.to_department, 14)}</span>
                    </span>
                    <Badge variant={flow.health_status === "healthy" ? "success" : flow.health_status === "warning" ? "warning" : "danger"} className="shrink-0">
                      {flow.health_status}
                    </Badge>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-aion-surface2">
                    <motion.div
                      className={cn(
                        "h-full rounded-full",
                        flow.health_status === "healthy" ? "bg-health-green" : flow.health_status === "warning" ? "bg-health-yellow" : "bg-health-red",
                      )}
                      initial={{ width: 0 }}
                      animate={{ width: `${(flow.flow_strength / maxFlow) * 100}%` }}
                      transition={{ duration: 0.7, delay: i * 0.04, ease: EASE }}
                    />
                  </div>
                </div>
              )) : (
                <p className="text-sm text-aion-ink-muted text-center py-6">No flow data available</p>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.34, ease: EASE }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-aion-violet" />
                Health Forecast
              </CardTitle>
            </CardHeader>
            <CardContent>
              {forecast ? (
                <div className="relative">
                  <div className="absolute left-[10px] top-3 bottom-3 w-px bg-aion-border" />
                  <div className="space-y-3">
                    {[
                      { key: "3_month_forecast" as const, label: "3 Months" },
                      { key: "6_month_forecast" as const, label: "6 Months" },
                      { key: "12_month_forecast" as const, label: "12 Months" },
                    ].map(({ key, label }) => {
                      const period = forecast[key];
                      return (
                        <div key={key} className="relative flex gap-3 pl-0.5">
                          <div className="relative z-10 mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-aion-violet-tint border border-aion-violet-border">
                            <Activity className="h-2.5 w-2.5 text-aion-violet" />
                          </div>
                          <div className="min-w-0 flex-1 rounded-lg border border-aion-border bg-aion-bg p-3">
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-xs font-semibold text-aion-ink">{label}</span>
                              <span className="text-2xs text-aion-ink-faint">{period.date}</span>
                            </div>
                            <p className="text-xs text-health-yellow mb-1">{period.projected_health_change}</p>
                            <p className="text-2xs text-aion-ink-faint">Confidence: {Math.round(period.confidence * 100)}%</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  {[0, 1, 2].map((i) => <Skeleton key={i} className="h-16 w-full rounded-lg" />)}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
