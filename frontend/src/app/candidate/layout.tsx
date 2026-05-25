"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { Sidebar } from "@/components/shared/Sidebar";
import { LayoutDashboard, FileText, User, Briefcase, ClipboardList } from "lucide-react";
import { ChatbotWidget } from "@/components/candidate/ChatbotWidget";

const navItems = [
  { href: "/candidate/dashboard", label: "Dashboard", icon: <LayoutDashboard className="w-5 h-5" /> },
  { href: "/candidate/resume", label: "My Resume", icon: <FileText className="w-5 h-5" /> },
  { href: "/candidate/profile", label: "Profile", icon: <User className="w-5 h-5" /> },
  { href: "/candidate/jobs", label: "Browse Jobs", icon: <Briefcase className="w-5 h-5" /> },
  { href: "/candidate/applications", label: "Applications", icon: <ClipboardList className="w-5 h-5" /> },
];

export default function CandidateLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated || user?.role !== "candidate") {
      router.replace("/login");
    }
  }, [isAuthenticated, user, router]);

  if (!isAuthenticated || user?.role !== "candidate") return null;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar navItems={navItems} role="candidate" />
      <main className="ml-64 flex-1 p-8">{children}</main>
      <ChatbotWidget />
    </div>
  );
}
