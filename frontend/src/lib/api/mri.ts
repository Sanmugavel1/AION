import { apiClient } from "./client";
import {
  BrainMapResponse,
  Bottleneck,
  InnovationCenter,
  KnowledgeBlackHole,
  KnowledgeFlow,
  TimelineForecast,
} from "@/types";

export const mriApi = {
  getBrainMap: async (): Promise<BrainMapResponse> => {
    const res = await apiClient.get("/mri/brain-map");
    return res.data;
  },

  getKnowledgeFlow: async (): Promise<KnowledgeFlow[]> => {
    const res = await apiClient.get("/mri/knowledge-flow");
    return res.data;
  },

  getBottlenecks: async (): Promise<Bottleneck[]> => {
    const res = await apiClient.get("/mri/bottlenecks");
    return res.data;
  },

  getDependencies: async () => {
    const res = await apiClient.get("/mri/dependencies");
    return res.data;
  },

  getInnovationCenters: async (): Promise<InnovationCenter[]> => {
    const res = await apiClient.get("/mri/innovation-centers");
    return res.data;
  },

  getBlackHoles: async (): Promise<KnowledgeBlackHole[]> => {
    const res = await apiClient.get("/mri/black-holes");
    return res.data;
  },

  getTimelineForecast: async (): Promise<TimelineForecast> => {
    const res = await apiClient.get("/mri/timeline-forecast");
    return res.data;
  },
};
