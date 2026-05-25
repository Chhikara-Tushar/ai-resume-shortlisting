import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost/api";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE}/v1/auth/refresh`, { refresh_token: refreshToken });
          const { access_token, refresh_token } = res.data;
          localStorage.setItem("access_token", access_token);
          localStorage.setItem("refresh_token", refresh_token);
          error.config.headers.Authorization = `Bearer ${access_token}`;
          return api.request(error.config);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      } else {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  register: (data: { email: string; password: string; full_name: string; role: string }) =>
    api.post("/v1/auth/register", data),
  login: (data: { email: string; password: string }) => api.post("/v1/auth/login", data),
  me: () => api.get("/v1/auth/me"),
};

// Admin
export const adminApi = {
  getUsers: (params?: { skip?: number; limit?: number; role?: string; search?: string }) =>
    api.get("/v1/admin/users", { params }),
  createUser: (data: object) => api.post("/v1/admin/users", data),
  updateUser: (id: string, data: object) => api.put(`/v1/admin/users/${id}`, data),
  deleteUser: (id: string) => api.delete(`/v1/admin/users/${id}`),
  getAnalyticsOverview: () => api.get("/v1/admin/analytics/overview"),
  getAnalyticsTrends: (days?: number) => api.get("/v1/admin/analytics/trends", { params: { days } }),
  getRecruiters: () => api.get("/v1/admin/recruiters"),
  getSettings: () => api.get("/v1/admin/system/settings"),
  updateSettings: (settings: Record<string, string>) => api.put("/v1/admin/system/settings", { settings }),
};

// Jobs
export const jobsApi = {
  create: (data: object) => api.post("/v1/jobs", data),
  list: (params?: { status?: string }) => api.get("/v1/jobs", { params }),
  get: (id: string) => api.get(`/v1/jobs/${id}`),
  update: (id: string, data: object) => api.put(`/v1/jobs/${id}`, data),
  delete: (id: string) => api.delete(`/v1/jobs/${id}`),
  getRankedCandidates: (id: string, minScore?: number) =>
    api.get(`/v1/jobs/${id}/candidates`, { params: { min_score: minScore } }),
  shortlistCandidate: (jobId: string, candidateId: string) =>
    api.post(`/v1/jobs/${jobId}/candidates/${candidateId}/shortlist`),
  rejectCandidate: (jobId: string, candidateId: string) =>
    api.post(`/v1/jobs/${jobId}/candidates/${candidateId}/reject`),
  getInsights: (id: string) => api.get(`/v1/jobs/${id}/insights`),
  compareCandidates: (id: string, ids: string[]) =>
    api.get(`/v1/jobs/${id}/compare`, { params: { ids: ids.join(",") } }),
};

// Recruiter
export const recruiterApi = {
  getDashboard: () => api.get("/v1/recruiter/dashboard"),
  updateProfile: (data: object) => api.put("/v1/recruiter/profile", data),
  suggestSkills: (q: string) => api.get("/v1/recruiter/skills/suggest", { params: { q } }),
};

// Candidate
export const candidateApi = {
  getProfile: () => api.get("/v1/candidate/profile"),
  updateProfile: (data: object) => api.put("/v1/candidate/profile", data),
  addSkill: (data: { name: string; proficiency_level?: string; years_of_experience?: number }) =>
    api.post("/v1/candidate/skills", data),
  removeSkill: (name: string) => api.delete(`/v1/candidate/skills/${name}`),
  uploadResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/v1/candidate/resume/upload", form, { headers: { "Content-Type": "multipart/form-data" } });
  },
  getResumeAnalysis: () => api.get("/v1/candidate/resume/analysis"),
  getATSScore: () => api.get("/v1/candidate/ats-score"),
  getSkillGaps: (jobId?: string) => api.get("/v1/candidate/skill-gaps", { params: { job_id: jobId } }),
  getJobRecommendations: () => api.get("/v1/candidate/recommendations/jobs"),
  getSkillRecommendations: () => api.get("/v1/candidate/recommendations/skills"),
  getApplications: () => api.get("/v1/candidate/applications"),
  apply: (jobId: string) => api.post(`/v1/candidate/apply/${jobId}`),
};

// AI
export const aiApi = {
  chat: (data: { message: string; session_id?: string }) => api.post("/v1/ai/chat", data),
};
