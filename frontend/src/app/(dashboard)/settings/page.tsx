"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { Settings, User, Bell, Shield, Palette, Database } from "lucide-react";
import { useAuthStore } from "@/lib/stores/auth.store";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";
import { toast } from "sonner";

const SETTINGS_TABS = [
  { key: "profile", label: "Profile", icon: User },
  { key: "notifications", label: "Notifications", icon: Bell },
  { key: "security", label: "Security", icon: Shield },
  { key: "appearance", label: "Appearance", icon: Palette },
  { key: "system", label: "System", icon: Database },
] as const;

type Tab = (typeof SETTINGS_TABS)[number]["key"];

function Toggle({ checked, onChange, label, description }: { checked: boolean; onChange: (v: boolean) => void; label: string; description?: string }) {
  return (
    <div className="flex items-center justify-between gap-4 py-1">
      <div>
        <span className="text-sm text-aion-ink">{label}</span>
        {description && <p className="text-xs text-aion-ink-faint">{description}</p>}
      </div>
      <button
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative h-6 w-11 shrink-0 rounded-full transition-colors duration-200 cursor-pointer",
          checked ? "bg-aion-accent" : "bg-aion-surface2 border border-aion-border-strong"
        )}
      >
        <span className={cn(
          "absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform duration-200",
          checked ? "translate-x-5" : "translate-x-0"
        )} />
      </button>
    </div>
  );
}

function ProfileTab() {
  const user = useAuthStore((s) => s.user);
  const [displayName, setDisplayName] = useState(user?.email?.split("@")[0] ?? "");

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-aion-accent-tint text-xl font-bold text-aion-accent">
          {(user?.email?.[0] ?? "U").toUpperCase()}
        </div>
        <div>
          <p className="text-sm font-semibold text-aion-ink">{user?.email}</p>
          <Badge variant="secondary" className="mt-1 capitalize">{user?.role?.replace("_", " ") ?? "User"}</Badge>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <label className="text-xs text-aion-ink-muted">Display Name</label>
          <Input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <label className="text-xs text-aion-ink-muted">Email Address</label>
          <Input value={user?.email ?? ""} disabled />
        </div>
        <div className="space-y-1.5">
          <label className="text-xs text-aion-ink-muted">Organization ID</label>
          <Input value={user?.org_id ?? ""} disabled />
        </div>
        <div className="space-y-1.5">
          <label className="text-xs text-aion-ink-muted">Role</label>
          <Input value={user?.role ?? ""} disabled className="capitalize" />
        </div>
      </div>
      <Button onClick={() => toast.success("Profile updated")} size="sm">Save Changes</Button>
    </div>
  );
}

function NotificationsTab() {
  const [settings, setSettings] = useState({
    critical_alerts: true,
    disease_scan: true,
    healing_approved: false,
    weekly_briefing: true,
    simulation_complete: true,
    email_digest: false,
  });
  const toggle = (k: keyof typeof settings) => setSettings((s) => ({ ...s, [k]: !s[k] }));

  return (
    <div className="space-y-1 divide-y divide-aion-border">
      {Object.entries({
        critical_alerts: "Critical Disease Alerts",
        disease_scan: "Disease Scan Completed",
        healing_approved: "Healing Action Approved",
        weekly_briefing: "Weekly Board Briefing",
        simulation_complete: "Simulation Complete",
        email_digest: "Email Digest",
      }).map(([k, label]) => (
        <div key={k} className="py-3 first:pt-0">
          <Toggle checked={settings[k as keyof typeof settings]} onChange={() => toggle(k as keyof typeof settings)} label={label} />
        </div>
      ))}
      <div className="pt-4">
        <Button onClick={() => toast.success("Notification preferences saved")} size="sm">Save Preferences</Button>
      </div>
    </div>
  );
}

function SecurityTab() {
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");

  const handleChange = () => {
    if (newPw !== confirmPw) { toast.error("Passwords do not match"); return; }
    if (newPw.length < 8) { toast.error("Password must be at least 8 characters"); return; }
    toast.success("Password updated");
    setCurrentPw(""); setNewPw(""); setConfirmPw("");
  };

  return (
    <div className="space-y-4 max-w-md">
      <div className="space-y-1.5">
        <label className="text-xs text-aion-ink-muted">Current Password</label>
        <Input type="password" value={currentPw} onChange={(e) => setCurrentPw(e.target.value)} />
      </div>
      <div className="space-y-1.5">
        <label className="text-xs text-aion-ink-muted">New Password</label>
        <Input type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} />
      </div>
      <div className="space-y-1.5">
        <label className="text-xs text-aion-ink-muted">Confirm New Password</label>
        <Input type="password" value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)} />
      </div>
      <Button onClick={handleChange} size="sm">Update Password</Button>
      <div className="mt-8 rounded-lg border border-aion-border bg-aion-surface2 p-4 space-y-3">
        <p className="text-sm font-semibold text-aion-ink">Active Sessions</p>
        <div className="flex items-center justify-between text-xs">
          <span className="text-aion-ink-muted">Current session (this browser)</span>
          <Badge variant="success">Active</Badge>
        </div>
      </div>
    </div>
  );
}

