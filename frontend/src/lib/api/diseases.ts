import { apiClient } from "./client";
import { DiseaseScanReport, DiseaseTimeline, DiseaseType } from "@/types";

export const diseasesApi = {
  scan: async (): Promise<DiseaseScanReport> => {
    const res = await apiClient.get("/diseases/scan");
    return res.data;
  },

  getReport: async (): Promise<DiseaseScanReport> => {
    const res = await apiClient.get("/diseases/report");
    return res.data;
  },

  getDisease: async (diseaseType: DiseaseType) => {
    const res = await apiClient.get(`/diseases/${diseaseType}`);
    return res.data;
  },

  getTimeline: async (): Promise<DiseaseTimeline> => {
    const res = await apiClient.get("/diseases/timeline");
    return res.data;
  },
};
