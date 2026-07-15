"use client";
import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "@/components/layout/sidebar";
import { TopNav } from "@/components/layout/topnav";
import { DashboardBackground } from "@/components/layout/dashboard-background";
import { useAuthStore } from "@/lib/stores/auth.store";
import { useCurrentUser } from "@/lib/hooks/use-auth";

function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isInitialized = useAuthStore((s) => s.isInitialized);
  const setUser = useAuthStore((s) => s.setUser);
  const { data: user } = useCurrentUser();

  useEffect(() => {
    // Wait for the auth store to finish rehydrating from sessionStorage before
    // deciding to redirect — otherwise every hard page load (refresh, direct
    // URL) briefly sees the default isAuthenticated=false and bounces a
    // logged-in user to /login.
    if (isInitialized && !isAuthenticated) {
      router.push("/login");
    }
  }, [isInitialized, isAuthenticated, router]);

  useEffect(() => {
    if (user) setUser(user);
  }, [user, setUser]);

  if (!isInitialized || !isAuthenticated) return null;
  return <>{children}</>;
}

function PageTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    // No mode="wait": the incoming page mounts and starts fetching data
    // immediately, overlapping with the outgoing page's fade — avoids a
    // forced blank gap between pages while data loads.
    <AnimatePresence initial={false}>
      <motion.div
        key={pathname}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="relative flex h-screen overflow-hidden bg-aion-bg">
        <DashboardBackground />
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopNav />
          <main className="flex-1 overflow-y-auto">
            <div className="mx-auto max-w-[1600px] p-6">
              <PageTransition>{children}</PageTransition>
            </div>
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
