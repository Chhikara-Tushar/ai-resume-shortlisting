"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { jobsApi } from "@/lib/api";
import toast from "react-hot-toast";
import Link from "next/link";
import { Plus, MapPin, Clock, Users, ChevronRight, Briefcase } from "lucide-react";

export default function RecruiterJobs() {
  const qc = useQueryClient();
  const { data: jobs = [], isLoading } = useQuery({ queryKey: ["recruiter-jobs"], queryFn: () => jobsApi.list().then(r => r.data) });

  const closeMutation = useMutation({
    mutationFn: (id: string) => jobsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["recruiter-jobs"] }); toast.success("Job closed"); },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">My Jobs</h1>
          <p className="text-slate-500 mt-1">{jobs.length} jobs posted</p>
        </div>
        <Link href="/recruiter/jobs/new" className="btn-primary">
          <Plus className="w-4 h-4" /> Post Job
        </Link>
      </div>

      {isLoading ? (
        <div className="card p-8 text-center text-slate-400">Loading jobs...</div>
      ) : jobs.length === 0 ? (
        <div className="card p-12 text-center">
          <Briefcase className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500 font-medium">No jobs posted yet</p>
          <Link href="/recruiter/jobs/new" className="btn-primary mt-4 inline-flex">Post your first job</Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {jobs.map((job: any) => (
            <div key={job.id} className="card p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-slate-900 text-lg">{job.title}</h3>
                    <span className={`badge ${job.status === "active" ? "badge-green" : "badge-slate"}`}>{job.status}</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-slate-500">
                    {job.company && <span className="flex items-center gap-1"><Briefcase className="w-3.5 h-3.5" />{job.company}</span>}
                    {job.location && <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{job.location}</span>}
                    <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" />{job.job_type?.replace("_", " ")}</span>
                    <span className="flex items-center gap-1"><Users className="w-3.5 h-3.5" />{job.application_count} applicants</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  {job.status === "active" && (
                    <button onClick={() => closeMutation.mutate(job.id)} className="btn-secondary text-xs px-3 py-1.5">Close</button>
                  )}
                  <Link href={`/recruiter/jobs/${job.id}`} className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1">
                    View <ChevronRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
