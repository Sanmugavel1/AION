"use client";
import { useMemo, useState } from "react";
import { motion, AnimatePresence, LayoutGroup } from "framer-motion";
import {
  Zap, CheckCircle2, XCircle, Plus, ChevronDown, Clock, Trophy,
  FileText, UserPlus, GraduationCap, Merge, Archive, Bell,
  ClipboardList, HelpCircle, BookOpen, Share2, MessageSquare, Target,
} from "lucide-react";
import {
  useHealingRecommendations,
  useApproveRecommendation,
  useRejectRecommendation,
  useGenerateRecommendations,
} from "@/lib/hooks/use-healing";
import { HealingAction, HealingActionType, HealingPriority } from "@/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import { formatRelativeTime } from "@/lib/utils/format";

const EASE = [0.16, 1, 0.3, 1] as const;

const STATUS_TABS = [
  { key: "pending", label: "Pending", icon: Clock },
  { key: "approved", label: "Approved", icon: CheckCircle2 },
  { key: "completed", label: "Completed", icon: Trophy },
  { key: "rejected", label: "Rejected", icon: XCircle },
] as const;

type StatusTab = (typeof STATUS_TABS)[number]["key"];

const PRIORITY_CONFIG: Record<HealingPriority, { variant: "danger" | "warning" | "secondary"; label: string; text: string; dot: string; bg: string; border: string }> = {
  critical: { variant: "danger", label: "Critical", text: "text-health-red", dot: "bg-health-red", bg: "bg-health-red-tint", border: "border-health-red-border" },
  high: { variant: "danger", label: "High", text: "text-health-red", dot: "bg-health-red", bg: "bg-health-red-tint", border: "border-health-red-border" },
  medium: { variant: "warning", label: "Medium", text: "text-health-yellow", dot: "bg-health-yellow", bg: "bg-health-yellow-tint", border: "border-health-yellow-border" },
  low: { variant: "secondary", label: "Low", text: "text-aion-ink-muted", dot: "bg-aion-ink-faint", bg: "bg-aion-surface2", border: "border-aion-border" },
};

const ACTION_TYPE_ICON: Record<HealingActionType, typeof FileText> = {
  create_sop: FileText,
  assign_mentor: UserPlus,
  schedule_training: GraduationCap,
  merge_docs: Merge,
  archive_files: Archive,
  notify_managers: Bell,
  generate_onboarding: ClipboardList,
  create_quiz: HelpCircle,
  update_wiki: BookOpen,
  knowledge_transfer: Share2,
};

const STATUS_STRIPE: Record<string, string> = {
  pending: "before:bg-aion-accent/60",
  approved: "before:bg-health-green",
  in_progress: "before:bg-aion-accent",
  completed: "before:bg-health-green",
  rejected: "before:bg-health-red/60",
  cancelled: "before:bg-aion-border-strong",
};

const EMPTY_STATE: Record<StatusTab, { icon: typeof Zap; message: string }> = {
  pending: { icon: Zap, message: "No pending actions — you're all caught up." },
  approved: { icon: CheckCircle2, message: "No approved actions yet." },
  completed: { icon: Trophy, message: "No completed healing workflows yet." },
  rejected: { icon: XCircle, message: "No rejected actions." },
};

