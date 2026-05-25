"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import toast from "react-hot-toast";
import { Search, Plus, Pencil, Power, X } from "lucide-react";

interface UserForm {
  full_name: string;
  email: string;
  password: string;
  role: string;
}

export default function AdminUsers() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [editUser, setEditUser] = useState<any>(null);
  const [form, setForm] = useState<UserForm>({ full_name: "", email: "", password: "", role: "candidate" });

  const { data: users = [], isLoading } = useQuery({
    queryKey: ["admin-users", search, roleFilter],
    queryFn: () => adminApi.getUsers({ search, role: roleFilter || undefined }).then(r => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: UserForm) => adminApi.createUser(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("User created");
      setEditUser(null);
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Failed to create user"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<UserForm> }) => adminApi.updateUser(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("User updated");
      setEditUser(null);
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Failed to update user"),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      adminApi.updateUser(id, { is_active }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["admin-users"] }); toast.success("Updated"); },
  });

  const openAdd = () => {
    setForm({ full_name: "", email: "", password: "", role: "candidate" });
    setEditUser({});
  };

  const openEdit = (user: any) => {
    setForm({ full_name: user.full_name, email: user.email, password: "", role: user.role });
    setEditUser(user);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editUser?.id) {
      const payload: any = { full_name: form.full_name, email: form.email, role: form.role };
      if (form.password) payload.password = form.password;
      updateMutation.mutate({ id: editUser.id, data: payload });
    } else {
      if (!form.password) { toast.error("Password is required"); return; }
      createMutation.mutate(form);
    }
  };

  const roleBadge = (role: string) => {
    const map: Record<string, string> = { admin: "badge-red", recruiter: "badge-purple", candidate: "badge-blue" };
    return <span className={map[role] || "badge-slate"}>{role}</span>;
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">User Management</h1>
          <p className="text-slate-500 mt-1">{users.length} users total</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={openAdd}>
          <Plus className="w-4 h-4" /> Add User
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4 flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input value={search} onChange={e => setSearch(e.target.value)} className="input pl-9" placeholder="Search by name or email..." />
        </div>
        <select value={roleFilter} onChange={e => setRoleFilter(e.target.value)} className="input w-40">
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="recruiter">Recruiter</option>
          <option value="candidate">Candidate</option>
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              {["Name", "Email", "Role", "Status", "Joined", "Actions"].map(h => (
                <th key={h} className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-6 py-3">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading ? (
              <tr><td colSpan={6} className="text-center py-8 text-slate-400">Loading...</td></tr>
            ) : users.map((user: any) => (
              <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-sm font-bold">
                      {user.full_name?.charAt(0)}
                    </div>
                    <span className="text-sm font-medium text-slate-900">{user.full_name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-slate-600">{user.email}</td>
                <td className="px-6 py-4">{roleBadge(user.role)}</td>
                <td className="px-6 py-4">
                  <span className={`badge ${user.is_active ? "badge-green" : "badge-red"}`}>
                    {user.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-slate-500">
                  {new Date(user.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <button onClick={() => openEdit(user)} className="p-1.5 text-slate-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors">
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button onClick={() => toggleMutation.mutate({ id: user.id, is_active: !user.is_active })} className={`p-1.5 rounded-lg transition-colors ${user.is_active ? "text-slate-400 hover:text-red-600 hover:bg-red-50" : "text-slate-400 hover:text-green-600 hover:bg-green-50"}`}>
                      <Power className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add / Edit Modal */}
      {editUser !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4">
            <div className="flex items-center justify-between p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900">
                {editUser?.id ? "Edit User" : "Add New User"}
              </h2>
              <button onClick={() => setEditUser(null)} className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="label">Full Name</label>
                <input
                  className="input"
                  placeholder="John Doe"
                  value={form.full_name}
                  onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label className="label">Email</label>
                <input
                  type="email"
                  className="input"
                  placeholder="john@example.com"
                  value={form.email}
                  onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label className="label">
                  Password {editUser?.id && <span className="text-slate-400 font-normal">(leave blank to keep current)</span>}
                </label>
                <input
                  type="password"
                  className="input"
                  placeholder={editUser?.id ? "••••••••" : "Min 8 characters"}
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  required={!editUser?.id}
                />
              </div>
              <div>
                <label className="label">Role</label>
                <select
                  className="input"
                  value={form.role}
                  onChange={e => setForm(f => ({ ...f, role: e.target.value }))}
                >
                  <option value="candidate">Candidate</option>
                  <option value="recruiter">Recruiter</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setEditUser(null)} className="btn-secondary flex-1">
                  Cancel
                </button>
                <button type="submit" className="btn-primary flex-1" disabled={isSubmitting}>
                  {isSubmitting ? "Saving..." : editUser?.id ? "Save Changes" : "Create User"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
