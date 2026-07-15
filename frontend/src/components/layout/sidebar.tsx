"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity, Bot, Brain, Bug, Building2, ChevronLeft, ChevronRight, FlaskConical,
  GitBranch, HeartPulse, LayoutDashboard, PlayCircle, Settings, Sparkles,
  TrendingUp, Upload, User,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { AionLogo } from "@/components/ui/aion-logo";
import { useUIStore } from "@/lib/stores/ui.store";
import { useAuthStore } from "@/lib/stores/auth.store";

const navigation = [
  {
    section: "AI Advisor",
    items: [
      { label: "Ask Axon", href: "/dashboard/advisor", icon: Bot, permission: null },
      { label: "Live Demo Report", href: "/dashboard/demo", icon: PlayCircle, permission: null },
    ],
  },
  {
    section: "Intelligence",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard, permission: null },
      { label: "Org MRI", href: "/dashboard/mri", icon: Brain, permission: "read:intelligence" },
      { label: "Intelligence Index", href: "/dashboard/intelligence", icon: TrendingUp, permission: "read:intelligence" },
      { label: "Disease Panel", href: "/dashboard/diseases", icon: Bug, permission: "read:intelligence" },
      { label: "Decay Engine", href: "/dashboard/decay", icon: Activity, permission: "read:knowledge" },
    ],
  },
  {
    section: "People",
    items: [
      { label: "OCSIE", href: "/dashboard/ocsie", icon: User, permission: "read:ocsie" },
    ],
  },
  {
    section: "Actions",
    items: [
      { label: "Simulations", href: "/dashboard/simulation", icon: FlaskConical, permission: "run:simulation" },
      { label: "Self-Healing", href: "/dashboard/healing", icon: HeartPulse, permission: "read:healing" },
    ],
  },
  {
    section: "Board",
    items: [
      { label: "Board Advisor", href: "/dashboard/board", icon: Sparkles, permission: "view:board" },
    ],
  },
  {
    section: "Data",
    items: [
      { label: "Upload Documents", href: "/dashboard/upload", icon: Upload, permission: "write:knowledge" },
      { label: "Memory Graph", href: "/dashboard/graph", icon: GitBranch, permission: "read:graph" },
      { label: "Organization Setup", href: "/dashboard/setup", icon: Building2, permission: null },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const hasPermission = useAuthStore((s) => s.hasPermission);

  return (
    <motion.aside
      initial={false}
      animate={{ width: sidebarOpen ? 240 : 64 }}
      transition={{ duration: 0.25, ease: "easeInOut" }}
      className="relative flex h-screen flex-col bg-aion-sidebar overflow-hidden"
    >
      {/* Logo */}
      <div className="relative flex h-16 items-center border-b border-white/[0.06] px-4">
        <Link href="/dashboard" className="flex items-center gap-2.5 min-w-0">
          <AionLogo size={32} className="shrink-0 drop-shadow-[0_0_8px_rgba(232,184,75,0.45)]" />
          <AnimatePresence>
            {sidebarOpen && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto" }}
                exit={{ opacity: 0, width: 0 }}
                className="font-bold text-sm tracking-widest text-white whitespace-nowrap"
              >
                AION
              </motion.span>
            )}
          </AnimatePresence>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-3 no-scrollbar">
        {navigation.map((group) => {
          const visibleItems = group.items.filter(
            (item) => !item.permission || hasPermission(item.permission as never),
          );
          if (visibleItems.length === 0) return null;

          return (
            <div key={group.section} className="mb-2">
              <AnimatePresence>
                {sidebarOpen && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="px-4 pb-1 pt-2 text-2xs font-semibold uppercase tracking-widest text-aion-sidebar-text/50"
                  >
                    {group.section}
                  </motion.p>
                )}
              </AnimatePresence>

              {visibleItems.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
                const Icon = item.icon;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "sidebar-link mx-2 my-0.5",
                      isActive && "text-white",
                      !sidebarOpen && "justify-center px-0",
                    )}
                    title={!sidebarOpen ? item.label : undefined}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="sidebar-active-pill"
                        className="absolute inset-0 rounded-md bg-aion-sidebar-hover"
                        transition={{ type: "spring", stiffness: 420, damping: 34 }}
                      >
                        <div className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-full bg-aion-accent" />
                      </motion.div>
                    )}
                    <motion.span
                      whileHover={{ x: isActive ? 0 : 2 }}
                      transition={{ type: "spring", stiffness: 400, damping: 25 }}
                      className="relative z-10 flex items-center gap-3"
                    >
                      <Icon className={cn("h-4 w-4 shrink-0", isActive ? "text-aion-accent" : "text-aion-sidebar-text")} />
                      <AnimatePresence>
                        {sidebarOpen && (
                          <motion.span
                            initial={{ opacity: 0, width: 0 }}
                            animate={{ opacity: 1, width: "auto" }}
                            exit={{ opacity: 0, width: 0 }}
                            className="overflow-hidden whitespace-nowrap text-sm"
                          >
                            {item.label}
                          </motion.span>
                        )}
                      </AnimatePresence>
                    </motion.span>
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-white/[0.06] p-3">
        <Link
          href="/dashboard/settings"
          className={cn("sidebar-link", !sidebarOpen && "justify-center px-0")}
        >
          <Settings className="h-4 w-4 shrink-0 text-aion-sidebar-text" />
          <AnimatePresence>
            {sidebarOpen && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto" }}
                exit={{ opacity: 0, width: 0 }}
                className="overflow-hidden whitespace-nowrap text-sm"
              >
                Settings
              </motion.span>
            )}
          </AnimatePresence>
        </Link>

        {/* Collapse toggle */}
        <button
          onClick={toggleSidebar}
          className={cn(
            "sidebar-link mt-1 w-full",
            !sidebarOpen && "justify-center px-0",
          )}
          aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
          {sidebarOpen ? (
            <ChevronLeft className="h-4 w-4 shrink-0" />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0" />
          )}
          <AnimatePresence>
            {sidebarOpen && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto" }}
                exit={{ opacity: 0, width: 0 }}
                className="overflow-hidden whitespace-nowrap text-sm"
              >
                Collapse
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>
    </motion.aside>
  );
}
