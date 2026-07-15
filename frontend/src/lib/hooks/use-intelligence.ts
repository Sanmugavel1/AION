import { useQuery } from "@tanstack/react-query";
import { intelligenceApi } from "@/lib/api";
import { useAuthStore } from "@/lib/stores/auth.store";

export const intelligenceKeys = {
  all: ["intelligence"] as const,
  index: (orgId: string) => [...intelligenceKeys.all, "index", orgId] as const,
  history: (orgId: string, limit: number) => [...intelligenceKeys.all, "history", orgId, limit] as const,
  trends: (orgId: string) => [...intelligenceKeys.all, "trends", orgId] as const,
};

export function useIntelligenceIndex() {
  const orgId = useAuthStore((s) => s.user?.org_id ?? "");
  return useQuery({
    queryKey: intelligenceKeys.index(orgId),
    queryFn: intelligenceApi.getIndex,
    staleTime: 5 * 60 * 1000,
    enabled: !!orgId,
  });
}

export function useIntelligenceHistory(limit = 30) {
  const orgId = useAuthStore((s) => s.user?.org_id ?? "");
  return useQuery({
    queryKey: intelligenceKeys.history(orgId, limit),
    queryFn: () => intelligenceApi.getHistory(limit),
    staleTime: 10 * 60 * 1000,
    enabled: !!orgId,
  });
}

export function useIntelligenceTrends() {
  const orgId = useAuthStore((s) => s.user?.org_id ?? "");
  return useQuery({
    queryKey: intelligenceKeys.trends(orgId),
    queryFn: intelligenceApi.getTrends,
    staleTime: 10 * 60 * 1000,
    enabled: !!orgId,
  });
}
