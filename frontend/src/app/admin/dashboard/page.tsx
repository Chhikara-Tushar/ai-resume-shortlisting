"use client";
import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import { StatCard } from "@/components/shared/StatCard";
import { Users, Briefcase, ClipboardList, TrendingUp, Brain } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

export default function AdminDashboard() {
  const { data: overview } = useQuery({ queryKey: ["admin-overview"], queryFn: () => adminApi.getAnalyticsOverview().then(r => r.data) });
  const { data: trends } = useQuery({ queryKey: ["admin-trends"], queryFn: () => adminApi.getAnalyticsTrends(30).then(r => r.data) });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Admin Dashboard</h1>
        <p className="text-slate-500 mt-1">Platform overview and analytics</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-6">
        <StatCard title="Total Users" value={overview?.total_users || 0} subtitle={`${overview?.total_candidates || 0} candidates, ${overview?.total_recruiters || 0} recruiters`} icon={<Users className="w-6 h-6" />} color="blue" />
        <StatCard title="Total Jobs" value={overview?.total_jobs || 0} subtitle={`${overview?.active_jobs || 0} active`} icon={<Briefcase className="w-6 h-6" />} color="purple" />
        <StatCard title="Applications" value={overview?.total_applications || 0} icon={<ClipboardList className="w-6 h-6" />} color="green" />
        <StatCard title="Avg AI Score" value={`${overview?.avg_ai_score?.toFixed(1) || "0.0"}%`} icon={<Brain className="w-6 h-6" />} color="orange" />
      </div>

      {/* Activity Trends Chart */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-6">Activity Trends (30 days)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trends || []}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#94a3b8" />
            <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
            <Tooltip contentStyle={{ borderRadius: "8px", border: "1px solid #e2e8f0" }} />
            <Legend />
            <Line type="monotone" dataKey="new_users" stroke="#3b82f6" name="New Users" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="new_jobs" stroke="#8b5cf6" name="New Jobs" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="new_applications" stroke="#10b981" name="Applications" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-6">
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">User Distribution</h3>
          <div className="space-y-3">
            {[
              { label: "Candidates", value: overview?.total_candidates || 0, color: "bg-blue-500" },
              { label: "Recruiters", value: overview?.total_recruiters || 0, color: "bg-purple-500" },
            ].map(item => (
              <div key={item.label}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-600">{item.label}</span>
                  <span className="font-medium">{item.value}</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full">
                  <div className={`h-2 rounded-full ${item.color}`} style={{ width: `${Math.min((item.value / (overview?.total_users || 1)) * 100, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Job Status</h3>
          <div className="space-y-3">
            {[
              { label: "Active Jobs", value: overview?.active_jobs || 0, color: "bg-green-500" },
              { label: "Closed Jobs", value: (overview?.total_jobs || 0) - (overview?.active_jobs || 0), color: "bg-slate-400" },
            ].map(item => (
              <div key={item.label}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-600">{item.label}</span>
                  <span className="font-medium">{item.value}</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full">
                  <div className={`h-2 rounded-full ${item.color}`} style={{ width: `${Math.min((item.value / (overview?.total_jobs || 1)) * 100, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Platform Health</h3>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span className="text-sm text-slate-600">AI Engine</span>
              <span className="ml-auto text-xs text-green-600 font-medium">Online</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span className="text-sm text-slate-600">Database</span>
              <span className="ml-auto text-xs text-green-600 font-medium">Online</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span className="text-sm text-slate-600">Vector Search</span>
              <span className="ml-auto text-xs text-green-600 font-medium">Online</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
