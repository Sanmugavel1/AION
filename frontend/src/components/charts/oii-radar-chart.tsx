"use client";
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip,
} from "recharts";
import { OIIDimensions } from "@/types";

const DIMENSION_LABELS: Record<keyof OIIDimensions, string> = {
  knowledge_velocity: "Velocity",
  knowledge_coverage: "Coverage",
  knowledge_quality: "Quality",
  learning_agility: "Agility",
  collaboration_density: "Collab",
  innovation_index: "Innovation",
  decision_intelligence: "Decision",
  cognitive_resilience: "Resilience",
  knowledge_accessibility: "Access",
  expertise_depth: "Depth",
  knowledge_retention: "Retention",
  adaptability_score: "Adaptability",
};

interface OIIRadarChartProps {
  dimensions: OIIDimensions;
}

export function OIIRadarChart({ dimensions }: OIIRadarChartProps) {
  const data = Object.entries(dimensions).map(([key, value]) => ({
    dimension: DIMENSION_LABELS[key as keyof OIIDimensions],
    value: Math.round(value * 100),
    fullMark: 100,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
        <PolarGrid stroke="rgba(255,255,255,0.12)" />
        <PolarAngleAxis
          dataKey="dimension"
          tick={{ fill: "#A69C8C", fontSize: 10 }}
        />
        <Radar
          name="OII"
          dataKey="value"
          stroke="#E8B84B"
          fill="#E8B84B"
          fillOpacity={0.22}
          strokeWidth={2}
          dot={{ r: 2.5, fill: "#E8B84B", strokeWidth: 0 }}
        />
        <Tooltip
          contentStyle={{
            background: "#17140F",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "8px",
            color: "#F3EFE4",
            fontSize: "12px",
            boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
          }}
          formatter={(value: number) => [`${value}%`, "Score"]}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
