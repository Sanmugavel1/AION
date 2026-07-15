import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils/cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-md px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-aion-accent-tint text-aion-accent border border-aion-accent-border",
        secondary: "bg-aion-surface2 text-aion-ink-muted border border-aion-border",
        success: "bg-health-green-tint text-health-green border border-health-green-border",
        warning: "bg-health-yellow-tint text-health-yellow border border-health-yellow-border",
        danger: "bg-health-red-tint text-health-red border border-health-red-border",
        outline: "border border-aion-border text-aion-ink",
        critical: "bg-health-red-tint text-health-red border border-health-red-border animate-pulse",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
