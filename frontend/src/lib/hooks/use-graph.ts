import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { graphApi } from "@/lib/api";
import { toast } from "sonner";

export const useDepartments = () =>
  useQuery({ queryKey: ["graph", "departments"], queryFn: () => graphApi.listDepartments(), staleTime: 60 * 1000 });

export function useCreateDepartment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => graphApi.createDepartment(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["graph", "departments"] });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Failed to create department");
    },
  });
}

export function useBulkCreatePeople() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (people: Parameters<typeof graphApi.bulkCreatePeople>[0]) => graphApi.bulkCreatePeople(people),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["graph", "departments"] });
      toast.success(`Added ${data.count} ${data.count === 1 ? "person" : "people"}`);
    },
    onError: () => toast.error("Failed to add people"),
  });
}

export function useBulkCreatePolicies() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (policies: Parameters<typeof graphApi.bulkCreatePolicies>[0]) => graphApi.bulkCreatePolicies(policies),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["graph", "departments"] });
      toast.success(`Added ${data.count} ${data.count === 1 ? "policy" : "policies"}`);
    },
    onError: () => toast.error("Failed to add policies"),
  });
}
