"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";
import { jobsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Plus, X, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function NewJobPage() {
  const router = useRouter();
  const [skills, setSkills] = useState<Array<{ name: string; importance: string }>>([]);
  const [skillInput, setSkillInput] = useState("");
  const [importance, setImportance] = useState("required");

  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: { title: "", description: "", company: "", location: "", job_type: "full_time", experience_required: 0, salary_min: "", salary_max: "" }
  });

  const mutation = useMutation({
    mutationFn: (data: any) => jobsApi.create(data),
    onSuccess: (res) => {
      toast.success("Job posted!");
      router.push(`/recruiter/jobs/${res.data.id}`);
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Failed to create job"),
  });

  const addSkill = () => {
    if (!skillInput.trim()) return;
    setSkills(prev => [...prev, { name: skillInput.trim(), importance }]);
    setSkillInput("");
  };

  const onSubmit = (data: any) => {
    mutation.mutate({ ...data, experience_required: parseFloat(data.experience_required) || 0, skills });
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/recruiter/jobs" className="btn-secondary p-2"><ArrowLeft className="w-4 h-4" /></Link>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Post a New Job</h1>
          <p className="text-slate-500 text-sm mt-1">Fill in the details to attract top candidates</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="card p-6 space-y-4">
          <h2 className="font-semibold text-slate-900">Job Details</h2>
          <div>
            <label className="label">Job Title *</label>
            <input {...register("title", { required: true })} className="input" placeholder="e.g. Senior Frontend Developer" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Company</label>
              <input {...register("company")} className="input" placeholder="Company name" />
            </div>
            <div>
              <label className="label">Location</label>
              <input {...register("location")} className="input" placeholder="City, Country or Remote" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Job Type</label>
              <select {...register("job_type")} className="input">
                <option value="full_time">Full Time</option>
                <option value="part_time">Part Time</option>
                <option value="contract">Contract</option>
                <option value="internship">Internship</option>
                <option value="remote">Remote</option>
              </select>
            </div>
            <div>
              <label className="label">Experience Required (years)</label>
              <input {...register("experience_required")} type="number" min="0" step="0.5" className="input" placeholder="0" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Min Salary (optional)</label>
              <input {...register("salary_min")} type="number" className="input" placeholder="50000" />
            </div>
            <div>
              <label className="label">Max Salary (optional)</label>
              <input {...register("salary_max")} type="number" className="input" placeholder="80000" />
            </div>
          </div>
          <div>
            <label className="label">Job Description *</label>
            <textarea {...register("description", { required: true })} rows={6} className="input resize-none" placeholder="Describe responsibilities, requirements, and what you're looking for..." />
          </div>
        </div>

        {/* Skills */}
        <div className="card p-6 space-y-4">
          <h2 className="font-semibold text-slate-900">Required Skills</h2>
          <div className="flex gap-2">
            <input value={skillInput} onChange={e => setSkillInput(e.target.value)} onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addSkill())} className="input flex-1" placeholder="e.g. React, Python, AWS..." />
            <select value={importance} onChange={e => setImportance(e.target.value)} className="input w-36">
              <option value="required">Required</option>
              <option value="preferred">Preferred</option>
            </select>
            <button type="button" onClick={addSkill} className="btn-primary px-3"><Plus className="w-4 h-4" /></button>
          </div>
          <div className="flex flex-wrap gap-2">
            {skills.map((s, i) => (
              <span key={i} className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium ${s.importance === "required" ? "bg-primary-100 text-primary-800" : "bg-slate-100 text-slate-700"}`}>
                {s.name}
                <span className="text-xs opacity-60">({s.importance})</span>
                <button type="button" onClick={() => setSkills(prev => prev.filter((_, j) => j !== i))}><X className="w-3 h-3" /></button>
              </span>
            ))}
          </div>
        </div>

        <div className="flex gap-3">
          <button type="submit" disabled={mutation.isPending} className="btn-primary flex-1 py-3">
            {mutation.isPending ? "Posting..." : "Post Job"}
          </button>
          <Link href="/recruiter/jobs" className="btn-secondary px-6">Cancel</Link>
        </div>
      </form>
    </div>
  );
}
