import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ingestionApi } from "@/lib/api";
import { useAuthStore } from "@/lib/stores/auth.store";

const ingestionKeys = {
  all: ["ingestion"] as const,
  recent: (orgId: string) => [...ingestionKeys.all, "recent", orgId] as const,
};

export function useRecentUploads() {
  const orgId = useAuthStore((s) => s.user?.org_id ?? "");
  return useQuery({
    queryKey: ingestionKeys.recent(orgId),
    queryFn: () => ingestionApi.recent(),
    staleTime: 30 * 1000,
    enabled: !!orgId,
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => ingestionApi.upload(file),
    onSuccess: () => {
      // A new document can change the Intelligence Index, disease scan, decay
      // report, and graph/MRI views all at once — simplest correct thing is
      // to invalidate everything rather than track every downstream key.
      qc.invalidateQueries();
    },
  });
}
