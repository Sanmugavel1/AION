import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { APIError, TokenResponse } from "@/types";

// 127.0.0.1, not localhost — on Windows, "localhost" resolves to the IPv6
// loopback (::1) first, which nothing is listening on, adding a multi-second
// fallback delay to every request before it retries on IPv4. Measured ~18x
// slower (447ms -> 24ms per call) with "localhost" vs "127.0.0.1" locally.
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001";
const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX || "/api/v1";

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}${API_PREFIX}`,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: string) => void; reject: (e: unknown) => void }> = [];

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach(({ resolve, reject }) => (error ? reject(error) : resolve(token!)));
  failedQueue = [];
}

// Request interceptor — attach access token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== "undefined") {
      const token = sessionStorage.getItem("aion_access_token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor — handle 401, refresh token
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<APIError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers!.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = typeof window !== "undefined" ? localStorage.getItem("aion_refresh_token") : null;

      if (!refreshToken) {
        clearAuth();
        if (typeof window !== "undefined") window.location.href = "/login";
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post<TokenResponse>(
          `${BASE_URL}${API_PREFIX}/auth/refresh`,
          null,
          { params: { refresh_token: refreshToken } },
        );
        storeTokens(data.access_token, data.refresh_token);
        processQueue(null, data.access_token);
        originalRequest.headers!.Authorization = `Bearer ${data.access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearAuth();
        if (typeof window !== "undefined") window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

export function storeTokens(access: string, refresh: string) {
  if (typeof window !== "undefined") {
    sessionStorage.setItem("aion_access_token", access);
    localStorage.setItem("aion_refresh_token", refresh);
  }
}

export function clearAuth() {
  if (typeof window !== "undefined") {
    sessionStorage.removeItem("aion_access_token");
    sessionStorage.removeItem("aion_user");
    localStorage.removeItem("aion_refresh_token");
  }
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("aion_access_token");
}
