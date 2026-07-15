"use client";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils/cn";

const EASE = [0.16, 1, 0.3, 1] as const;

/** Fields that already appear as the node's headline / are too noisy to show as chips. */
const OMIT_KEYS = new Set(["step", "event", "timestamp", "parameters", "breakdown"]);

function prettyLabel(key: string) {
  return key.replace(/_/g, " ");
}

function prettyValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return value.toLocaleString();
  if (Array.isArray(value)) return value.length ? value.slice(0, 3).join(", ") + (value.length > 3 ? "…" : "") : "none";
  if (typeof value === "object") return Object.keys(value as object).length ? "…" : "—";
  return String(value);
}

/**
 * Renders the simulation's cascade_chain as a real connected flow — a
 * numbered, vertically-linked sequence of diagnostic steps, rather than a
 * raw JSON dump. Each step's payload shape varies by scenario type, so
 * fields are rendered generically as key/value chips beneath the headline.
 */
export function CascadeChain({ steps }: { steps: unknown[] }) {
  return (
    <div className="relative">
      {/* connecting spine — subtle accent→insight drift, since this is literally a journey through the graph */}
      <div className="absolute left-[15px] top-2 bottom-2 w-px bg-gradient-to-b from-aion-accent/40 via-aion-insight/25 to-transparent" />

      <div className="space-y-5">
        {steps.map((raw, i) => {
          const step = (raw && typeof raw === "object" ? raw : {}) as Record<string, unknown>;
          const headline = typeof step.event === "string" ? step.event : `Step ${i + 1}`;
          const entries = Object.entries(step).filter(([k]) => !OMIT_KEYS.has(k));

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -12 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.45, ease: EASE, delay: i * 0.1 }}
              className="relative flex items-start gap-3.5"
            >
              <motion.div
                initial={{ scale: 0.6, opacity: 0 }}
                whileInView={{ scale: 1, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 + 0.15, duration: 0.3, ease: EASE }}
                className={cn(
                  "relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                  "bg-aion-accent-tint text-aion-accent ring-1 ring-aion-accent-border text-xs font-bold tabular-nums",
                )}
              >
                {typeof step.step === "number" ? step.step : i + 1}
              </motion.div>

              <div className="min-w-0 flex-1 pt-1">
                <p className="text-sm font-medium text-aion-ink leading-snug">{headline}</p>
                {entries.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {entries.map(([k, v]) => (
                      <span
                        key={k}
                        className="rounded-md border border-aion-border bg-aion-surface2 px-2 py-1 text-2xs text-aion-ink-muted"
                      >
                        <span className="capitalize text-aion-ink-faint">{prettyLabel(k)}:</span>{" "}
                        <span className="text-aion-ink font-mono">{prettyValue(v)}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
