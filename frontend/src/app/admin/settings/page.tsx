"use client";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Save, Settings } from "lucide-react";

const DEFAULT_SETTINGS = [
  { key: "max_upload_mb", description: "Maximum resume upload size (MB)", default: "10" },
  { key: "openai_model", description: "OpenAI model for AI insights", default: "gpt-4o-mini" },
  { key: "embedding_model", description: "Hugging Face embedding model", default: "sentence-transformers/all-MiniLM-L6-v2" },
  { key: "max_candidates_ranked", description: "Max candidates to rank per job", default: "100" },
  { key: "ats_minimum_score", description: "Minimum ATS score for applications", default: "0" },
];

export default function AdminSettings() {
  const qc = useQueryClient();
  const [values, setValues] = useState<Record<string, string>>({});

  const { data: settings = [] } = useQuery({
    queryKey: ["admin-settings"],
    queryFn: () => adminApi.getSettings().then(r => r.data),
  });

  useEffect(() => {
    const merged: Record<string, string> = {};
    DEFAULT_SETTINGS.forEach(s => { merged[s.key] = s.default; });
    settings.forEach((s: any) => { merged[s.key] = s.value || ""; });
    setValues(merged);
  }, [settings]);

  const mutation = useMutation({
    mutationFn: () => adminApi.updateSettings(values),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["admin-settings"] }); toast.success("Settings saved"); },
  });

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">System Settings</h1>
        <p className="text-slate-500 mt-1">Configure platform behavior and AI models</p>
      </div>

      <div className="card p-6 space-y-6">
        <div className="flex items-center gap-2 pb-4 border-b border-slate-200">
          <Settings className="w-5 h-5 text-primary-600" />
          <h2 className="font-semibold text-slate-900">Configuration</h2>
        </div>

        {DEFAULT_SETTINGS.map(setting => (
          <div key={setting.key}>
            <label className="label">{setting.key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}</label>
            <input
              value={values[setting.key] || ""}
              onChange={e => setValues(prev => ({ ...prev, [setting.key]: e.target.value }))}
              className="input"
              placeholder={setting.default}
            />
            <p className="text-xs text-slate-400 mt-1">{setting.description}</p>
          </div>
        ))}

        <button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="btn-primary">
          <Save className="w-4 h-4" />
          {mutation.isPending ? "Saving..." : "Save Settings"}
        </button>
      </div>
    </div>
  );
}
