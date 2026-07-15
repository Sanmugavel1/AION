import { apiClient } from "./client";
import { OIISnapshot, OIITrends } from "@/types";

export const intelligenceApi = {
  getIndex: async (): Promise<OIISnapshot | { message: string }> => {
    const res = await apiClient.get("/intelligence/index");
    return res.data;
  },

  getHistory: async (limit = 30): Promise<OIISnapshot[]> => {
    const res = await apiClient.get("/intelligence/history", { params: { limit } });
    return res.data;
  },

  getTrends: async (): Promise<OIITrends> => {
    const res = await apiClient.get("/intelligence/trends");
    return res.data;
  },
};
