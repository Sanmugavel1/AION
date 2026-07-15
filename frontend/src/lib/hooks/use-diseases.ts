import { useQuery } from "@tanstack/react-query";
import { diseasesApi } from "@/lib/api";
import { useAuthStore } from "@/lib/stores/auth.store";
import { DiseaseType } from "@/types";

export const diseaseKeys = {
  all: ["diseases"] as const,
  scan: (orgId: string) => [...diseaseKeys.all, "scan", orgId] as const,
  single: (orgId: string, type: DiseaseType) => [...diseaseKeys.all, orgId, type] as const,
  timeline: (orgId: string) => [...diseaseKeys.all, "timeline", orgId] as const,
};

export function useDiseaseScan() {
  const orgId = useAuthStore((s) => s.user?.org_id ?? "");
  return useQuery({
    queryKey: diseaseKeys.scan(orgId),
    queryFn: diseasesApi.scan,
    staleTime: 10 * 60 * 1000,
    enabled: !!orgId,
  });
}

export function useDiseaseTimeline() {
  const orgId = useAuthStore((s) => s.user?.org_id ?? "");
  return useQuery({
    queryKey: diseaseKeys.timeline(orgId),
    queryFn: diseasesApi.getTimeline,
    staleTime: 10 * 60 * 1000,
    enabled: !!orgId,
  });
}
