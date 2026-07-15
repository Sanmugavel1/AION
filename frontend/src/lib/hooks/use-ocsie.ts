import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ocsieApi } from "@/lib/api";
import { toast } from "sonner";

const ocsieKeys = {
  all: ["ocsie"] as const,
  profile: (id: string) => [...ocsieKeys.all, "profile", id] as const,
  report: (id: string) => [...ocsieKeys.all, "report", id] as const,
  roadmap: (id: string) => [...ocsieKeys.all, "roadmap", id] as const,
  impact: (id: string) => [...ocsieKeys.all, "impact", id] as const,
  unfinished: (id: string) => [...ocsieKeys.all, "unfinished", id] as const,
  gap: (from: string, to: string) => [...ocsieKeys.all, "gap", from, to] as const,
};

export function useEmployeeProfile(employeeId: string) {
  return useQuery({
    queryKey: ocsieKeys.profile(employeeId),
    queryFn: () => ocsieApi.getProfile(employeeId),
    staleTime: 2 * 60 * 1000,
    enabled: !!employeeId,
  });
}

export function useContinuityReport(employeeId: string) {
  return useQuery({
    queryKey: ocsieKeys.report(employeeId),
    queryFn: () => ocsieApi.getContinuityReport(employeeId),
    staleTime: 5 * 60 * 1000,
    enabled: !!employeeId,
  });
}

export function useSuccessorRoadmap(employeeId: string) {
  return useQuery({
    queryKey: ocsieKeys.roadmap(employeeId),
    queryFn: () => ocsieApi.getSuccessorRoadmap(employeeId),
    staleTime: 10 * 60 * 1000,
    enabled: !!employeeId,
  });
}

export function useBusinessImpact(employeeId: string) {
  return useQuery({
    queryKey: ocsieKeys.impact(employeeId),
    queryFn: () => ocsieApi.getBusinessImpact(employeeId),
    staleTime: 5 * 60 * 1000,
    enabled: !!employeeId,
  });
}

export function useInitiateTransition() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, params }: { id: string; params: { departure_date?: string; reason?: string } }) =>
      ocsieApi.initiateTransition(id, params),
    onSuccess: () => {
      toast.success("Departure protocol initiated");
      qc.invalidateQueries({ queryKey: ocsieKeys.all });
    },
    onError: () => toast.error("Failed to initiate departure protocol"),
  });
}
