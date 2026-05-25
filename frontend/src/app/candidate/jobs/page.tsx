"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { candidateApi, jobsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { MapPin, Clock, Briefcase, TrendingUp, X } from "lucide-react";

export default function CandidateJobs() {
  const qc = useQueryClient();
  const [selectedJob, setSelectedJob] = useState<any>(null);

  const { data: recs = [] } = useQuery({ queryKey: ["job-recommendations"], queryFn: () => candidateApi.getJobRecommendations().then(r => r.data) });
  const { data: allJobs = [] } = useQuery({ queryKey: ["all-jobs"], queryFn: () => jobsApi.list({ status: "active" }).then(r => r.data) });
  const { data: apps = [] } = useQuery({ queryKey: ["my-applications"], queryFn: () => candidateApi.getApplications().then(r => r.data) });

  const appliedJobIds = new Set(apps.map((a: any) => a.job_id));

  const applyMutation = useMutation({
    mutationFn: (jobId: string) => candidateApi.apply(jobId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["my-applications"] }); toast.success("Applied successfully!"); },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Failed to apply"),
  });

  const recommendedIds = new Set(recs.map((r: any) => r.job_id));
  const otherJobs = allJobs.filter((j: any) => !recommendedIds.has(j.id));

  const renderJob = (job: any, matchScore?: number) => (
    <div key={job.job_id || job.id} className={`card p-5 cursor-pointer transition-all hover:shadow-md ${selectedJob?.id === (job.job_id || job.id) ? "ring-2 ring-primary-500" : ""}`} onClick={() => setSelectedJob({ ...job, id: job.job_id || job.id })}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-slate-900">{job.title}</h3>
            {matchScore && <span className="badge-green text-xs">{matchScore?.toFixed(0)}% match</span>}
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-500">
            {job.company && <span className="flex items-center gap-1"><Briefcase className="w-3.5 h-3.5" />{job.company}</span>}
            {job.location && <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{job.location}</span>}
            <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" />{(job.job_type || "").replace("_", " ")}</span>
          </div>
          {job.matching_skills?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {job.matching_skills.slice(0, 4).map((s: string) => <span key={s} className="badge-green text-xs">{s}</span>)}
              {job.missing_skills?.slice(0, 2).map((s: string) => <span key={s} className="badge-red text-xs">{s}</span>)}
            </div>
          )}
        </div>
        <div className="flex flex-col items-end gap-2">
          {appliedJobIds.has(job.job_id || job.id) ? (
            <span className="badge-green">Applied</span>
          ) : (
            <button
              onClick={(e) => { e.stopPropagation(); applyMutation.mutate(job.job_id || job.id); }}
              disabled={applyMutation.isPending}
              className="btn-primary text-xs px-4"
            >
              Apply
            </button>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Browse Jobs</h1>
        <p className="text-slate-500 mt-1">{allJobs.length} jobs available · {recs.length} AI-matched for you</p>
      </div>

      {recs.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary-600" /> AI Job Recommendations
          </h2>
          <div className="space-y-3">
            {recs.map((job: any) => renderJob(job, job.match_score))}
          </div>
        </div>
      )}

      {otherJobs.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-slate-900 mb-3">All Jobs</h2>
          <div className="space-y-3">
            {otherJobs.map((job: any) => renderJob(job))}
          </div>
        </div>
      )}

      {allJobs.length === 0 && (
        <div className="card p-12 text-center">
          <Briefcase className="w-12 h-12 text-slate-200 mx-auto mb-3" />
          <p className="text-slate-500">No jobs available at this time</p>
        </div>
      )}
    </div>
  );
}
