"use client";
import { Bell, Home, LogOut, User } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useAuthStore } from "@/lib/stores/auth.store";
import { useLogout } from "@/lib/hooks/use-auth";
import { useIntelligenceIndex } from "@/lib/hooks/use-intelligence";
import { useDiseaseScan } from "@/lib/hooks/use-diseases";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";
import { OIISnapshot } from "@/types";

function OrgHealthBadge() {
  const { data } = useIntelligenceIndex();
  const snap = data as OIISnapshot | undefined;
  if (!snap?.overall_health) return null;

  const pct = Math.round(snap.overall_health * 100);
  const color = pct >= 75 ? "text-health-green" : pct >= 50 ? "text-health-yellow" : "text-health-red";

  return (
    <div className="flex items-center gap-2 rounded-md border border-aion-border bg-aion-surface2 px-3 py-1">
      <span className="text-2xs font-medium text-aion-ink-muted uppercase tracking-wider">Org Health</span>
      <span className={cn("text-sm font-bold tabular-nums", color)}>{pct}%</span>
    </div>
  );
}

function DiseaseAlertBadge() {
  const { data } = useDiseaseScan();
  const critical = data?.critical_diseases ?? 0;
  const warning = data?.warning_diseases ?? 0;

  if (critical === 0 && warning === 0) return null;

  return (
    <Link href="/dashboard/diseases">
      <div className={cn(
        "flex items-center gap-1.5 rounded-md border px-3 py-1 cursor-pointer transition-all hover:brightness-95",
        critical > 0
          ? "border-health-red-border bg-health-red-tint text-health-red"
          : "border-health-yellow-border bg-health-yellow-tint text-health-yellow",
      )}>
        <div className={cn("h-1.5 w-1.5 rounded-full", critical > 0 ? "bg-health-red animate-pulse" : "bg-health-yellow")} />
        <span className="text-xs font-medium">
          {critical > 0 ? `${critical} Critical` : `${warning} Warning`}
        </span>
      </div>
    </Link>
  );
}

export function TopNav() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();

  return (
    <header className="relative flex h-16 items-center justify-between overflow-hidden border-b border-aion-border bg-aion-surface/85 px-6 backdrop-blur-xl">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-60"
        style={{ background: "radial-gradient(ellipse 40% 100% at 15% 50%, rgba(232,184,75,0.08), transparent)" }}
      />
      {/* Left: home + breadcrumb / status */}
      <div className="flex items-center gap-3">
        <Link href="/" title="Back to home page">
          <motion.div
            whileHover={{ scale: 1.06, backgroundColor: "rgba(232,184,75,0.10)" }}
            whileTap={{ scale: 0.94 }}
            transition={{ type: "spring", stiffness: 400, damping: 20 }}
            className="flex h-9 w-9 items-center justify-center rounded-md border border-aion-border bg-aion-surface2 cursor-pointer"
            aria-label="Back to home page"
          >
            <Home className="h-4 w-4 text-aion-ink-muted" />
          </motion.div>
        </Link>
        <div className="h-5 w-px bg-aion-border" />
        <OrgHealthBadge />
        <DiseaseAlertBadge />
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" aria-label="Notifications">
          <Bell className="h-4 w-4 text-aion-ink-muted" />
        </Button>

        <div className="flex items-center gap-2 rounded-md border border-aion-border bg-aion-surface2 px-3 py-1.5">
          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-aion-accent-tint ring-1 ring-aion-accent-border">
            <User className="h-3.5 w-3.5 text-aion-accent" />
          </div>
          <div className="hidden sm:block">
            <p className="text-xs font-medium text-aion-ink leading-none">{user?.email?.split("@")[0] ?? "User"}</p>
            <p className="text-2xs text-aion-ink-muted capitalize mt-0.5">{user?.role?.replace("_", " ")}</p>
          </div>
        </div>

        <Button variant="ghost" size="icon" onClick={logout} aria-label="Logout">
          <LogOut className="h-4 w-4 text-aion-ink-muted hover:text-health-red transition-colors" />
        </Button>
      </div>
    </header>
  );
}
