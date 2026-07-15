import { apiClient } from "./client";

export const boardApi = {
  getLatestBriefing: async () => {
    const res = await apiClient.get("/advisor/briefing/latest");
    const data = res.data;
    // Normalize the backend nested response into a flat structure the UI expects
    const execSummary = data.executive_summary;
    const sections = data.sections ?? {};
    return {
      briefing_date: data.briefing_date,
      generated_for: data.generated_for,
      org_id: data.org_id,
      executive_summary:
        typeof execSummary === "string"
          ? execSummary
          : execSummary?.top_priority ?? "No briefing summary available.",
      key_metrics: {
        // score arrives as a "49.6%" string (0-100 scale); OIIHealthGauge expects a 0-1 fraction
        overall_oii_score: (parseFloat(sections["1_organization_health"]?.score) || 0) / 100,
        health_trend: execSummary?.health_trend ?? "stable",
        bottleneck_count: sections["2_predicted_risks"]?.[0]?.count ?? 0,
      },
      recommendations: [
        ...(sections["4_future_critical_areas"] ?? []).map((area: string) => ({
          title: "Critical Area",
          description: area,
        })),
        ...(sections["5_innovation_opportunities"] ?? []).map((opp: string) => ({
          title: "Innovation Opportunity",
          description: opp,
        })),
      ],
      raw: data,
    };
  },

  listBriefings: async () => {
    const res = await apiClient.get("/advisor/briefing");
    return res.data;
  },

  getRisks: async () => {
    const res = await apiClient.get("/advisor/risks");
    // Backend returns { org_id, predicted_risks: [...] }
    const data = res.data;
    return (data.predicted_risks ?? []).map((r: any) => ({
      id: r.risk_type,
      title: (r.risk_type ?? "").replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()),
      description: `Timeline: ${r.timeline_days} days`,
      severity: r.severity,
      mitigation_strategy: r.action ?? null,
    }));
  },

  getOpportunities: async () => {
    const res = await apiClient.get("/advisor/opportunities");
    // Backend returns { org_id, opportunities: [...] }
    const data = res.data;
    return (data.opportunities ?? []).map((o: any) => ({
      id: o.type,
      title: (o.type ?? "").replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()),
      description: o.description,
      potential_value: "High Value",
    }));
  },

  chat: async (message: string, history: { role: "user" | "assistant"; content: string }[]) => {
    const res = await apiClient.post("/advisor/chat", { message, history });
    return res.data as { answer: string; grounded_on: Record<string, unknown> };
  },
};
