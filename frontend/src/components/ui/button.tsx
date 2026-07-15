"use client";
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import { motion, useMotionValue, useSpring, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils/cn";

const buttonVariants = cva(
  "relative inline-flex items-center justify-center gap-2 rounded-md text-sm font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 cursor-pointer select-none overflow-hidden",
  {
    variants: {
      variant: {
        default: "bg-aion-accent text-white hover:bg-aion-accent-hover",
        destructive: "bg-health-red text-white hover:brightness-110",
        outline: "border border-aion-border bg-aion-surface text-aion-ink hover:bg-aion-surface2 hover:border-aion-border-strong",
        ghost: "hover:bg-aion-surface2 text-aion-ink",
        link: "text-aion-accent underline-offset-4 hover:underline",
        glass: "bg-aion-surface2 border border-aion-border text-aion-ink hover:bg-aion-border/40",
        success: "bg-health-green text-white hover:brightness-110",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-7 rounded-md px-3 text-xs",
        lg: "h-11 rounded-md px-8 text-base",
        icon: "h-9 w-9",
        "icon-sm": "h-7 w-7",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
  /** Subtle mouse-follow "magnetic" lift. Off by default for dense UI (tables, toolbars). */
  magnetic?: boolean;
}

interface Ripple { id: number; x: number; y: number; size: number; }

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, disabled, children, magnetic, onMouseMove, onMouseLeave, onClick, ...props }, ref) => {
    const x = useMotionValue(0);
    const y = useMotionValue(0);
    const springX = useSpring(x, { stiffness: 300, damping: 20, mass: 0.5 });
    const springY = useSpring(y, { stiffness: 300, damping: 20, mass: 0.5 });
    const [ripples, setRipples] = React.useState<Ripple[]>([]);
    const rippleId = React.useRef(0);

    const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (magnetic) {
        const rect = e.currentTarget.getBoundingClientRect();
        x.set((e.clientX - rect.left - rect.width / 2) * 0.25);
        y.set((e.clientY - rect.top - rect.height / 2) * 0.35);
      }
      onMouseMove?.(e);
    };
    const handleMouseLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (magnetic) { x.set(0); y.set(0); }
      onMouseLeave?.(e);
    };
    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      const rect = e.currentTarget.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height) * 1.6;
      const id = rippleId.current++;
      setRipples((r) => [...r, { id, x: e.clientX - rect.left, y: e.clientY - rect.top, size }]);
      setTimeout(() => setRipples((r) => r.filter((rp) => rp.id !== id)), 650);
      onClick?.(e);
    };

    return (
      <motion.button
        ref={ref}
        style={magnetic ? { x: springX, y: springY } : undefined}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        whileTap={{ scale: 0.97 }}
        className={cn(buttonVariants({ variant, size }), className)}
        disabled={disabled || loading}
        {...(props as any)}
      >
        <AnimatePresence>
          {ripples.map((r) => (
            <motion.span
              key={r.id}
              initial={{ opacity: 0.35, scale: 0 }}
              animate={{ opacity: 0, scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.6, ease: "easeOut" }}
              className="pointer-events-none absolute rounded-full bg-white"
              style={{ left: r.x, top: r.y, width: r.size, height: r.size, marginLeft: -r.size / 2, marginTop: -r.size / 2 }}
            />
          ))}
        </AnimatePresence>
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        {children}
      </motion.button>
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
