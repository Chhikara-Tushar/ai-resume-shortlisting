"use client";
import { useQuery } from "@tanstack/react-query";
import { candidateApi } from "@/lib/api";
import { ScoreBar } from "@/components/shared/ScoreBar";
import { StatCard } from "@/components/shared/StatCard";
import { FileText, Briefcase, ClipboardList, TrendingUp, MapPin, AlertCircle } from "lucide-react";
import Link from "next/link";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer } from "recharts";

export default function CandidateDashboard() {
  const { data: profile } = useQuery({ queryKey: ["candidate-profile"], queryFn: () => candidateApi.getProfile().then(r => r.data) });
  const { data: ats } = useQuery({ queryKey: ["ats-score"], queryFn: () => candidateApi.getATSScore().then(r => r.data) });
  const { data: apps = [] } = useQuery({ queryKey: ["my-applications"], queryFn: () => candidateApi.getApplications().then(r => r.data) });
  const { data: jobs = [] } = useQuery({ queryKey: ["job-recommendations"], queryFn: () => candidateApi.getJobRecommendations().then(r => r.data) });

  const radarData = ats?.breakdown ? [
    { subject: "Contact", value: (ats.breakdown.contact_info / 20) * 100 },
    { subject: "Skills", value: (ats.breakdown.skills / 20) * 100 },
    { subject: "Experience", value: (ats.breakdown.experience / 20) * 100 },
    { subject: "Education", value: (ats.breakdown.education / 15) * 100 },
    { subject: "Format", value: (ats.breakdown.formatting / 15) * 100 },
  ] : [];

  const hasResume = !!profile?.resume_path;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Welcome, {profile?.full_name || "there"}</h1>
        <p className="text-slate-500 mt-1">Your career dashboard</p>
      </div>

      {!hasResume && (
        <div className="card p-5 border-l-4 border-primary-500 bg-primary-50">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-primary-600" />
            <div className="flex-1">
              <p className="font-medium text-primary-900">Upload your resume to get started</p>
              <p className="text-sm text-primary-700">Get an AI-powered ATS score, skill analysis, and job recommendations</p>
            </div>
            <Link href="/candidate/resume" className="btn-primary text-sm">Upload Resume</Link>
          </div>
        </div>
      )}

      <div className="grid grid-cols-4 gap-6">
        <StatCard title="ATS Score" value={`${ats?.total_score?.toFixed(0) || 0}/100`} icon={<TrendingUp className="w-6 h-6" />} color="blue" />
        <StatCard title="Skills" value={profile?.skills?.length || 0} subtitle="in your profile" icon={<TrendingUp className="w-6 h-6" />} color="green" />
        <StatCard title="Applications" value={apps.length} icon={<ClipboardList className="w-6 h-6" />} color="purple" />
        <StatCard title="Job Matches" value={jobs.length} icon={<Briefcase className="w-6 h-6" />} color="orange" />
      </div>

      <div className="grid grid-cols-2 gap-8">
        {/* ATS Score breakdown */}
        <div className="card p-6">
          <h2 className="font-semibold text-slate-900 mb-4">ATS Score Breakdown</h2>
          {hasResume && ats?.breakdown ? (
            <div className="space-y-3">
              {Object.entries(ats.breakdown).map(([key, value]: [string, any]) => (
                <ScoreBar key={key} score={value} label={key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())} size="sm" />
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-slate-200 mx-auto mb-3" />
              <p className="text-sm text-slate-400">Upload a resume to see your ATS score</p>
            </div>
          )}
        </div>

        {/* Job Recommendations */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-slate-900">Top Job Matches</h2>
            <Link href="/candidate/jobs" className="text-sm text-primary-600 hover:underline">View all</Link>
          </div>
          <div className="space-y-3">
            {jobs.slice(0, 4).map((job: any) => (
              <Link key={job.job_id} href="/candidate/jobs" className="flex items-start justify-between p-3 hover:bg-slate-50 rounded-lg transition-colors">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 truncate">{job.title}</p>
                  <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                    {job.company && <span>{job.company}</span>}
                    {job.location && <span className="flex items-center gap-0.5"><MapPin className="w-3 h-3" />{job.location}</span>}
                  </div>
                </div>
                <span className="badge-green ml-2 shrink-0">{job.match_score?.toFixed(0)}% match</span>
              </Link>
            ))}
            {jobs.length === 0 && <p className="text-sm text-slate-400 text-center py-4">Upload resume for job recommendations</p>}
          </div>
        </div>
      </div>

      {/* Recent Applications */}
      {apps.length > 0 && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-slate-900">Recent Applications</h2>
            <Link href="/candidate/applications" className="text-sm text-primary-600 hover:underline">View all</Link>
          </div>
          <div className="space-y-3">
            {apps.slice(0, 4).map((app: any) => (
              <div key={app.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-slate-900">{app.job_title}</p>
                  <p className="text-xs text-slate-400">{app.company} · {new Date(app.applied_at).toLocaleDateString()}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`badge ${app.status === "shortlisted" ? "badge-green" : app.status === "rejected" ? "badge-red" : app.status === "interview" ? "badge-purple" : "badge-blue"}`}>{app.status}</span>
                  {app.ai_score > 0 && <span className="text-xs text-slate-500">Score: {app.ai_score?.toFixed(1)}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
