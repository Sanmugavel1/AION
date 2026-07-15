import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { CurrentUser, Permission } from "@/types";
import { clearAuth, storeTokens } from "@/lib/api/client";

interface AuthState {
  user: CurrentUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isInitialized: boolean;

  setTokens: (access: string, refresh: string) => void;
  setUser: (user: CurrentUser) => void;
  logout: () => void;
  hasPermission: (permission: Permission) => boolean;
  hasAnyPermission: (permissions: Permission[]) => boolean;
  initialize: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isInitialized: false,

      setTokens: (access, refresh) => {
        storeTokens(access, refresh);
        set({ accessToken: access, refreshToken: refresh, isAuthenticated: true });
      },

      setUser: (user) => set({ user }),

      logout: () => {
        clearAuth();
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
      },

      hasPermission: (permission) => {
        const { user } = get();
        return user?.permissions.includes(permission) ?? false;
      },

      hasAnyPermission: (permissions) => {
        const { user } = get();
        return permissions.some((p) => user?.permissions.includes(p) ?? false);
      },

      initialize: () => {
        if (typeof window !== "undefined") {
          const token = sessionStorage.getItem("aion_access_token");
          const refresh = localStorage.getItem("aion_refresh_token");
          set({
            accessToken: token,
            refreshToken: refresh,
            isAuthenticated: !!token,
            isInitialized: true,
          });
        }
      },
    }),
    {
      name: "aion-auth",
      storage: createJSONStorage(() => ({
        getItem: (name) => (typeof window !== "undefined" ? sessionStorage.getItem(name) : null),
        setItem: (name, value) => typeof window !== "undefined" && sessionStorage.setItem(name, value),
        removeItem: (name) => typeof window !== "undefined" && sessionStorage.removeItem(name),
      })),
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
      onRehydrateStorage: () => (state) => {
        // Rehydration from sessionStorage is asynchronous — until this fires, isAuthenticated
        // is still its default (false), which would otherwise cause AuthGuard to redirect to
        // /login on every hard page load even with a valid session.
        state?.initialize();
      },
    },
  ),
);
