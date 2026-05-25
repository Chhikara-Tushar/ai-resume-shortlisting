"use client";
import { useQuery } from "@tanstack/react-query";
import { candidateApi } from "@/lib/api";
import { ClipboardList, CheckCircle2, XCircle, Clock, Star, MessageSquare } from "lucide-react";

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  applied:     { label: "Applied",     color: "badge-blue",   icon: <Clock className="w-3.5 h-3.5" /> },
  shortlisted: { label: "Shortlisted", color: "badge-green",  icon: <Star className="w-3.5 h-3.5" /> },
  interview:   { label: "Interview",   color: "badge-purple", icon: <MessageSquare className="w-3.5 h-3.5" /> },
  offered:     { label: "Offered",     color: "badge-green",  icon: <CheckCircle2 className="w-3.5 h-3.5" /> },
  rejected:    { label: "Rejected",    color: "badge-red",    icon: <XCircle className="w-3.5 h-3.5" /> },
  withdrawn:   { label: "Withdrawn",   color: "badge-slate",  icon: <XCircle className="w-3.5 h-3.5" /> },
};

export default function Applications() {
  const { data: apps = [], isLoading } = useQuery({ queryKey: ["my-applications"], queryFn: () => candidateApi.getApplications().then(r => r.data) });

  const counts = apps.reduce((acc: Record<string, number>, a: any) => { acc[a.status] = (acc[a.status] || 0) + 1; return acc; }, {});

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">My Applications</h1>
        <p className="text-slate-500 mt-1">{apps.length} total applications</p>
      </div>

      {/* Status summary */}
      <div className="grid grid-cols-5 gap-3">
        {Object.entries(STATUS_CONFIG).map(([status, config]) => (
          <div key={status} className="card p-4 text-center">
            <p className="text-2xl font-bold text-slate-900">{counts[status] || 0}</p>
            <p className="text-xs text-slate-500 mt-1">{config.label}</p>
          </div>
        ))}
      </div>

      {/* Applications list */}
      {isLoading ? (
        <div className="card p-8 text-center text-slate-400">Loading...</div>
      ) : apps.length === 0 ? (
        <div className="card p-12 text-center">
          <ClipboardList className="w-12 h-12 text-slate-200 mx-auto mb-3" />
          <p className="text-slate-500 font-medium">No applications yet</p>
          <p className="text-slate-400 text-sm mt-1">Browse jobs and apply to see them here</p>
        </div>
      ) : (
        <div className="space-y-3">
          {apps.map((app: any) => {
            const config = STATUS_CONFIG[app.status] || STATUS_CONFIG.applied;
            return (
              <div key={app.id} className="card p-5">
                <div className="flex items-center gap-4">
                  <div className="w-1 self-stretch rounded-full" style={{ backgroundColor: app.status === "shortlisted" || app.status === "offered" ? "#22c55e" : app.status === "rejected" ? "#ef4444" : app.status === "interview" ? "#8b5cf6" : "#3b82f6" }} />
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="font-semibold text-slate-900">{app.job_title}</h3>
                      <span className={`badge flex items-center gap-1 ${config.color}`}>
                        {config.icon} {config.label}
                      </span>
                    </div>
                    <p className="text-sm text-slate-500">{app.company}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-400">{new Date(app.applied_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</p>
                    {app.ai_score > 0 && (
                      <p className="text-xs text-slate-600 mt-1">AI Score: <span className="font-semibold">{app.ai_score?.toFixed(1)}</span></p>
                    )}
                    {app.overall_rank && (
                      <p className="text-xs text-primary-600 font-medium">Rank #{app.overall_rank}</p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
