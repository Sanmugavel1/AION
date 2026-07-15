import { apiClient } from "./client";
import { PredefinedScenario, SimulationRequest, SimulationResult } from "@/types";

export const simulationApi = {
  getScenarios: async (): Promise<{ scenarios: PredefinedScenario[] }> => {
    const res = await apiClient.get("/simulation/scenarios");
    return res.data;
  },

  run: async (request: SimulationRequest): Promise<SimulationResult> => {
    const res = await apiClient.post("/simulation/run", request);
    return res.data;
  },
};
