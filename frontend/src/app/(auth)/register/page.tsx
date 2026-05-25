"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import toast from "react-hot-toast";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import Link from "next/link";
import { Brain, User, Briefcase } from "lucide-react";

const schema = z.object({
  full_name: z.string().min(2, "Name required"),
  email: z.string().email("Invalid email"),
  password: z.string().min(8, "Min 8 characters"),
  role: z.enum(["candidate", "recruiter"]),
});

type Form = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [loading, setLoading] = useState(false);

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { role: "candidate" },
  });
  const selectedRole = watch("role");

  const onSubmit = async (data: Form) => {
    setLoading(true);
    try {
      const res = await authApi.register(data);
      const { access_token, refresh_token, role } = res.data;
      const meRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost/api"}/v1/auth/me`, {
        headers: { Authorization: `Bearer ${access_token}` },
      });
      const me = await meRes.json();
      setAuth(me.user, access_token, refresh_token);
      toast.success("Account created!");
      if (role === "recruiter") router.push("/recruiter/dashboard");
      else router.push("/candidate/dashboard");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-2xl mb-4">
            <Brain className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Create Account</h1>
          <p className="text-slate-500 mt-1">Join the AI hiring platform</p>
        </div>

        <div className="card p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Role selector */}
            <div className="grid grid-cols-2 gap-3">
              {(["candidate", "recruiter"] as const).map((role) => (
                <button
                  key={role}
                  type="button"
                  onClick={() => setValue("role", role)}
                  className={`flex items-center gap-2 p-3 rounded-lg border-2 transition-all text-sm font-medium ${
                    selectedRole === role
                      ? "border-primary-600 bg-primary-50 text-primary-700"
                      : "border-slate-200 text-slate-600 hover:border-slate-300"
                  }`}
                >
                  {role === "candidate" ? <User className="w-4 h-4" /> : <Briefcase className="w-4 h-4" />}
                  {role === "candidate" ? "Job Seeker" : "Recruiter"}
                </button>
              ))}
            </div>

            <div>
              <label className="label">Full Name</label>
              <input {...register("full_name")} className="input" placeholder="John Doe" />
              {errors.full_name && <p className="text-red-500 text-xs mt-1">{errors.full_name.message}</p>}
            </div>
            <div>
              <label className="label">Email</label>
              <input {...register("email")} type="email" className="input" placeholder="you@company.com" />
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
            </div>
            <div>
              <label className="label">Password</label>
              <input {...register("password")} type="password" className="input" placeholder="Min 8 characters" />
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
              {loading ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <p className="text-center text-sm text-slate-500 mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-primary-600 font-medium hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
