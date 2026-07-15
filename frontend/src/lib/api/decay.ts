import { apiClient } from "./client";
import { DecayReport, EntropyReport, HalfLifeResult } from "@/types";

export interface HalfLifeParams {
  domain?: string;
  access_freq_per_week?: number;
  last_updated_days_ago?: number;
  days_since_last_access?: number;
  owner_count?: number;
}

export const decayApi = {
  getReport: async (): Promise<DecayReport> => {
    const res = await apiClient.get("/decay/report");
    return res.data;
  },

  getEntropy: async (): Promise<EntropyReport> => {
    const res = await apiClient.get("/decay/entropy");
    return res.data;
  },

  getHalfLife: async (knowledgeId: string, params?: HalfLifeParams): Promise<HalfLifeResult> => {
    const res = await apiClient.get(`/decay/half-life/${knowledgeId}`, { params });
    return res.data;
  },

  getForgotten: async (thresholdDays = 90) => {
    const res = await apiClient.get("/decay/forgotten", { params: { threshold_days: thresholdDays } });
    return res.data;
  },

  getConflicts: async () => {
    const res = await apiClient.get("/decay/conflicts");
    return res.data;
  },
};
