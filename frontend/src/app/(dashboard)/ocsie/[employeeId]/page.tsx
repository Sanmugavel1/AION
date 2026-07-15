"use client";
import { use } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Dna, Shield, AlertTriangle, FileText, Compass, Sparkles } from "lucide-react";
import Link from "next/link";
import {
  useEmployeeProfile,
  useContinuityReport,
  useSuccessorRoadmap,
  useBusinessImpact,
} from "@/lib/hooks/use-ocsie";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import { formatCurrency } from "@/lib/utils/format";

function RiskRing({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const radius = 46;
  const stroke = 7;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (pct / 100) * circumference;
  const color = value >= 0.7 ? "#F45B5B" : value >= 0.4 ? "#F5A623" : "#3FCF8E";
  const svgSize = (radius + stroke) * 2 + 8;

  return (
    <div className="relative shrink-0" style={{ width: svgSize, height: svgSize }}>
      <svg width={svgSize} height={svgSize} className="-rotate-90">
        <circle cx={svgSize / 2} cy={svgSize / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.10)" strokeWidth={stroke} />
        <motion.circle
          cx={svgSize / 2} cy={svgSize / 2} r={radius} fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: dashOffset }}
          transition={{ duration: 1.1, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold tabular-nums" style={{ color }}>{pct}</span>
        <span className="-mt-0.5 text-2xs text-aion-ink-faint">risk</span>
      </div>
    </div>
  );
}

const ACCENT_TEXT: Record<string, string> = {
  "aion-accent": "text-aion-accent",
  "health-yellow": "text-health-yellow",
  "health-green": "text-health-green",
  "aion-insight": "text-aion-insight",
  "aion-rose": "text-aion-rose",
};

function SectionHeading({ icon: Icon, label, accent = "aion-accent" }: { icon: typeof Dna; label: string; accent?: keyof typeof ACCENT_TEXT }) {
  return (
    <CardTitle className="flex items-center gap-2">
      <span className={cn("flex h-6 w-6 items-center justify-center rounded-md bg-aion-surface2", ACCENT_TEXT[accent])}>
        <Icon className="h-3.5 w-3.5" />
      </span>
      {label}
    </CardTitle>
  );
}

export default function EmployeeProfilePage({ params }: { params: Promise<{ employeeId: string }> }) {
  const { employeeId } = use(params);
  const { data: profile, isLoading: profileLoading } = useEmployeeProfile(employeeId);
  const { data: report } = useContinuityReport(employeeId);
  const { data: roadmap } = useSuccessorRoadmap(employeeId);
  const { data: impact } = useBusinessImpact(employeeId);

  const employeeName = profile?.employee.name ?? "";
  const employeeRole = profile?.employee.role ?? "";
  const employeeDeptId = profile?.employee.department_id ?? "";
  const riskScore = profile?.knowledge_dna.knowledge_risk_score ?? 0;
  const riskColor = riskScore >= 0.7 ? "text-health-red" : riskScore >= 0.4 ? "text-health-yellow" : "text-health-green";
  const riskLabel = riskScore >= 0.7 ? "Critical" : riskScore >= 0.4 ? "Elevated" : "Stable";
  const primaryDomains = profile?.knowledge_dna.primary_domains ?? [];

  const initials = employeeName.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase() || "??";
  const successors = (profile?.risk_assessment.recommended_successors ?? []) as any[];

  return (
    <div className="space-y-6">
      <Link href="/dashboard/ocsie">
        <Button variant="ghost" size="sm" className="gap-2 text-aion-ink-muted hover:text-aion-ink">
          <ArrowLeft className="h-4 w-4" />
          Back to OCSIE
        </Button>
      </Link>

      {/* Hero — identity + risk */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        {profileLoading ? (
          <div className="flex items-center gap-4">
            <Skeleton className="h-16 w-16 rounded-full" />
            <div className="space-y-2">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-32" />
            </div>
          </div>
        ) : profile ? (
          <Card>
            <CardContent className="flex flex-col items-center gap-6 p-6 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-aion-rose-tint text-xl font-bold text-aion-rose shadow-glow-rose ring-2 ring-aion-rose-border">
                  {initials}
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-aion-ink">{employeeName}</h1>
                  <p className="text-sm text-aion-ink-muted">
                    {employeeRole}
                    {employeeDeptId && ` · Dept: ${employeeDeptId.slice(0, 8)}…`}
                  </p>
                  <div className="mt-2 flex items-center gap-2">
                    <Badge variant={riskScore >= 0.7 ? "critical" : riskScore >= 0.4 ? "warning" : "success"}>
                      {riskLabel} continuity risk
                    </Badge>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4 sm:border-l sm:border-aion-border sm:pl-6">
                <RiskRing value={riskScore} />
                <div className="w-32">
                  <p className="mb-1 text-2xs uppercase tracking-wider text-aion-ink-faint">Knowledge Risk</p>
                  <Progress value={riskScore * 100} className="h-1.5" indicatorColor={riskScore >= 0.7 ? "bg-health-red" : riskScore >= 0.4 ? "bg-health-yellow" : "bg-health-green"} />
                  <p className={cn("mt-2 text-xs font-medium", riskColor)}>{riskLabel}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="p-12 text-center">
            <p className="text-sm text-aion-ink-muted">Employee profile not found</p>
          </Card>
        )}
      </motion.div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Knowledge DNA */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card className="h-full">
            <CardHeader><SectionHeading icon={Dna} label="Knowledge DNA" accent="aion-rose" /></CardHeader>
            <CardContent className="space-y-2">
              {primaryDomains.length ? (
                primaryDomains.map((domain, i) => (
                  <div key={i} className="flex items-center gap-3 rounded-md border-l-2 border-aion-accent-border bg-aion-surface2 px-3 py-2">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-aion-accent-tint text-2xs font-bold text-aion-accent">{i + 1}</span>
                    <span className="flex-1 text-xs font-medium text-aion-ink">{domain}</span>
                    <Badge variant="secondary">Domain</Badge>
                  </div>
                ))
              ) : (
                <>
                  {profile?.knowledge_dna.technical_expertise &&
                    Object.entries(profile.knowledge_dna.technical_expertise).slice(0, 5).map(([k], i) => (
                      <div key={k} className="flex items-center gap-3 rounded-md border-l-2 border-aion-accent-border bg-aion-surface2 px-3 py-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-aion-accent-tint text-2xs font-bold text-aion-accent">{i + 1}</span>
                        <span className="flex-1 text-xs font-medium text-aion-ink">{k}</span>
                        <Badge variant="secondary">Technical</Badge>
                      </div>
                    ))}
                  {!profile?.knowledge_dna.technical_expertise && (
                    <p className="py-4 text-center text-sm text-aion-ink-muted">No knowledge areas on file</p>
                  )}
                </>
              )}
              {profile?.knowledge_dna.decision_style && (
                <div className="mt-3 rounded-md border border-aion-border bg-aion-surface2 p-3">
                  <p className="mb-1 text-2xs uppercase tracking-wider text-aion-ink-faint">Decision Style</p>
                  <p className="text-xs text-aion-ink">{profile.knowledge_dna.decision_style}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Business Impact */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <Card className="h-full">
            <CardHeader><SectionHeading icon={AlertTriangle} label="Business Impact Assessment" accent="health-yellow" /></CardHeader>
            <CardContent className="space-y-3">
              {impact ? (
                <>
                  <div className="rounded-md border border-health-red-border bg-health-red-tint p-3">
                    <p className="text-xs text-aion-ink-muted">Revenue at Risk</p>
                    <p className="text-xl font-bold tabular-nums text-health-red">
                      {formatCurrency(impact.revenue_risk_estimate_usd ?? 0)}
                    </p>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded-md bg-aion-surface2 p-2.5">
                      <p className="text-2xs text-aion-ink-faint">Recovery Time</p>
                      <p className="text-sm font-bold tabular-nums text-aion-ink">{impact.recovery_time_days ?? "—"}d</p>
                    </div>
                    <div className="rounded-md bg-aion-surface2 p-2.5">
                      <p className="text-2xs text-aion-ink-faint">Orphaned Items</p>
                      <p className="text-sm font-bold tabular-nums text-aion-ink">{impact.orphaned_knowledge_items ?? 0}</p>
                    </div>
                  </div>
                  <Badge
                    variant={impact.knowledge_loss_severity === "critical" ? "critical" : impact.knowledge_loss_severity === "high" ? "danger" : "warning"}
                    className="w-full justify-center"
                  >
                    {impact.knowledge_loss_severity} loss severity
                  </Badge>
                  {impact.immediate_actions?.length > 0 && (
                    <div className="space-y-1.5">
                      {impact.immediate_actions.map((action, i) => (
                        <div key={i} className="flex items-center gap-2 text-xs text-aion-ink-muted">
                          <div className="h-1.5 w-1.5 shrink-0 rounded-full bg-aion-accent" />
                          {action}
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div className="space-y-2">
                  {[0, 1, 2].map((i) => <Skeleton key={i} className="h-12 rounded-md" />)}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Successor readiness — roadmap + recommended successors */}
      {(roadmap || successors.length > 0) && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <SectionHeading icon={Compass} label="Successor Readiness" accent="health-green" />
                {roadmap && <Badge variant="secondary">{roadmap.estimated_full_competency_weeks}w to full competency</Badge>}
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              {successors.length > 0 && (
                <div className="space-y-2.5">
                  <p className="flex items-center gap-1.5 text-2xs font-semibold uppercase tracking-wider text-aion-ink-faint">
                    <Shield className="h-3 w-3" /> Recommended Successors
                  </p>
                  {successors.map((s: any, i: number) => {
                    const readiness = s?.readiness_score != null ? Math.round(s.readiness_score * 100) : null;
                    const rColor = readiness == null ? "bg-aion-border-strong" : readiness >= 70 ? "bg-health-green" : readiness >= 40 ? "bg-health-yellow" : "bg-health-red";
                    return (
                      <div key={s?.employee_id ?? i} className="flex items-center gap-4 rounded-md border border-aion-border bg-aion-surface2 p-3.5">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-aion-surface text-sm font-bold text-aion-ink">
                          {String(s?.name ?? "?")[0]}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-semibold text-aion-ink">{s?.name ?? s?.employee_id ?? "Unknown"}</p>
                          {readiness != null && (
                            <div className="mt-1.5 flex items-center gap-2">
                              <Progress value={readiness} className="h-1.5 flex-1" indicatorColor={rColor} />
                              <span className="w-9 shrink-0 text-right text-xs font-semibold tabular-nums text-aion-ink">{readiness}%</span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {roadmap && (
                <div className="space-y-2.5">
                  <p className="flex items-center gap-1.5 text-2xs font-semibold uppercase tracking-wider text-aion-ink-faint">
                    <Sparkles className="h-3 w-3" /> Onboarding Roadmap
                  </p>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                    {(["week_1", "week_2", "week_3"] as const).map((week, i) => (
                      <div key={week} className="space-y-3 rounded-md border border-aion-border bg-aion-surface2 p-4">
                        <div className="flex items-center gap-2">
                          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-aion-accent-tint text-xs font-bold text-aion-accent">
                            {i + 1}
                          </div>
                          <p className="text-xs font-semibold text-aion-ink">{roadmap[week].focus}</p>
                        </div>
                        <ul className="space-y-1.5">
                          {roadmap[week].tasks.map((task, ti) => (
                            <li key={ti} className="flex items-start gap-1.5 text-xs text-aion-ink-muted">
                              <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-aion-border-strong" />
                              {task}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Continuity Report — closing chapter, its own full-bleed band so the
          document ends with a visual shift rather than one more white card */}
      {report && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="-mx-6 border-y border-aion-border bg-aion-surface2 px-6 py-8"
        >
          <div className="mb-4 flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-aion-insight-tint text-aion-insight">
              <FileText className="h-4 w-4" />
            </span>
            <h2 className="text-base font-semibold text-aion-ink">Continuity Intelligence Report</h2>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {Object.entries(report.sections ?? {}).map(([key, value]) => (
              <div key={key} className="rounded-lg border border-aion-border bg-aion-surface p-4 shadow-card">
                <p className="mb-1 text-2xs uppercase tracking-wider text-aion-ink-faint">
                  {key.replace(/^\d+_/, "").replace(/_/g, " ")}
                </p>
                <p className="text-xs leading-relaxed text-aion-ink-muted">
                  {typeof value === "string"
                    ? value
                    : typeof value === "object" && value !== null
                    ? JSON.stringify(value).slice(0, 200) + "…"
                    : String(value)}
                </p>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
