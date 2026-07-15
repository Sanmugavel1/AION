"use client";
import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Users, Search, ChevronRight, Dna, AlertTriangle, Plus, ShieldCheck, Network } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { graphApi } from "@/lib/api";
import { GraphNode } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils/cn";

const HEALTH_TEXT: Record<string, string> = {
  green: "text-health-green",
  yellow: "text-health-yellow",
  red: "text-health-red",
};

const RISK_BADGE_MAP: Record<string, "critical" | "warning" | "success"> = {
  red: "critical",
  yellow: "warning",
  green: "success",
};

function initialsOf(label?: string) {
  return label?.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase() ?? "??";
}

function RiskBadge({ color }: { color: string }) {
  const label = color === "red" ? "High Risk" : color === "yellow" ? "Medium Risk" : "Low Risk";
  const variant = RISK_BADGE_MAP[color] ?? "secondary";
  return <Badge variant={variant}>{label}</Badge>;
}

function SpotlightCard({ node, index }: { node: GraphNode; index: number }) {
  const riskPct = Math.round((1 - (node.health_score ?? 0.5)) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ delay: index * 0.06, duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
    >
      <Link href={`/dashboard/ocsie/${node.id}`} className="group">
        <Card className="relative cursor-pointer overflow-hidden border-health-red-border transition-shadow duration-200 hover:shadow-glow-rose">
          <div className="pointer-events-none absolute inset-y-0 left-0 w-1 bg-health-red" />
          <CardContent className="relative flex items-center gap-5 p-5">
            <div className="relative flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-health-red-tint text-base font-bold text-health-red ring-2 ring-health-red-border">
              {initialsOf(node.label)}
              <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-health-red text-white">
                <AlertTriangle className="h-2.5 w-2.5" />
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-aion-ink">{node.label}</p>
              <p className="truncate text-xs text-aion-ink-muted">{node.tooltip}</p>
              <div className="mt-2 flex items-center gap-2">
                <Progress value={riskPct} className="h-1.5 flex-1" indicatorColor="bg-health-red" />
                <span className="text-xs font-bold tabular-nums text-health-red">{riskPct}%</span>
              </div>
            </div>
            <ChevronRight className="h-4 w-4 shrink-0 text-aion-ink-faint transition-colors group-hover:text-health-red" />
          </CardContent>
        </Card>
      </Link>
    </motion.div>
  );
}

function PersonRow({ node, index }: { node: GraphNode; index: number }) {
  const initials = initialsOf(node.label);
  const riskPct = Math.round((1 - (node.health_score ?? 0.5)) * 100);
  const barColor = node.health_color === "red" ? "bg-health-red" : node.health_color === "yellow" ? "bg-health-yellow" : "bg-health-green";
  const textColor = HEALTH_TEXT[node.health_color] ?? "text-aion-ink";
  const avatarBg = node.health_color === "red" ? "bg-health-red-tint text-health-red" : node.health_color === "yellow" ? "bg-health-yellow-tint text-health-yellow" : "bg-aion-rose-tint text-aion-rose";

  return (
    <motion.tr
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: Math.min(index * 0.015, 0.3), duration: 0.2 }}
      className="group cursor-pointer border-b border-aion-border last:border-0 hover:bg-aion-surface2"
    >
      <td className="p-0">
        <Link href={`/dashboard/ocsie/${node.id}`} className="flex items-center gap-3 px-4 py-3">
          <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold", avatarBg)}>
            {initials}
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-aion-ink">{node.label}</p>
            <p className="truncate text-xs text-aion-ink-muted">{node.tooltip}</p>
          </div>
        </Link>
      </td>
      <td className="px-4 py-3 text-xs text-aion-ink-muted">
        <span className="flex items-center gap-1">
          <Network className="h-3 w-3" /> {node.connection_count}
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <Progress value={riskPct} className="h-1.5 w-20" indicatorColor={barColor} />
          <span className={cn("w-9 text-xs font-semibold tabular-nums", textColor)}>{riskPct}%</span>
        </div>
      </td>
      <td className="px-4 py-3"><RiskBadge color={node.health_color} /></td>
      <td className="w-8 px-4 py-3 text-right">
        <ChevronRight className="ml-auto h-4 w-4 text-aion-ink-faint opacity-0 transition-opacity group-hover:opacity-100" />
      </td>
    </motion.tr>
  );
}