function HealingActionCard({ rec, i }: { rec: HealingAction; i: number }) {
  const [expanded, setExpanded] = useState(false);
  const approve = useApproveRecommendation();
  const reject = useRejectRecommendation();
  const pc = PRIORITY_CONFIG[rec.priority];
  const TypeIcon = ACTION_TYPE_ICON[rec.action_type] ?? Zap;
  const isPending = rec.status === "pending";
  const isBusy = approve.isPending || reject.isPending;

  return (
    <motion.div layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.3, ease: EASE, delay: i * 0.03 }}>
      <Card
        className={cn(
          "relative overflow-hidden pl-0.5 before:absolute before:inset-y-0 before:left-0 before:w-[3px] before:content-['']",
          STATUS_STRIPE[rec.status] ?? "before:bg-aion-border-strong",
        )}
      >
        <div
          className="flex items-start gap-4 p-4 pl-5 cursor-pointer"
          onClick={() => setExpanded((e) => !e)}
        >
          <div className={cn("mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border", pc.bg, pc.border)}>
            <TypeIcon className={cn("h-4 w-4", pc.text)} />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-sm font-semibold text-aion-ink">{rec.title}</p>
              <Badge variant={pc.variant}>{pc.label}</Badge>
              <Badge variant="secondary" className="text-2xs">{rec.action_type.replace(/_/g, " ")}</Badge>
            </div>
            <p className="text-xs text-aion-ink-muted mt-1 line-clamp-2">{rec.description}</p>
            <div className="flex items-center gap-4 mt-2 text-2xs text-aion-ink-faint">
              {rec.estimated_impact && <span>Impact: <span className="text-aion-ink-muted">{rec.estimated_impact}</span></span>}
              {rec.created_at && <span>{formatRelativeTime(rec.created_at)}</span>}
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {isPending && (
              <>
                <Button
                  size="sm"
                  variant="success"
                  disabled={isBusy}
                  loading={approve.isPending}
                  onClick={(e) => { e.stopPropagation(); approve.mutate(rec.id); }}
                >
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Approve
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="border-health-red-border text-health-red hover:bg-health-red-tint"
                  disabled={isBusy}
                  loading={reject.isPending}
                  onClick={(e) => { e.stopPropagation(); reject.mutate({ id: rec.id }); }}
                >
                  <XCircle className="h-3.5 w-3.5" />
                  Reject
                </Button>
              </>
            )}
            {!isPending && (
              <Badge variant={rec.status === "completed" ? "success" : rec.status === "approved" ? "secondary" : "outline"} className="capitalize">
                {rec.status.replace(/_/g, " ")}
              </Badge>
            )}
            <ChevronDown className={cn("h-4 w-4 text-aion-ink-faint transition-transform duration-300", expanded && "rotate-180")} />
          </div>
        </div>

        <AnimatePresence initial={false}>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25, ease: EASE }}
              className="overflow-hidden"
            >
              <div className="border-t border-aion-border px-4 pb-4 pt-3 pl-5 space-y-3">
                {(rec as any).rationale && (
                  <div>
                    <p className="text-2xs text-aion-ink-faint uppercase tracking-wider mb-1 flex items-center gap-1.5">
                      <MessageSquare className="h-3 w-3" />
                      Reasoning
                    </p>
                    <p className="text-xs text-aion-ink leading-relaxed">{(rec as any).rationale}</p>
                  </div>
                )}
                {Array.isArray((rec as any).target_entities) && (rec as any).target_entities.length > 0 && (
                  <div>
                    <p className="text-2xs text-aion-ink-faint uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                      <Target className="h-3 w-3" />
                      Affected Entities
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {((rec as any).target_entities as string[]).map((e) => (
                        <span key={e} className="rounded-full border border-aion-border bg-aion-surface2 px-2.5 py-0.5 text-xs text-aion-ink">
                          {e}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
    </motion.div>
  );
}

export default function HealingPage() {
  const [tab, setTab] = useState<StatusTab>("pending");
  const { data, isLoading } = useHealingRecommendations(tab);
  const generate = useGenerateRecommendations();
  const empty = EMPTY_STATE[tab];

  const priorityCounts = useMemo(() => {
    const counts: Record<HealingPriority, number> = { critical: 0, high: 0, medium: 0, low: 0 };
    for (const rec of data?.recommendations ?? []) counts[rec.priority] = (counts[rec.priority] ?? 0) + 1;
    return counts;
  }, [data]);

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Zap className="h-5 w-5 text-aion-accent" />
            Self-Healing Protocol
          </h1>
          <p className="page-subtitle mt-1">AI-generated corrective actions — approve to trigger automated healing workflows</p>
        </div>
        <Button
          onClick={() => generate.mutate()}
          loading={generate.isPending}
          size="sm"
          className="border-0 bg-brand-gradient bg-[length:160%_100%] bg-left text-white shadow-glow-accent transition-[background-position,transform] duration-300 hover:bg-right hover:-translate-y-0.5"
        >
          <Plus className="h-4 w-4" />
          Generate Recommendations
        </Button>
      </motion.div>

      {/* Priority breakdown — plain readout, not another row of boxes */}
      {!isLoading && data?.recommendations?.length ? (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
          className="flex items-center gap-7 border-y border-aion-border py-3.5">
          {(["critical", "high", "medium", "low"] as HealingPriority[]).map((p, idx) => {
            const pc = PRIORITY_CONFIG[p];
            return (
              <div key={p} className={cn("flex items-center gap-2", idx > 0 && "border-l border-aion-border pl-7")}>
                <span className={cn("h-2 w-2 rounded-full", pc.dot)} />
                <span className={cn("text-xl font-bold tabular-nums", pc.text)}>{priorityCounts[p]}</span>
                <span className="text-xs text-aion-ink-muted">{pc.label}</span>
              </div>
            );
          })}
        </motion.div>
      ) : null}

      {/* Tabs — segmented control */}
      <LayoutGroup id="healing-tabs">
        <div className="flex gap-1 rounded-lg border border-aion-border bg-aion-surface2 p-1 w-fit">
          {STATUS_TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={cn(
                "relative flex items-center gap-1.5 rounded-md px-4 py-1.5 text-xs font-medium transition-colors duration-200 cursor-pointer",
                tab === t.key ? "text-aion-ink" : "text-aion-ink-muted hover:text-aion-ink",
              )}
            >
              {tab === t.key && (
                <motion.span
                  layoutId="healing-tab-pill"
                  className="absolute inset-0 rounded-md bg-aion-surface shadow-card"
                  transition={{ type: "spring", stiffness: 400, damping: 32 }}
                />
              )}
              <span className="relative flex items-center gap-1.5">
                <t.icon className="h-3.5 w-3.5" />
                {t.label}
                {t.key === "pending" && data?.total != null && data.total > 0 && (
                  <span className="ml-0.5 rounded-full bg-aion-accent-tint text-aion-accent px-1.5 py-0.5 text-2xs font-semibold">
                    {data.total}
                  </span>
                )}
              </span>
            </button>
          ))}
        </div>
      </LayoutGroup>

      {/* Actions list */}
      <AnimatePresence mode="wait">
        {isLoading ? (
          <motion.div key="loading" className="space-y-3" exit={{ opacity: 0 }}>
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-lg" />)}
          </motion.div>
        ) : data?.recommendations?.length ? (
          <motion.div key={tab} className="space-y-3">
            {data.recommendations.map((rec, i) => (
              <HealingActionCard key={rec.id} rec={rec} i={i} />
            ))}
          </motion.div>
        ) : (
          <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Card className="p-12 text-center">
              <empty.icon className="h-10 w-10 text-aion-ink-faint mx-auto mb-3" />
              <p className="text-sm text-aion-ink-muted">{empty.message}</p>
              {tab === "pending" && (
                <Button onClick={() => generate.mutate()} loading={generate.isPending} size="sm" className="mt-4">
                  Generate Recommendations
                </Button>
              )}
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
