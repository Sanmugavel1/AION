import { useMutation, useQuery } from "@tanstack/react-query";
import { boardApi } from "@/lib/api";

export const useBoardBriefing = () =>
  useQuery({ queryKey: ["board", "briefing"], queryFn: () => boardApi.getLatestBriefing(), staleTime: 10 * 60 * 1000 });

export const useBoardRisks = () =>
  useQuery({ queryKey: ["board", "risks"], queryFn: () => boardApi.getRisks(), staleTime: 10 * 60 * 1000 });

export const useBoardOpportunities = () =>
  useQuery({ queryKey: ["board", "opportunities"], queryFn: () => boardApi.getOpportunities(), staleTime: 10 * 60 * 1000 });

export const useAdvisorChat = () =>
  useMutation({
    mutationFn: ({ message, history }: { message: string; history: { role: "user" | "assistant"; content: string }[] }) =>
      boardApi.chat(message, history),
  });
