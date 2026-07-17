"use client";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { AxiosError } from "axios";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/stores/auth.store";
import { LoginRequest, RegisterRequest } from "@/types";
import { toast } from "sonner";

// Backend Render free-tier instances spin down after ~15min idle and take
// 30-50s+ to cold-start. Distinguish "server is waking up" from "your
// credentials are wrong" instead of collapsing every failure into the same
// message — a timeout/network error is not the same problem as a 401.
function describeAuthError(error: unknown, wrongCredsMessage: string): string {
  if (error instanceof AxiosError) {
    if (!error.response) {
      return error.code === "ECONNABORTED"
        ? "The server is taking longer than usual to respond — it may be starting up after being idle. Please try again."
        : "Can't reach the server right now — it may be starting up after being idle. Please retry in a moment.";
    }
    if (error.response.status === 401) {
      return wrongCredsMessage;
    }
    const detail = (error.response.data as { detail?: string; message?: string } | undefined);
    if (detail?.detail) return detail.detail;
    if (detail?.message) return detail.message;
  }
  return "Something went wrong — please try again.";
}

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
    onError: (error) => toast.error(describeAuthError(error, "Invalid credentials")),
  });
}

const DEMO_CREDENTIALS = { username: "demo@aion.ai", password: "DemoPass123!" };

export function useRunDemo() {
  const { setTokens, setUser } = useAuthStore();
  const router = useRouter();
  let wakingToastId: string | number | undefined;

  return useMutation({
    mutationFn: async () => {
      // If the free-tier backend is cold, the login call can take 30s+.
      // Let the user know what's happening instead of leaving them staring
      // at a spinner that looks identical to "broken."
      const wakeTimer = setTimeout(() => {
        wakingToastId = toast.loading("Waking up the demo server — this can take up to a minute on first load…");
      }, 3000);
      try {
        return await authApi.login(DEMO_CREDENTIALS);
      } finally {
        clearTimeout(wakeTimer);
        if (wakingToastId !== undefined) toast.dismiss(wakingToastId);
      }
    },
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
    onError: (error) =>
      toast.error(describeAuthError(error, "Demo is temporarily unavailable — please try again")),
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
    onError: (error) => toast.error(describeAuthError(error, "Registration failed")),
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
