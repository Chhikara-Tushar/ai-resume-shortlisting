"use client";
import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { candidateApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Save, Plus, X, Lightbulb } from "lucide-react";

export default function CandidateProfile() {
  const qc = useQueryClient();
  const [form, setForm] = useState<any>({});
  const [skillInput, setSkillInput] = useState("");

  const { data: profile } = useQuery({ queryKey: ["candidate-profile"], queryFn: () => candidateApi.getProfile().then(r => r.data) });
  const { data: skillRecs } = useQuery({ queryKey: ["skill-recommendations"], queryFn: () => candidateApi.getSkillRecommendations().then(r => r.data), retry: false });

  useEffect(() => {
    if (profile) setForm({ full_name: profile.full_name, phone: profile.phone || "", location: profile.location || "", linkedin_url: profile.linkedin_url || "", github_url: profile.github_url || "", portfolio_url: profile.portfolio_url || "" });
  }, [profile]);

  const updateMutation = useMutation({
    mutationFn: () => candidateApi.updateProfile(form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["candidate-profile"] }); toast.success("Profile updated"); },
  });

  const addSkillMutation = useMutation({
    mutationFn: (name: string) => candidateApi.addSkill({ name }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["candidate-profile"] }); setSkillInput(""); },
  });

  const removeSkillMutation = useMutation({
    mutationFn: (name: string) => candidateApi.removeSkill(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["candidate-profile"] }),
  });

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">My Profile</h1>
        <p className="text-slate-500 mt-1">Keep your information up to date</p>
      </div>

      <div className="card p-6 space-y-4">
        <h2 className="font-semibold text-slate-900">Personal Information</h2>
        <div className="grid grid-cols-2 gap-4">
          {[
            { key: "full_name", label: "Full Name", type: "text" },
            { key: "phone", label: "Phone", type: "tel" },
            { key: "location", label: "Location", type: "text" },
            { key: "linkedin_url", label: "LinkedIn URL", type: "url" },
            { key: "github_url", label: "GitHub URL", type: "url" },
            { key: "portfolio_url", label: "Portfolio URL", type: "url" },
          ].map(field => (
            <div key={field.key}>
              <label className="label">{field.label}</label>
              <input type={field.type} value={form[field.key] || ""} onChange={e => setForm((p: any) => ({ ...p, [field.key]: e.target.value }))} className="input" />
            </div>
          ))}
        </div>
        <button onClick={() => updateMutation.mutate()} disabled={updateMutation.isPending} className="btn-primary">
          <Save className="w-4 h-4" />
          {updateMutation.isPending ? "Saving..." : "Save Changes"}
        </button>
      </div>

      <div className="card p-6 space-y-4">
        <h2 className="font-semibold text-slate-900">Skills</h2>
        <div className="flex gap-2">
          <input value={skillInput} onChange={e => setSkillInput(e.target.value)} onKeyDown={e => e.key === "Enter" && skillInput.trim() && addSkillMutation.mutate(skillInput.trim())} className="input flex-1" placeholder="Add a skill..." />
          <button onClick={() => skillInput.trim() && addSkillMutation.mutate(skillInput.trim())} className="btn-primary px-3"><Plus className="w-4 h-4" /></button>
        </div>
        <div className="flex flex-wrap gap-2">
          {profile?.skills?.map((s: any) => (
            <span key={s.name} className="inline-flex items-center gap-1.5 bg-primary-100 text-primary-800 px-3 py-1 rounded-full text-sm font-medium">
              {s.name}
              <button onClick={() => removeSkillMutation.mutate(s.name)}><X className="w-3 h-3" /></button>
            </span>
          ))}
        </div>
      </div>

      {skillRecs?.recommendations?.length > 0 && (
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="w-5 h-5 text-yellow-500" />
            <h2 className="font-semibold text-slate-900">AI Skill Recommendations</h2>
          </div>
          <p className="text-sm text-slate-500 mb-3">Skills to learn based on your profile and market demand</p>
          <div className="flex flex-wrap gap-2">
            {skillRecs.recommendations.map((skill: string) => (
              <button key={skill} onClick={() => addSkillMutation.mutate(skill)} className="inline-flex items-center gap-1 bg-yellow-50 text-yellow-800 border border-yellow-200 px-3 py-1 rounded-full text-sm hover:bg-yellow-100 transition-colors">
                <Plus className="w-3 h-3" /> {skill}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
