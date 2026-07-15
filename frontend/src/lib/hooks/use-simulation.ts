import { useMutation, useQuery } from "@tanstack/react-query";
import { simulationApi } from "@/lib/api";
import { SimulationRequest } from "@/types";
import { useUIStore } from "@/lib/stores/ui.store";
import { toast } from "sonner";

export function useSimulationScenarios() {
  return useQuery({
    queryKey: ["simulation", "scenarios"],
    queryFn: simulationApi.getScenarios,
    staleTime: Infinity,
  });
}

export function useRunSimulation() {
  const setResult = useUIStore((s) => s.setSimulationResult);
  const setRunning = useUIStore((s) => s.setSimulationRunning);

  return useMutation({
    mutationFn: (request: SimulationRequest) => simulationApi.run(request),
    onMutate: () => setRunning(true),
    onSuccess: (data) => {
      setResult(data);
      setRunning(false);
      toast.success("Simulation completed");
    },
    onError: () => {
      setRunning(false);
      toast.error("Simulation failed");
    },
  });
}
