"use client";
import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useDropzone } from "react-dropzone";
import { candidateApi } from "@/lib/api";
import { ScoreBar } from "@/components/shared/ScoreBar";
import toast from "react-hot-toast";
import { Upload, FileText, CheckCircle2, AlertTriangle, Brain } from "lucide-react";

export default function ResumePage() {
  const qc = useQueryClient();
  const [uploadResult, setUploadResult] = useState<any>(null);

  const { data: analysis, isLoading } = useQuery({
    queryKey: ["resume-analysis"],
    queryFn: () => candidateApi.getResumeAnalysis().then(r => r.data),
    retry: false,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => candidateApi.uploadResume(file),
    onSuccess: (res) => {
      setUploadResult(res.data);
      qc.invalidateQueries({ queryKey: ["resume-analysis"] });
      qc.invalidateQueries({ queryKey: ["ats-score"] });
      qc.invalidateQueries({ queryKey: ["candidate-profile"] });
      toast.success("Resume uploaded and analyzed!");
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Upload failed"),
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles[0]) uploadMutation.mutate(acceptedFiles[0]);
  }, [uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"] },
    maxFiles: 1,
  });

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">My Resume</h1>
        <p className="text-slate-500 mt-1">Upload and analyze your resume with AI</p>
      </div>

      {/* Upload zone */}
      <div {...getRootProps()} className={`card p-10 text-center cursor-pointer border-2 border-dashed transition-colors ${isDragActive ? "border-primary-400 bg-primary-50" : "border-slate-200 hover:border-primary-300 hover:bg-slate-50"}`}>
        <input {...getInputProps()} />
        {uploadMutation.isPending ? (
          <div className="space-y-2">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600 mx-auto" />
            <p className="text-slate-600 font-medium">Analyzing with AI...</p>
            <p className="text-slate-400 text-sm">Parsing resume, extracting skills, computing ATS score...</p>
          </div>
        ) : (
          <>
            <Upload className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="font-medium text-slate-700">{isDragActive ? "Drop to upload" : "Drag & drop your resume"}</p>
            <p className="text-sm text-slate-400 mt-1">or click to browse · PDF, DOCX · Max 10MB</p>
          </>
        )}
      </div>

      {/* Upload result */}
      {uploadResult && (
        <div className="card p-5 border-l-4 border-green-500 bg-green-50">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
            <p className="font-medium text-green-900">Resume analyzed successfully</p>
          </div>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div><span className="text-green-700">ATS Score</span><p className="font-bold text-green-900">{uploadResult.ats_score?.toFixed(1)}/100</p></div>
            <div><span className="text-green-700">Skills Found</span><p className="font-bold text-green-900">{uploadResult.skills_extracted}</p></div>
            <div><span className="text-green-700">Experience</span><p className="font-bold text-green-900">{uploadResult.experience_years?.toFixed(1)}y</p></div>
          </div>
        </div>
      )}

      {/* Analysis */}
      {isLoading ? (
        <div className="card p-8 text-center text-slate-400">Loading analysis...</div>
      ) : analysis ? (
        <div className="space-y-6">
          {/* ATS Score */}
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Brain className="w-5 h-5 text-primary-600" />
              <h2 className="font-semibold text-slate-900">ATS Score Analysis</h2>
              <span className="ml-auto text-2xl font-bold text-primary-600">{analysis.ats_score?.total_score?.toFixed(1)}/100</span>
            </div>
            <div className="space-y-3">
              {[
                { key: "contact_info_score", label: "Contact Info", max: 20 },
                { key: "skills_score", label: "Skills", max: 20 },
                { key: "experience_score", label: "Experience", max: 20 },
                { key: "education_score", label: "Education", max: 15 },
                { key: "formatting_score", label: "Formatting", max: 15 },
                { key: "keyword_density_score", label: "Keywords", max: 10 },
              ].map(({ key, label, max }) => (
                <div key={key} className="flex items-center gap-3">
                  <span className="text-sm text-slate-600 w-28 shrink-0">{label}</span>
                  <ScoreBar score={(analysis.ats_score?.[key] / max) * 100} size="sm" showLabel={false} />
                  <span className="text-xs text-slate-500 w-14 text-right">{analysis.ats_score?.[key]}/{max}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          {analysis.ats_score?.recommendations?.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-5 h-5 text-yellow-500" />
                <h2 className="font-semibold text-slate-900">Improvement Suggestions</h2>
              </div>
              <ul className="space-y-2">
                {analysis.ats_score.recommendations.map((r: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                    <span className="w-5 h-5 bg-yellow-100 text-yellow-700 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">{i + 1}</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Extracted info */}
          <div className="card p-6">
            <h2 className="font-semibold text-slate-900 mb-4">Extracted Information</h2>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-xs text-slate-400 mb-2">SKILLS DETECTED</p>
                <div className="flex flex-wrap gap-1.5">
                  {analysis.parsed_data?.skills?.map((s: string) => <span key={s} className="badge-blue">{s}</span>)}
                </div>
              </div>
              <div>
                <p className="text-xs text-slate-400 mb-2">EDUCATION</p>
                <div className="space-y-1">
                  {analysis.parsed_data?.education?.map((e: string, i: number) => (
                    <p key={i} className="text-sm text-slate-700">{e}</p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="card p-8 text-center">
          <FileText className="w-12 h-12 text-slate-200 mx-auto mb-3" />
          <p className="text-slate-500">Upload a resume to see your AI analysis</p>
        </div>
      )}
    </div>
  );
}
