import { useQuery } from "@tanstack/react-query";
import { mriApi } from "@/lib/api";
import { useAuthStore } from "@/lib/stores/auth.store";

export const mriKeys = {
  all: ["mri"] as const,
  brainMap: (orgId: string) => [...mriKeys.all, "brain-map", orgId] as const,
  flow: (orgId: string) => [...mriKeys.all, "flow", orgId] as const,
  bottlenecks: (orgId: string) => [...mriKeys.all, "bottlenecks", orgId] as const,
  blackHoles: (orgId: string) => [...mriKeys.all, "black-holes", orgId] as const,
  forecast: (orgId: string) => [...mriKeys.all, "forecast", orgId] as const,
  innovationCenters: (orgId: string) => [...mriKeys.all, "innovation", orgId] as const,
};

function useOrgId() {
  return useAuthStore((s) => s.user?.org_id ?? "");
}

export function useBrainMap() {
  const orgId = useOrgId();
  return useQuery({
    queryKey: mriKeys.brainMap(orgId),
    queryFn: mriApi.getBrainMap,
    staleTime: 5 * 60 * 1000,
    enabled: !!orgId,
  });
}

export function useKnowledgeFlow() {
  const orgId = useOrgId();
  return useQuery({
    queryKey: mriKeys.flow(orgId),
    queryFn: mriApi.getKnowledgeFlow,
    staleTime: 5 * 60 * 1000,
    enabled: !!orgId,
  });
}

export function useBottlenecks() {
  const orgId = useOrgId();
  return useQuery({
    queryKey: mriKeys.bottlenecks(orgId),
    queryFn: mriApi.getBottlenecks,
    staleTime: 5 * 60 * 1000,
    enabled: !!orgId,
  });
}

export function useBlackHoles() {
  const orgId = useOrgId();
  return useQuery({
    queryKey: mriKeys.blackHoles(orgId),
    queryFn: mriApi.getBlackHoles,
    staleTime: 5 * 60 * 1000,
    enabled: !!orgId,
  });
}

export function useInnovationCenters() {
  const orgId = useOrgId();
  return useQuery({
    queryKey: mriKeys.innovationCenters(orgId),
    queryFn: mriApi.getInnovationCenters,
    staleTime: 5 * 60 * 1000,
    enabled: !!orgId,
  });
}

export function useTimelineForecast() {
  const orgId = useOrgId();
  return useQuery({
    queryKey: mriKeys.forecast(orgId),
    queryFn: mriApi.getTimelineForecast,
    staleTime: 30 * 60 * 1000,
    enabled: !!orgId,
  });
}
