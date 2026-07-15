import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { healingApi } from "@/lib/api";
import { useAuthStore } from "@/lib/stores/auth.store";
import { HealingPriority, HealingStatus } from "@/types";
import { toast } from "sonner";

const healingKeys = {
  all: ["healing"] as const,
  recommendations: (orgId: string, status?: string, priority?: string) =>
    [...healingKeys.all, "recs", orgId, status, priority] as const,
};

export function useHealingRecommendations(status?: HealingStatus, priority?: HealingPriority) {
  const orgId = useAuthStore((s) => s.user?.org_id ?? "");
  return useQuery({
    queryKey: healingKeys.recommendations(orgId, status, priority),
    queryFn: () =>
      healingApi.getRecommendations(
        status || priority ? { status_filter: status, priority } : undefined,
      ),
    staleTime: 60 * 1000,
    enabled: !!orgId,
  });
}

export function useApproveRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: healingApi.approve,
    onSuccess: () => {
      toast.success("Recommendation approved");
      qc.invalidateQueries({ queryKey: healingKeys.all });
    },
    onError: () => toast.error("Failed to approve recommendation"),
  });
}

export function useRejectRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => healingApi.reject(id, reason),
    onSuccess: () => {
      toast.success("Recommendation rejected");
      qc.invalidateQueries({ queryKey: healingKeys.all });
    },
    onError: () => toast.error("Failed to reject recommendation"),
  });
}

export function useGenerateRecommendations() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: healingApi.generate,
    onSuccess: (data) => {
      toast.success(`Generated ${data.generated} new recommendations`);
      qc.invalidateQueries({ queryKey: healingKeys.all });
    },
    onError: () => toast.error("Failed to generate recommendations"),
  });
}
