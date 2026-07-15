"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { Dna, BrainCircuit, Radio, Archive, Lightbulb } from "lucide-react";
import { DiseaseScanReport, DiseaseType } from "@/types";
import { cn } from "@/lib/utils/cn";

const DISEASE_LABELS: Record<DiseaseType, string> = {
  knowledge_cancer: "Knowledge Cancer",
  memory_alzheimers: "Memory Alzheimer's",
  communication_stroke: "Comm. Stroke",
  knowledge_obesity: "Knowledge Obesity",
  innovation_paralysis: "Innovation Paralysis",
};

const DISEASE_ICONS: Record<DiseaseType, typeof Dna> = {
  knowledge_cancer: Dna,
  memory_alzheimers: BrainCircuit,
  communication_stroke: Radio,
  knowledge_obesity: Archive,
  innovation_paralysis: Lightbulb,
};

const SEVERITY_STYLES = {
  critical: { border: "border-health-red-border", bg: "bg-health-red-tint", text: "text-health-red", dot: "bg-health-red animate-pulse" },
  warning: { border: "border-health-yellow-border", bg: "bg-health-yellow-tint", text: "text-health-yellow", dot: "bg-health-yellow" },
  healthy: { border: "border-health-green-border", bg: "bg-health-green-tint", text: "text-health-green", dot: "bg-health-green" },
} as const;

interface DiseaseAlertStripProps {
  data: DiseaseScanReport;
}

export function DiseaseAlertStrip({ data }: DiseaseAlertStripProps) {
  const diseases = Object.entries(data.diseases) as [DiseaseType, DiseaseScanReport["diseases"][DiseaseType]][];

  return (
    <div className="grid grid-cols-5 gap-3">
      {diseases.map(([type, disease], i) => {
        const Icon = DISEASE_ICONS[type];
        const style = SEVERITY_STYLES[disease.severity as keyof typeof SEVERITY_STYLES] ?? SEVERITY_STYLES.healthy;
        return (
          <motion.div
            key={type}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
          >
            <Link href="/dashboard/diseases">
              <div className={cn("card-surface-hover cursor-pointer p-3.5 border", style.border)}>
                <div className="flex items-start justify-between">
                  <div className={cn("flex h-7 w-7 items-center justify-center rounded-md", style.bg)}>
                    <Icon className={cn("h-3.5 w-3.5", style.text)} />
                  </div>
                  <div className={cn("h-1.5 w-1.5 rounded-full mt-1", style.dot)} />
                </div>
                <p className="mt-2.5 text-2xs text-aion-ink-muted leading-tight">{DISEASE_LABELS[type]}</p>
                <div className="mt-1.5 flex items-center justify-between">
                  <span className={cn("text-sm font-semibold tabular-nums", style.text)}>
                    {disease.severity_score}%
                  </span>
                  <span className="text-2xs capitalize text-aion-ink-faint">{disease.severity}</span>
                </div>
              </div>
            </Link>
          </motion.div>
        );
      })}
    </div>
  );
}
