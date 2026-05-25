"use client";
import { useQuery } from "@tanstack/react-query";
import { recruiterApi, jobsApi } from "@/lib/api";
import { StatCard } from "@/components/shared/StatCard";
import { Briefcase, Users, UserCheck, TrendingUp } from "lucide-react";
import Link from "next/link";

export default function RecruiterDashboard() {
  const { data: dashboard } = useQuery({ queryKey: ["recruiter-dashboard"], queryFn: () => recruiterApi.getDashboard().then(r => r.data) });
  const { data: jobs = [] } = useQuery({ queryKey: ["recruiter-jobs-preview"], queryFn: () => jobsApi.list().then(r => r.data) });

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Welcome back, {dashboard?.recruiter_name || "Recruiter"}</h1>
          <p className="text-slate-500 mt-1">{dashboard?.company_name || "Your company"}</p>
        </div>
        <Link href="/recruiter/jobs/new" className="btn-primary">Post a Job</Link>
      </div>

      <div className="grid grid-cols-4 gap-6">
        <StatCard title="Total Jobs" value={dashboard?.total_jobs || 0} subtitle={`${dashboard?.active_jobs || 0} active`} icon={<Briefcase className="w-6 h-6" />} color="blue" />
        <StatCard title="Total Applicants" value={dashboard?.total_applicants || 0} icon={<Users className="w-6 h-6" />} color="purple" />
        <StatCard title="Shortlisted" value={dashboard?.shortlisted || 0} icon={<UserCheck className="w-6 h-6" />} color="green" />
        <StatCard title="Active Jobs" value={dashboard?.active_jobs || 0} icon={<TrendingUp className="w-6 h-6" />} color="orange" />
      </div>

      <div className="grid grid-cols-2 gap-8">
        {/* Recent Jobs */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-slate-900">Recent Jobs</h2>
            <Link href="/recruiter/jobs" className="text-sm text-primary-600 hover:underline">View all</Link>
          </div>
          <div className="space-y-3">
            {jobs.slice(0, 5).map((job: any) => (
              <Link key={job.id} href={`/recruiter/jobs/${job.id}`} className="flex items-center justify-between p-3 hover:bg-slate-50 rounded-lg transition-colors">
                <div>
                  <p className="text-sm font-medium text-slate-900">{job.title}</p>
                  <p className="text-xs text-slate-400">{job.application_count} applicants</p>
                </div>
                <span className={`badge ${job.status === "active" ? "badge-green" : "badge-slate"}`}>{job.status}</span>
              </Link>
            ))}
            {jobs.length === 0 && <p className="text-sm text-slate-400 text-center py-4">No jobs posted yet</p>}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card p-6">
          <h2 className="font-semibold text-slate-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Post New Job", href: "/recruiter/jobs/new", color: "bg-primary-50 text-primary-700 hover:bg-primary-100" },
              { label: "View All Jobs", href: "/recruiter/jobs", color: "bg-purple-50 text-purple-700 hover:bg-purple-100" },
            ].map(action => (
              <Link key={action.href} href={action.href} className={`p-4 rounded-lg text-sm font-medium transition-colors text-center ${action.color}`}>
                {action.label}
              </Link>
            ))}
          </div>

          <div className="mt-6 p-4 bg-primary-50 rounded-lg border border-primary-100">
            <p className="text-sm font-medium text-primary-900">AI-Powered Insights</p>
            <p className="text-xs text-primary-700 mt-1">Get intelligent hiring recommendations for your open positions using our AI engine.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
