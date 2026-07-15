"use client";
import { motion } from "framer-motion";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRegister } from "@/lib/hooks/use-auth";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AionLogo } from "@/components/ui/aion-logo";
import { cn } from "@/lib/utils/cn";

const registerFormSchema = z.object({
  email: z.string().email("Valid email required"),
  username: z.string().min(3, "Username must be at least 3 characters"),
  full_name: z.string().min(1, "Full name is required"),
  org_name: z.string().min(2, "Organization name is required"),
  password: z.string().min(8, "Minimum 8 characters"),
  industry: z.string().optional(),
});

type RegisterForm = z.infer<typeof registerFormSchema>;

export default function RegisterPage() {
  const { mutate: register, isPending } = useRegister();

  const {
    register: formRegister,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({ resolver: zodResolver(registerFormSchema) });

  const onSubmit = (data: RegisterForm) => {
    register(data);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="relative z-10 w-full max-w-md px-4"
    >
      <Link href="/" className="mb-8 block text-center cursor-pointer" title="Back to home">
        <motion.div
          whileHover={{ scale: 1.05 }}
          transition={{ type: "spring", stiffness: 400, damping: 20 }}
          className="mb-4 inline-flex h-14 w-14 items-center justify-center"
        >
          <AionLogo size={56} className="drop-shadow-[0_0_14px_rgba(232,184,75,0.5)]" />
        </motion.div>
        <h1 className="text-2xl font-bold tracking-tight text-aion-ink">AION</h1>
        <p className="text-xs text-aion-ink-faint mt-1">Request Platform Access</p>
      </Link>

      <div className="rounded-2xl border border-aion-border bg-aion-surface/80 backdrop-blur-xl shadow-card-lg p-8">
        <h2 className="text-lg font-bold text-aion-ink mb-1">Create account</h2>
        <p className="text-xs text-aion-ink-faint mb-6">Creates your organization's workspace instantly — no approval wait</p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-aion-ink-muted">Full Name</label>
              <Input {...formRegister("full_name")} placeholder="Jane Smith" className={cn(errors.full_name && "border-health-red/50")} />
              {errors.full_name && <p className="text-xs text-health-red">{errors.full_name.message}</p>}
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-aion-ink-muted">Username</label>
              <Input {...formRegister("username")} placeholder="jsmith" className={cn(errors.username && "border-health-red/50")} />
              {errors.username && <p className="text-xs text-health-red">{errors.username.message}</p>}
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-aion-ink-muted">Email</label>
            <Input {...formRegister("email")} type="email" placeholder="you@organization.com" className={cn(errors.email && "border-health-red/50")} />
            {errors.email && <p className="text-xs text-health-red">{errors.email.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-aion-ink-muted">Organization Name</label>
              <Input {...formRegister("org_name")} placeholder="Acme Corp" className={cn(errors.org_name && "border-health-red/50")} />
              {errors.org_name && <p className="text-xs text-health-red">{errors.org_name.message}</p>}
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-aion-ink-muted">Industry (optional)</label>
              <Input {...formRegister("industry")} placeholder="Technology" />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-aion-ink-muted">Password</label>
            <Input {...formRegister("password")} type="password" placeholder="Min. 8 characters" className={cn(errors.password && "border-health-red/50")} />
            {errors.password && <p className="text-xs text-health-red">{errors.password.message}</p>}
          </div>

          <Button type="submit" loading={isPending} className="w-full mt-2">
            Request Access
          </Button>
        </form>

        <p className="mt-6 text-center text-xs text-aion-ink-faint">
          Already have an account?{" "}
          <Link href="/login" className="text-aion-accent hover:underline font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </motion.div>
  );
}
