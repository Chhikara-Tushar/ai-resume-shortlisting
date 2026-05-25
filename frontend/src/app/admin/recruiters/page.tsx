"use client";
import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import { Building2, Briefcase, Users } from "lucide-react";

export default function AdminRecruiters() {
  const { data: recruiters = [], isLoading } = useQuery({
    queryKey: ["admin-recruiters"],
    queryFn: () => adminApi.getRecruiters().then(r => r.data),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Recruiter Management</h1>
        <p className="text-slate-500 mt-1">{recruiters.length} recruiters on platform</p>
      </div>

      <div className="grid gap-4">
        {isLoading ? (
          <div className="card p-8 text-center text-slate-400">Loading...</div>
        ) : recruiters.map((r: any) => (
          <div key={r.id} className="card p-6 flex items-center gap-6">
            <div className="w-12 h-12 bg-purple-100 text-purple-700 rounded-xl flex items-center justify-center text-lg font-bold">
              {r.full_name?.charAt(0)}
            </div>
            <div className="flex-1">
              <p className="font-semibold text-slate-900">{r.full_name}</p>
              <p className="text-sm text-slate-500">{r.email}</p>
              {r.company_name && (
                <div className="flex items-center gap-1 text-xs text-slate-400 mt-1">
                  <Building2 className="w-3 h-3" />
                  {r.company_name}
                </div>
              )}
            </div>
            <div className="flex gap-6 text-center">
              <div>
                <div className="flex items-center gap-1 text-slate-600">
                  <Briefcase className="w-4 h-4" />
                  <span className="font-bold text-lg">{r.job_count}</span>
                </div>
                <p className="text-xs text-slate-400">Jobs</p>
              </div>
              <div>
                <div className="flex items-center gap-1 text-slate-600">
                  <Users className="w-4 h-4" />
                  <span className="font-bold text-lg">{r.application_count}</span>
                </div>
                <p className="text-xs text-slate-400">Applicants</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-400">Joined</p>
              <p className="text-sm text-slate-600">{new Date(r.created_at).toLocaleDateString()}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
