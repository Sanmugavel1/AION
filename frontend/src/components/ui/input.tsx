import * as React from "react";
import { cn } from "@/lib/utils/cn";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, type, ...props }, ref) => (
  <input
    type={type}
    ref={ref}
    className={cn(
      "flex h-9 w-full rounded-lg border border-aion-border bg-aion-surface",
      "px-3 py-1 text-sm text-aion-ink placeholder:text-aion-ink-faint",
      "transition-colors",
      "focus:outline-none focus:border-aion-accent focus:ring-1 focus:ring-aion-accent/30",
      "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-aion-surface2",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";

export { Input };
