"use client";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/stores/auth.store";
import { LoginRequest, RegisterRequest } from "@/types";
import { toast } from "sonner";

export function useLogin() {
  const { setTokens, setUser } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onSuccess: async (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token);
      try {
        const user = await authApi.me();
        setUser(user);
        router.push("/dashboard");
      } catch {
        toast.error("Failed to load user info");
      }
    },
    onError: () => toast.error("Invalid credentials"),
  });
}

const DEMO_CREDENTIALS = { username: "demo@aion.ai", password: "DemoPass123!" };

export function useRunDemo() {
  const { setTokens, setUser } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: () => authApi.login(DEMO_CREDENTIALS),
    onSuccess: async (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token);
      try {
        const user = await authApi.me();
        setUser(user);
        router.push("/dashboard/demo");
      } catch {
        toast.error("Failed to load demo account");
      }
    },
    onError: () => toast.error("Demo is temporarily unavailable — please try again"),
  });
}

export function useRegister() {
  const { setTokens, setUser } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
    onSuccess: async (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token);
      try {
        const user = await authApi.me();
        setUser(user);
        router.push("/dashboard");
      } catch {
        toast.error("Failed to load user info");
      }
    },
    onError: () => toast.error("Registration failed"),
  });
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout);
  const router = useRouter();

  return () => {
    logout();
    router.push("/login");
  };
}

export function useCurrentUser() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.me,
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });
}
