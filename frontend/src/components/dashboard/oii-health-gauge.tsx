"use client";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils/cn";

interface OIIHealthGaugeProps {
  value: number; // 0-1
  size?: "sm" | "md" | "lg";
}

export function OIIHealthGauge({ value, size = "md" }: OIIHealthGaugeProps) {
  const pct = Math.round(value * 100);
  const radius = size === "lg" ? 52 : size === "md" ? 40 : 28;
  const stroke = size === "lg" ? 6 : 5;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (pct / 100) * circumference;

  const color = pct >= 75 ? "#3FCF8E" : pct >= 50 ? "#F5A623" : "#F45B5B";
  const svgSize = (radius + stroke) * 2 + 8;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: svgSize, height: svgSize }}>
        <svg width={svgSize} height={svgSize} className="-rotate-90">
          {/* Background ring */}
          <circle
            cx={svgSize / 2}
            cy={svgSize / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.10)"
            strokeWidth={stroke}
          />
          {/* Progress ring */}
          <motion.circle
            cx={svgSize / 2}
            cy={svgSize / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: dashOffset }}
            transition={{ duration: 1.2, ease: "easeOut" }}
          />
        </svg>
        {/* Center value */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className={cn(
              "font-bold tabular-nums",
              size === "lg" ? "text-3xl" : size === "md" ? "text-2xl" : "text-base",
            )}
            style={{ color }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            {pct}
          </motion.span>
          <span className="text-2xs text-muted-foreground -mt-0.5">/ 100</span>
        </div>
      </div>
    </div>
  );
}
