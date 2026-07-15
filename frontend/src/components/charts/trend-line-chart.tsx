"use client";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { formatDate } from "@/lib/utils/format";

interface TrendLineChartProps {
  data: Array<{ date: string; score: number }>;
  height?: number;
}

export function TrendLineChart({ data, height = 160 }: TrendLineChartProps) {
  const formatted = data.map((d) => ({
    ...d,
    label: formatDate(d.date),
    score: Math.round(d.score * 100),
  })).reverse();

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={formatted} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#E8B84B" stopOpacity={0.35} />
            <stop offset="95%" stopColor="#E8B84B" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
        <XAxis dataKey="label" tick={{ fill: "#756B5C", fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis domain={[0, 100]} tick={{ fill: "#756B5C", fontSize: 10 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{
            background: "#17140F",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "8px",
            color: "#F3EFE4",
            fontSize: "12px",
            boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
          }}
          formatter={(v: number) => [`${v}%`, "Health Score"]}
        />
        <ReferenceLine y={75} stroke="#3FCF8E" strokeOpacity={0.45} strokeDasharray="4 4" />
        <ReferenceLine y={50} stroke="#F5A623" strokeOpacity={0.45} strokeDasharray="4 4" />
        <Area
          type="monotone"
          dataKey="score"
          stroke="#E8B84B"
          strokeWidth={2}
          fill="url(#trendGrad)"
          dot={false}
          activeDot={{ r: 4, fill: "#E8B84B", stroke: "#0C0B09", strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
