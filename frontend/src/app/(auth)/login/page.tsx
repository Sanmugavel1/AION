"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Eye, EyeOff } from "lucide-react";
import { useLogin } from "@/lib/hooks/use-auth";
import { loginSchema } from "@/lib/validators/auth.schema";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AionLogo } from "@/components/ui/aion-logo";
import { cn } from "@/lib/utils/cn";

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const { mutate: login, isPending } = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const onSubmit = (data: LoginForm) => {
    login(data);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="relative z-10 w-full max-w-sm px-4"
    >
      {/* Logo */}
      <Link href="/" className="mb-8 block text-center cursor-pointer" title="Back to home">
        <motion.div
          whileHover={{ scale: 1.05 }}
          transition={{ type: "spring", stiffness: 400, damping: 20 }}
          className="mb-4 inline-flex h-14 w-14 items-center justify-center"
        >
          <AionLogo size={56} className="drop-shadow-[0_0_14px_rgba(232,184,75,0.5)]" />
        </motion.div>
        <h1 className="text-2xl font-bold tracking-tight text-aion-ink">AION</h1>
        <p className="text-xs text-aion-ink-faint mt-1">Organizational Intelligence Platform</p>
      </Link>

      {/* Card */}
      <div className="rounded-2xl border border-aion-border bg-aion-surface/80 backdrop-blur-xl shadow-card-lg p-8">
        <h2 className="text-lg font-bold text-aion-ink mb-1">Sign in</h2>
        <p className="text-xs text-aion-ink-faint mb-6">Access your organizational intelligence dashboard</p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-aion-ink-muted">Email</label>
            <Input
              {...register("username")}
              type="email"
              placeholder="you@organization.com"
              autoComplete="email"
              className={cn(errors.username && "border-health-red/50 focus-visible:ring-health-red/50")}
            />
            {errors.username && <p className="text-xs text-health-red">{errors.username.message}</p>}
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-aion-ink-muted">Password</label>
              <a href="mailto:support@aion.ai?subject=Password%20reset" className="text-2xs text-aion-accent hover:underline">
                Forgot password?
              </a>
            </div>
            <div className="relative">
              <Input
                {...register("password")}
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                autoComplete="current-password"
                className={cn("pr-10", errors.password && "border-health-red/50 focus-visible:ring-health-red/50")}
              />
              <button
                type="button"
                onClick={() => setShowPassword((s) => !s)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-aion-ink-faint hover:text-aion-ink transition-colors cursor-pointer"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {errors.password && <p className="text-xs text-health-red">{errors.password.message}</p>}
          </div>

          <Button type="submit" loading={isPending} className="w-full mt-2">
            Sign In
          </Button>
        </form>

        <p className="mt-6 text-center text-xs text-aion-ink-faint">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-aion-accent hover:underline font-medium">
            Request access
          </Link>
        </p>
      </div>
    </motion.div>
  );
}
