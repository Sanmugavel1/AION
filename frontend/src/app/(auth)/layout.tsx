import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="relative min-h-screen flex items-center justify-center bg-aion-bg overflow-hidden">
      {/* Subtle ambient background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 h-[600px] w-[600px] rounded-full bg-aion-accent/[0.04] blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 h-[400px] w-[400px] rounded-full bg-aion-insight/[0.03] blur-[80px]" />
        {/* Faint grid texture */}
        <div className="absolute inset-0 opacity-[0.4]"
          style={{ backgroundImage: "linear-gradient(rgba(15,23,42,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(15,23,42,0.03) 1px, transparent 1px)", backgroundSize: "48px 48px" }}
        />
      </div>
      {children}
    </div>
  );
}