export default function OCSIEPage() {
  const [search, setSearch] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["graph", "nodes", "Person"],
    queryFn: () => graphApi.getNodes({ node_type: "Person", limit: 100 }),
    staleTime: 5 * 60 * 1000,
  });

  const people: GraphNode[] = data?.nodes ?? [];

  const filtered = useMemo(
    () => people.filter((e) =>
      !search || e.label?.toLowerCase().includes(search.toLowerCase()) || e.tooltip?.toLowerCase().includes(search.toLowerCase()),
    ),
    [people, search],
  );

  const highRiskPeople = useMemo(
    () => [...filtered].filter((e) => e.health_color === "red")
      .sort((a, b) => (a.health_score ?? 0.5) - (b.health_score ?? 0.5))
      .slice(0, 3),
    [filtered],
  );
  const highRiskIds = new Set(highRiskPeople.map((p) => p.id));
  const rest = filtered.filter((p) => !highRiskIds.has(p.id));
  const highRisk = filtered.filter((e) => e.health_color === "red").length;

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-aion-rose-tint text-aion-rose">
              <Dna className="h-4 w-4" />
            </span>
            Organizational Continuity & Succession Intelligence Engine
          </h1>
          <p className="page-subtitle mt-1">Employee knowledge DNA — successor identification, continuity planning, transition management</p>
        </div>
        <div className="flex items-center gap-3">
          {highRisk > 0 && (
            <div className="flex items-center gap-2 rounded-md border border-health-red-border bg-health-red-tint px-4 py-1.5">
              <AlertTriangle className="h-4 w-4 text-health-red" />
              <span className="text-sm font-medium text-health-red">{highRisk} High Risk</span>
            </div>
          )}
          <Link href="/dashboard/setup?step=1">
            <Button size="sm">
              <Plus className="h-4 w-4" /> Add People
            </Button>
          </Link>
        </div>
      </motion.div>

      {/* Stats */}
      {!isLoading && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className="grid grid-cols-3 gap-3">
          {[
            { label: "Total People", value: people.length, color: "text-aion-accent", chip: "bg-aion-accent-tint", icon: Users },
            { label: "High Risk", value: highRisk, color: "text-health-red", chip: "bg-health-red-tint", icon: AlertTriangle },
            { label: "Healthy", value: people.filter((e) => e.health_color === "green").length, color: "text-health-green", chip: "bg-health-green-tint", icon: ShieldCheck },
          ].map((item) => (
            <Card key={item.label} className="metric-card flex-row items-center gap-3">
              <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg", item.chip)}>
                <item.icon className={cn("h-4 w-4", item.color)} />
              </div>
              <div className="flex flex-1 items-center justify-between">
                <span className="text-xs text-aion-ink-muted">{item.label}</span>
                <span className={cn("text-2xl font-bold tabular-nums", item.color)}>{item.value}</span>
              </div>
            </Card>
          ))}
        </motion.div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-aion-ink-faint" />
        <Input
          placeholder="Search by name or role…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-3 gap-4 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-40 rounded-lg" />)}
        </div>
      ) : filtered.length ? (
        <>
          {highRiskPeople.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-3.5 w-3.5 text-health-red" />
                <h2 className="text-sm font-semibold text-aion-ink">Requires Immediate Attention</h2>
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                {highRiskPeople.map((p, i) => <SpotlightCard key={p.id} node={p} index={i} />)}
              </div>
            </motion.div>
          )}

          {rest.length > 0 && (
            <div className="space-y-3">
              {highRiskPeople.length > 0 && <h2 className="text-sm font-semibold text-aion-ink">All People</h2>}
              <div className="data-table overflow-hidden rounded-lg border border-aion-border bg-aion-surface">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[560px] border-collapse">
                    <thead>
                      <tr className="border-b border-aion-border bg-aion-surface2">
                        <th className="px-4 py-2.5 text-left">Person</th>
                        <th className="px-4 py-2.5 text-left">Connections</th>
                        <th className="px-4 py-2.5 text-left">Continuity Risk</th>
                        <th className="px-4 py-2.5 text-left">Status</th>
                        <th className="px-4 py-2.5"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {rest.map((p, i) => <PersonRow key={p.id} node={p} index={i} />)}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </>
      ) : (
        <Card className="p-12 text-center">
          <Users className="mx-auto mb-3 h-12 w-12 text-aion-ink-faint" />
          <p className="text-sm text-aion-ink-muted">{search ? "No people match your search" : "No employee data available"}</p>
        </Card>
      )}
    </div>
  );
}