function AppearanceTab() {
  const [density, setDensity] = useState("Default");
  const [reduceMotion, setReduceMotion] = useState(false);

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold text-aion-ink mb-1">Theme</p>
        <p className="text-xs text-aion-ink-muted mb-3">AION uses a fixed dark ink theme for consistency and a premium feel across your organization.</p>
        <div className="flex items-center gap-3 rounded-lg border border-aion-accent-border bg-aion-accent-tint px-4 py-3 w-fit">
          <div className="h-8 w-8 rounded-md border border-aion-border bg-aion-bg shadow-glow-accent" />
          <span className="text-sm font-medium text-aion-accent">AION Ink (active)</span>
        </div>
      </div>
      <div>
        <p className="text-sm font-semibold text-aion-ink mb-3">Display Density</p>
        <div className="flex gap-2">
          {["Compact", "Default", "Comfortable"].map((d) => (
            <button
              key={d}
              onClick={() => setDensity(d)}
              className={cn(
                "rounded-md border px-3 py-1.5 text-xs transition-colors cursor-pointer",
                density === d
                  ? "border-aion-accent-border bg-aion-accent-tint text-aion-accent font-medium"
                  : "border-aion-border bg-aion-surface text-aion-ink-muted hover:text-aion-ink hover:bg-aion-surface2"
              )}
            >
              {d}
            </button>
          ))}
        </div>
      </div>
      <Toggle checked={reduceMotion} onChange={setReduceMotion} label="Reduce Motion" description="Minimize animations across the dashboard" />
      <Button onClick={() => toast.success("Appearance saved")} size="sm">Save Appearance</Button>
    </div>
  );
}

function SystemTab() {
  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-aion-border bg-aion-surface2 p-4 space-y-2">
        <p className="text-sm font-semibold text-aion-ink">API Configuration</p>
        <div className="flex items-center justify-between text-xs text-aion-ink-muted">
          <span>Backend URL</span>
          <span className="font-mono text-aion-ink">{process.env.NEXT_PUBLIC_API_URL}</span>
        </div>
        <div className="flex items-center justify-between text-xs text-aion-ink-muted">
          <span>API Prefix</span>
          <span className="font-mono text-aion-ink">/api/v1</span>
        </div>
        <div className="flex items-center justify-between text-xs text-aion-ink-muted">
          <span>Status</span>
          <div className="flex items-center gap-1.5">
            <div className="h-1.5 w-1.5 rounded-full bg-health-green animate-pulse" />
            <span className="text-health-green font-medium">Connected</span>
          </div>
        </div>
      </div>
      <div className="rounded-lg border border-aion-border bg-aion-surface2 p-4 space-y-2">
        <p className="text-sm font-semibold text-aion-ink">Cache</p>
        <div className="flex items-center justify-between text-xs text-aion-ink-muted">
          <span>React Query cache</span>
          <Button variant="outline" size="sm" onClick={() => toast.success("Cache cleared")} className="h-6 text-xs">
            Clear Cache
          </Button>
        </div>
      </div>
      <div className="rounded-lg border border-health-red-border bg-health-red-tint p-4 space-y-2">
        <p className="text-sm font-semibold text-health-red">Danger Zone</p>
        <p className="text-xs text-aion-ink-muted">Permanently delete your account and all associated data</p>
        <Button variant="outline" size="sm" className="border-health-red-border text-health-red hover:bg-health-red-tint">
          Delete Account
        </Button>
      </div>
    </div>
  );
}

const TAB_CONTENT: Record<Tab, React.ComponentType> = {
  profile: ProfileTab,
  notifications: NotificationsTab,
  security: SecurityTab,
  appearance: AppearanceTab,
  system: SystemTab,
};

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("profile");
  const Content = TAB_CONTENT[tab];

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="page-title flex items-center gap-2">
          <Settings className="h-5 w-5 text-aion-accent" />
          Settings
        </h1>
        <p className="page-subtitle mt-1">Account, notifications, security, and system configuration</p>
      </motion.div>

      <div className="grid grid-cols-[200px_1fr] gap-8">
        {/* Sidebar nav — plain list, no card chrome. Only one real "surface" on this page. */}
        <nav className="h-fit space-y-0.5 border-r border-aion-border pr-2">
          {SETTINGS_TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={cn(
                "relative flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors duration-150 cursor-pointer",
                tab === key
                  ? "text-aion-accent font-medium"
                  : "text-aion-ink-muted hover:text-aion-ink hover:bg-aion-surface2"
              )}
            >
              {tab === key && <span className="absolute -left-2 top-1/2 h-5 w-[2px] -translate-y-1/2 rounded-full bg-brand-gradient" />}
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </button>
          ))}
        </nav>

        {/* Content */}
        <motion.div key={tab} initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }}>
          <Card className="relative overflow-hidden">
            {/* The one deliberate accent on this utility page — restrained on purpose. */}
            <div className="absolute inset-x-0 top-0 h-1 bg-brand-gradient" />
            {(() => {
              const WatermarkIcon = SETTINGS_TABS.find((t) => t.key === tab)?.icon ?? Settings;
              return <WatermarkIcon className="pointer-events-none absolute -right-4 -top-4 h-28 w-28 text-aion-ink opacity-[0.03]" />;
            })()}
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {(() => {
                  const Icon = SETTINGS_TABS.find((t) => t.key === tab)?.icon ?? Settings;
                  return <Icon className="h-4 w-4 text-aion-accent" />;
                })()}
                {SETTINGS_TABS.find((t) => t.key === tab)?.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Content />
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
