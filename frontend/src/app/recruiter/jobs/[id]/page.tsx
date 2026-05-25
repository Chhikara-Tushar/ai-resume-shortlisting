"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { jobsApi } from "@/lib/api";
import { ScoreBar, ScoreBadge } from "@/components/shared/ScoreBar";
import toast from "react-hot-toast";
import { ArrowLeft, Brain, UserCheck, UserX, Users, Lightbulb, BarChart2 } from "lucide-react";
import Link from "next/link";

const TABS = ["Candidates", "Insights", "Compare"];

export default function JobDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const qc = useQueryClient();
  const [tab, setTab] = useState("Candidates");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [compareMode, setCompareMode] = useState(false);

  const { data: job } = useQuery({ queryKey: ["job", id], queryFn: () => jobsApi.get(id).then(r => r.data) });
  const { data: candidates = [], isLoading: loadingCandidates } = useQuery({
    queryKey: ["job-candidates", id],
    queryFn: () => jobsApi.getRankedCandidates(id).then(r => r.data),
    enabled: tab === "Candidates",
  });
  const { data: insights, isLoading: loadingInsights } = useQuery({
    queryKey: ["job-insights", id],
    queryFn: () => jobsApi.getInsights(id).then(r => r.data),
    enabled: tab === "Insights",
  });
  const { data: comparison, isLoading: loadingCompare } = useQuery({
    queryKey: ["job-compare", id, selectedIds.join(",")],
    queryFn: () => jobsApi.compareCandidates(id, selectedIds).then(r => r.data),
    enabled: tab === "Compare" && selectedIds.length >= 2,
  });

  const shortlistMutation = useMutation({
    mutationFn: (cid: string) => jobsApi.shortlistCandidate(id, cid),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["job-candidates", id] }); toast.success("Shortlisted!"); },
  });
  const rejectMutation = useMutation({
    mutationFn: (cid: string) => jobsApi.rejectCandidate(id, cid),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["job-candidates", id] }); toast.success("Rejected"); },
  });

  const toggleSelect = (cid: string) => {
    setSelectedIds(prev => prev.includes(cid) ? prev.filter(x => x !== cid) : [...prev, cid].slice(0, 4));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/recruiter/jobs" className="btn-secondary p-2"><ArrowLeft className="w-4 h-4" /></Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-slate-900">{job?.title || "Loading..."}</h1>
          <p className="text-slate-500 text-sm">{job?.company} · {job?.location} · {job?.application_count} applicants</p>
        </div>
        <span className={`badge ${job?.status === "active" ? "badge-green" : "badge-slate"}`}>{job?.status}</span>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 flex gap-6">
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)} className={`pb-3 text-sm font-medium border-b-2 transition-colors ${tab === t ? "border-primary-600 text-primary-600" : "border-transparent text-slate-500 hover:text-slate-700"}`}>
            {t}
          </button>
        ))}
      </div>

      {/* Candidates Tab */}
      {tab === "Candidates" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">{candidates.length} candidates ranked by AI</p>
            <button onClick={() => { setTab("Compare"); setCompareMode(true); }} className="btn-secondary text-xs" disabled={selectedIds.length < 2}>
              Compare ({selectedIds.length}/4)
            </button>
          </div>

          {loadingCandidates ? (
            <div className="card p-8 text-center text-slate-400">Ranking candidates with AI...</div>
          ) : (
            <div className="space-y-3">
              {candidates.map((c: any) => (
                <div key={c.candidate_id} className={`card p-5 transition-all ${selectedIds.includes(c.candidate_id) ? "ring-2 ring-primary-500" : ""}`}>
                  <div className="flex items-start gap-4">
                    <div className="flex items-center gap-3">
                      <input type="checkbox" checked={selectedIds.includes(c.candidate_id)} onChange={() => toggleSelect(c.candidate_id)} className="w-4 h-4 rounded border-slate-300 text-primary-600" />
                      <div className="w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-sm font-bold">
                        #{c.overall_rank}
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <p className="font-semibold text-slate-900">{c.full_name}</p>
                        <span className={`badge ${c.status === "shortlisted" ? "badge-green" : c.status === "rejected" ? "badge-red" : "badge-blue"}`}>{c.status}</span>
                        <ScoreBadge score={c.ai_score} />
                      </div>
                      <p className="text-sm text-slate-500 mb-3">{c.email} · {c.experience_years}y exp · ATS: {c.ats_score?.toFixed(0)}</p>
                      <div className="grid grid-cols-3 gap-3 mb-3">
                        <ScoreBar score={c.semantic_score} label="Semantic Match" size="sm" />
                        <ScoreBar score={c.skill_match_score} label="Skill Match" size="sm" />
                        <ScoreBar score={c.experience_score} label="Experience" size="sm" />
                      </div>
                      {c.skills?.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {c.skills.slice(0, 6).map((s: string) => <span key={s} className="badge-blue">{s}</span>)}
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col gap-2 ml-4">
                      <button onClick={() => shortlistMutation.mutate(c.candidate_id)} disabled={c.status === "shortlisted"} className="btn-secondary text-xs px-3 flex items-center gap-1">
                        <UserCheck className="w-3.5 h-3.5" /> Shortlist
                      </button>
                      <button onClick={() => rejectMutation.mutate(c.candidate_id)} disabled={c.status === "rejected"} className="btn-danger text-xs px-3 flex items-center gap-1">
                        <UserX className="w-3.5 h-3.5" /> Reject
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Insights Tab */}
      {tab === "Insights" && (
        <div className="space-y-6">
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Brain className="w-5 h-5 text-primary-600" />
              <h2 className="font-semibold text-slate-900">AI Hiring Insights</h2>
              {insights?.cached && <span className="badge-slate text-xs">Cached</span>}
            </div>
            {loadingInsights ? (
              <div className="text-slate-400 text-sm animate-pulse">Generating insights with AI...</div>
            ) : (
              <p className="text-slate-700 leading-relaxed">{insights?.insights || "No insights available yet. Add candidates to generate insights."}</p>
            )}
          </div>

          <div className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <BarChart2 className="w-5 h-5 text-purple-600" />
              <h2 className="font-semibold text-slate-900">Required Skills</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {job?.skills?.map((s: any) => (
                <span key={s.name} className={`badge ${s.importance === "required" ? "badge-blue" : "badge-slate"}`}>
                  {s.name} <span className="opacity-60 ml-1">({s.importance})</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Compare Tab */}
      {tab === "Compare" && (
        <div className="space-y-4">
          {selectedIds.length < 2 ? (
            <div className="card p-8 text-center">
              <p className="text-slate-500">Select 2-4 candidates from the Candidates tab to compare them side by side.</p>
            </div>
          ) : loadingCompare ? (
            <div className="card p-8 text-center text-slate-400">Loading comparison...</div>
          ) : (
            <div className="overflow-x-auto">
              <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${comparison?.candidates?.length || 2}, 1fr)` }}>
                {comparison?.candidates?.map((c: any) => (
                  <div key={c.candidate_id} className="card p-5 space-y-4">
                    <div>
                      <p className="font-bold text-slate-900 text-lg">{c.full_name}</p>
                      <p className="text-sm text-slate-500">{c.email}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 mb-1">AI Score</p>
                      <ScoreBar score={c.ai_score} size="lg" />
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div><span className="text-slate-400">Experience</span><p className="font-semibold">{c.experience_years}y</p></div>
                      <div><span className="text-slate-400">ATS Score</span><p className="font-semibold">{c.ats_score?.toFixed(0)}</p></div>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 mb-2">Skills</p>
                      <div className="flex flex-wrap gap-1">
                        {c.skills?.slice(0, 8).map((s: string) => <span key={s} className="badge-blue text-xs">{s}</span>)}
                      </div>
                    </div>
                    <span className={`badge w-full justify-center ${c.status === "shortlisted" ? "badge-green" : c.status === "rejected" ? "badge-red" : "badge-blue"}`}>{c.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
