import { apiClient } from "./client";
import { HealingAction, HealingPriority, HealingStatus } from "@/types";

export const healingApi = {
  getRecommendations: async (params?: {
    status_filter?: HealingStatus;
    priority?: HealingPriority;
  }): Promise<{ recommendations: HealingAction[]; total: number }> => {
    const res = await apiClient.get("/healing/recommendations", { params });
    return res.data;
  },

  approve: async (id: string) => {
    const res = await apiClient.post(`/healing/recommendations/${id}/approve`);
    return res.data;
  },

  reject: async (id: string, reason?: string) => {
    const res = await apiClient.post(
      `/healing/recommendations/${id}/reject`,
      null,
      { params: reason ? { reason } : undefined },
    );
    return res.data;
  },

  generate: async (): Promise<{ generated: number; recommendations: HealingAction[] }> => {
    const res = await apiClient.post("/healing/generate");
    return res.data;
  },
};
