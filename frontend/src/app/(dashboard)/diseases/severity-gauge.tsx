"use client";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils/cn";

const EASE = [0.16, 1, 0.3, 1] as const;

/**
 * Radial severity gauge — used in place of a plain linear bar so the
 * disease panel reads like a real diagnostic/ops instrument.
 */
export function SeverityGauge({
  value,
  colorClass,
  colorHex,
  size = 64,
  strokeWidth = 5,
  delay = 0,
}: {
  value: number;
  colorClass: string;
  colorHex: string;
  size?: number;
  strokeWidth?: number;
  delay?: number;
}) {
  const clamped = Math.min(100, Math.max(0, value));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.10)"
          strokeWidth={strokeWidth}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colorHex}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: EASE, delay }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className={cn("font-mono font-bold tabular-nums", colorClass)} style={{ fontSize: size * 0.22 }}>
          {clamped}
        </span>
      </div>
    </div>
  );
}
