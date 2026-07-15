import { z } from "zod";

export const loginSchema = z.object({
  username: z.string().min(1, "Email or username is required"),
  password: z.string().min(1, "Password is required"),
});

export const registerSchema = z.object({
  email: z.string().email("Valid email is required"),
  username: z.string().min(3, "Username must be at least 3 characters").max(100),
  full_name: z.string().min(1, "Full name is required").max(255),
  password: z.string().min(8, "Password must be at least 8 characters"),
  org_name: z.string().min(2, "Organization name is required").max(255),
  industry: z.string().optional(),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
