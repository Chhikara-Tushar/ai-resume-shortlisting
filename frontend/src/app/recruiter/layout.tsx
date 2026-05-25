"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { Sidebar } from "@/components/shared/Sidebar";
import { LayoutDashboard, Briefcase, Users, Lightbulb } from "lucide-react";

const navItems = [
  { href: "/recruiter/dashboard", label: "Dashboard", icon: <LayoutDashboard className="w-5 h-5" /> },
  { href: "/recruiter/jobs", label: "Jobs", icon: <Briefcase className="w-5 h-5" /> },
  { href: "/recruiter/jobs/new", label: "Post a Job", icon: <Lightbulb className="w-5 h-5" /> },
];

export default function RecruiterLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated || !["recruiter", "admin"].includes(user?.role || "")) {
      router.replace("/login");
    }
  }, [isAuthenticated, user, router]);

  if (!isAuthenticated) return null;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar navItems={navItems} role="recruiter" />
      <main className="ml-64 flex-1 p-8">{children}</main>
    </div>
  );
}
