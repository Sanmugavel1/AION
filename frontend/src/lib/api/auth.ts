import { apiClient } from "./client";
import { CurrentUser, LoginRequest, RegisterRequest, TokenResponse } from "@/types";

export const authApi = {
  register: async (data: RegisterRequest): Promise<TokenResponse> => {
    const res = await apiClient.post<TokenResponse>("/auth/register", data);
    return res.data;
  },

  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const form = new URLSearchParams();
    form.append("username", data.username);
    form.append("password", data.password);
    const res = await apiClient.post<TokenResponse>("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return res.data;
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const res = await apiClient.post<TokenResponse>("/auth/refresh", null, {
      params: { refresh_token: refreshToken },
    });
    return res.data;
  },

  me: async (): Promise<CurrentUser> => {
    const res = await apiClient.get<CurrentUser>("/auth/me");
    return res.data;
  },
};
