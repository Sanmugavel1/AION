"use client";
import { motion } from "framer-motion";
import { Clock, AlertTriangle, BarChart2, Layers, ListChecks } from "lucide-react";
import { useDecayReport, useDecayEntropy, useDecayForgotten } from "@/lib/hooks/use-decay";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils/cn";

const EASE = [0.16, 1, 0.3, 1] as const;

/** Higher composite entropy = more disorder = worse, so the color scale is inverted vs. a normal health score. */
function entropySeverity(v: number) {
  if (v > 0.6) return { text: "text-health-red", bg: "bg-health-red" };
  if (v > 0.4) return { text: "text-health-yellow", bg: "bg-health-yellow" };
  return { text: "text-health-green", bg: "bg-health-green" };
}

export default function DecayPage() {
  const { data: report } = useDecayReport();
  const { data: entropy, isLoading: entropyLoading } = useDecayEntropy();
  const { data: forgotten } = useDecayForgotten();

  // Domain concentration ranking — larger share of knowledge concentrated in one
  // domain is a bigger decay/isolation risk if that domain also has few owners.
  const domainRanking = entropy?.domain_distribution
    ? Object.entries(entropy.domain_distribution)
        .map(([domain, count]) => ({ domain, count }))
        .sort((a, b) => b.count - a.count)
    : [];
  const maxDomainCount = domainRanking.length ? Math.max(...domainRanking.map((d) => d.count)) : 1;

  const entropyPct = entropy ? Math.round(entropy.composite_entropy_score * 100) : 0;
  const entropySev = entropySeverity(entropy?.composite_entropy_score ?? 0);

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="page-title flex items-center gap-2">
          <Clock className="h-5 w-5 text-aion-teal" />
          Knowledge Decay Engine
        </h1>
        <p className="page-subtitle mt-1">Entropy measurement, isolation analysis, and forgotten-knowledge recovery</p>
      </motion.div>

      {/* Hero: composite entropy score + domain concentration ranking */}
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05, duration: 0.5, ease: EASE }}>
        <Card className="relative overflow-hidden p-0 shadow-glow-teal">
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-aion-teal via-aion-accent to-aion-teal" />
          <Clock className="pointer-events-none absolute -right-6 -top-6 h-40 w-40 text-aion-ink opacity-[0.03]" />
          <div className="grid grid-cols-1 lg:grid-cols-5">
            <div className="flex flex-col justify-center gap-6 border-b border-aion-border p-8 lg:col-span-2 lg:border-b-0 lg:border-r">
              <div>
                <p
                  className="mb-2 cursor-help text-xs font-semibold uppercase tracking-wide text-aion-ink-faint"
                  title="Shannon entropy across all knowledge domains, weighted by isolation — higher means more disorder and risk of loss"
                >
                  Composite Entropy Score
                </p>
                {entropyLoading ? (
                  <Skeleton className="h-14 w-28" />
                ) : (
                  <div className="flex items-end gap-3">
                    <span className={cn("text-6xl font-bold tabular-nums leading-none", entropySev.text)}>
                      {entropy ? entropyPct : "—"}
                    </span>
                    <span className="mb-1.5 text-lg text-aion-ink-faint">%</span>
                  </div>
                )}
                {entropy?.health_interpretation && (
                  <p className="mt-2 text-xs text-aion-ink-muted">{entropy.health_interpretation}</p>
                )}
              </div>
              <div className="grid grid-cols-3 gap-4 border-t border-aion-border pt-5">
                <div className="cursor-help" title="Knowledge items with no incoming or outgoing connections to the rest of the graph">
                  <p className="text-2xs font-medium text-aion-ink-faint">Isolated Items</p>
                  <p className="text-base font-semibold text-aion-ink tabular-nums">{report?.summary.isolated_items ?? "—"}</p>
                </div>
                <div className="cursor-help" title="Critical knowledge documented or held by exactly one person — a single point of failure">
                  <p className="text-2xs font-medium text-aion-ink-faint">Single-Owner</p>
                  <p className="text-base font-semibold text-health-yellow tabular-nums">{report?.summary.single_owner_critical ?? "—"}</p>
                </div>
                <div className="cursor-help" title="Share of total knowledge items that are isolated from the rest of the graph">
                  <p className="text-2xs font-medium text-aion-ink-faint">Isolation</p>
                  <p className="text-base font-semibold text-aion-ink tabular-nums">
                    {entropy ? (entropy.isolation_ratio * 100).toFixed(1) + "%" : "—"}
                  </p>
                </div>
              </div>
            </div>

            <div className="p-6 lg:col-span-3">
              <div className="mb-4 flex items-center justify-between">
                <p
                  className="flex cursor-help items-center gap-2 text-sm font-semibold text-aion-ink"
                  title="Domains where knowledge is heavily concentrated are riskier — a single gap can take out a large share of institutional knowledge"
                >
                  <BarChart2 className="h-4 w-4 text-aion-teal" />
                  Domain Concentration Risk
                </p>
                {entropy && (
                  <span className="text-2xs text-aion-ink-faint">
                    Domain entropy: <span className="text-aion-ink font-semibold">{entropy.domain_entropy_bits?.toFixed(2)} bits</span>
                  </span>
                )}
              </div>
              {entropyLoading ? (
                <Skeleton className="h-48 w-full rounded-lg" />
              ) : domainRanking.length ? (
                <div
                  className="space-y-3 rounded-lg p-3 -m-3"
                  style={{
                    backgroundImage: "radial-gradient(rgba(15,23,42,0.035) 1px, transparent 1px)",
                    backgroundSize: "16px 16px",
                  }}
                >
                  {domainRanking.slice(0, 8).map((d, i) => {
                    const ratio = d.count / maxDomainCount;
                    const sev = ratio > 0.7 ? "text-health-red" : ratio > 0.4 ? "text-health-yellow" : "text-health-green";
                    const barBg = ratio > 0.7 ? "bg-health-red" : ratio > 0.4 ? "bg-health-yellow" : "bg-health-green";
                    return (
                      <div key={d.domain}>
                        <div className="mb-1.5 flex items-center justify-between text-2xs text-aion-ink-muted">
                          <span className="truncate">{i + 1}. {d.domain}</span>
                          <span className={cn("font-semibold shrink-0 tabular-nums", sev)}>{d.count}</span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-aion-surface2">
                          <motion.div
                            className={cn("h-full rounded-full", barBg)}
                            initial={{ width: 0 }}
                            animate={{ width: `${ratio * 100}%` }}
                            transition={{ duration: 0.8, delay: 0.1 + i * 0.05, ease: EASE }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-center text-sm text-aion-ink-muted py-12">No entropy data available</p>
              )}
            </div>
          </div>
        </Card>
      </motion.div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        {/* Single-owner critical — weighted heavier, it's the higher-severity of the two */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15, ease: EASE }} className="lg:col-span-7">
          <Card>
            <CardHeader>
              <CardTitle className="flex cursor-help items-center gap-2" title="Ranked by risk: how much health would be lost if the sole owner became unavailable">
                <Layers className="h-4 w-4 text-aion-teal" />
                Single-Owner Critical Knowledge
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 max-h-72 overflow-y-auto no-scrollbar">
              {report?.single_owner_critical?.length ? (
                report.single_owner_critical.map((item, i) => {
                  const risk = 1 - (item.health_score ?? 0.5);
                  const pct = Math.round(risk * 100);
                  return (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.2 + i * 0.03, ease: EASE }}
                      className="space-y-1"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-aion-ink font-medium truncate max-w-[220px]">{item.label}</span>
                        <span className={cn("tabular-nums font-semibold shrink-0",
                          risk >= 0.7 ? "text-health-red" : risk >= 0.4 ? "text-health-yellow" : "text-health-green"
                        )}>
                          {pct}% risk
                        </span>
                      </div>
                      <Progress value={pct} className="h-1.5"
                        indicatorColor={risk >= 0.7 ? "bg-health-red" : risk >= 0.4 ? "bg-health-yellow" : "bg-health-green"}
                      />
                    </motion.div>
                  );
                })
              ) : (
                <p className="text-sm text-aion-ink-muted text-center py-8">No single-owner critical items detected</p>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Forgotten knowledge */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, ease: EASE }} className="lg:col-span-5">
          <Card>
            <CardHeader>
              <CardTitle className="flex cursor-help items-center gap-2" title="Knowledge items that haven't been accessed, referenced, or updated in a long time">
                <AlertTriangle className="h-4 w-4 text-health-red" />
                Forgotten Knowledge
                {forgotten?.count != null && (
                  <Badge variant="danger">{forgotten.count}</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="max-h-72 space-y-2 overflow-y-auto no-scrollbar">
              {forgotten?.forgotten_items?.length ? (
                forgotten.forgotten_items.slice(0, 12).map((item: any, i: number) => {
                  const border = item.health_color === "red" ? "border-l-health-red" : item.health_color === "yellow" ? "border-l-health-yellow" : "border-l-health-green";
                  return (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.25 + i * 0.02, ease: EASE }}
                      className={cn("flex items-center justify-between gap-3 rounded-lg border border-aion-border border-l-2 bg-aion-bg px-3.5 py-2.5", border)}
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-medium text-aion-ink truncate">{item.label}</p>
                        <p className="text-2xs text-aion-ink-faint mt-0.5 truncate">{item.tooltip}</p>
                      </div>
                      <Badge variant={item.health_color === "red" ? "danger" : item.health_color === "yellow" ? "warning" : "secondary"} className="shrink-0">
                        {item.health_color === "red" ? "Critical" : item.health_color === "yellow" ? "Warning" : "Healthy"}
                      </Badge>
                    </motion.div>
                  );
                })
              ) : (
                <p className="text-center text-sm text-aion-ink-muted py-8">No forgotten knowledge items detected</p>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Recommendations */}
      {report?.recommendations?.length ? (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.28, ease: EASE }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <ListChecks className="h-4 w-4 text-aion-teal" />
                Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {report.recommendations.map((r, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.32 + i * 0.04, ease: EASE }}
                  className="flex items-start gap-3 rounded-lg bg-aion-bg px-3 py-2.5"
                >
                  <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-aion-teal-tint text-2xs font-bold text-aion-teal">
                    {i + 1}
                  </div>
                  <p className="text-xs text-aion-ink">{r}</p>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      ) : null}
    </div>
  );
}
