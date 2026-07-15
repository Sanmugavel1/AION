import { useQuery } from "@tanstack/react-query";
import { decayApi } from "@/lib/api";

export const useDecayReport = () =>
  useQuery({ queryKey: ["decay", "report"], queryFn: () => decayApi.getReport(), staleTime: 5 * 60 * 1000 });

export const useDecayEntropy = () =>
  useQuery({ queryKey: ["decay", "entropy"], queryFn: () => decayApi.getEntropy(), staleTime: 10 * 60 * 1000 });

export const useDecayHalfLife = (knowledgeId?: string) =>
  useQuery({
    queryKey: ["decay", "halflife", knowledgeId],
    queryFn: () => decayApi.getHalfLife(knowledgeId!),
    staleTime: 15 * 60 * 1000,
    enabled: !!knowledgeId,
  });

export const useDecayForgotten = () =>
  useQuery({ queryKey: ["decay", "forgotten"], queryFn: () => decayApi.getForgotten(), staleTime: 5 * 60 * 1000 });

export const useDecayConflicts = () =>
  useQuery({ queryKey: ["decay", "conflicts"], queryFn: () => decayApi.getConflicts(), staleTime: 10 * 60 * 1000 });
