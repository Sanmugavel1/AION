export function formatPercent(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatScore(value: number): string {
  return `${Math.round(value * 100)}`;
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function severityColor(severity: "critical" | "warning" | "healthy" | string): string {
  switch (severity) {
    case "critical": return "text-health-red";
    case "warning": return "text-health-yellow";
    case "healthy": return "text-health-green";
    default: return "text-muted-foreground";
  }
}

export function healthColorClass(color: "green" | "yellow" | "red" | string): string {
  switch (color) {
    case "green": return "text-health-green";
    case "yellow": return "text-health-yellow";
    case "red": return "text-health-red";
    default: return "text-muted-foreground";
  }
}

export function healthBgClass(color: "green" | "yellow" | "red" | string): string {
  switch (color) {
    case "green": return "bg-health-green/10 border-health-green/30";
    case "yellow": return "bg-health-yellow/10 border-health-yellow/30";
    case "red": return "bg-health-red/10 border-health-red/30";
    default: return "bg-muted border-border";
  }
}

export function riskSeverityColor(severity: "critical" | "high" | "medium" | "low" | string): string {
  switch (severity) {
    case "critical": return "text-red-500";
    case "high": return "text-orange-500";
    case "medium": return "text-yellow-500";
    case "low": return "text-green-500";
    default: return "text-muted-foreground";
  }
}

export function truncate(str: string, length = 60): string {
  return str.length > length ? `${str.slice(0, length)}…` : str;
}
