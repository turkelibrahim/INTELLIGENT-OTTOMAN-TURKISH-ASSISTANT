"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { authApi, type UserResponse } from "@/lib/api";

interface UserStats {
  total_documents: number;
  favorite_documents: number;
  archived_documents: number;
  member_since: string | null;
  last_login: string | null;
}

type ActiveSection = "overview" | "edit" | "password" | "activity";

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [activeSection, setActiveSection] = useState<ActiveSection>("overview");
  const [loading, setLoading] = useState(true);

  // Edit state
  const [fullName, setFullName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Password change state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pwMsg, setPwMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [pwSaving, setPwSaving] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [userData, statsData] = await Promise.all([
        authApi.getMe(),
        authApi.getMyStats(),
      ]);
      setUser(userData);
      setStats(statsData);
      setFullName(userData.full_name || "");
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadData();
  }, [loadData]);

  const handleSaveProfile = async () => {
    setSaving(true);
    setSaveMsg(null);
    try {
      const updated = await authApi.updateProfile({ full_name: fullName.trim() || undefined });
      setUser(updated);
      setSaveMsg({ type: "success", text: "Profiliniz başarıyla güncellendi." });
    } catch (err: unknown) {
      setSaveMsg({ type: "error", text: (err as { detail?: string })?.detail || "Güncelleme başarısız oldu." });
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    setPwMsg(null);
    if (newPassword !== confirmPassword) {
      setPwMsg({ type: "error", text: "Yeni parolalar eşleşmiyor." });
      return;
    }
    if (newPassword.length < 6) {
      setPwMsg({ type: "error", text: "Parola en az 6 karakter olmalıdır." });
      return;
    }
    setPwSaving(true);
    try {
      await authApi.updateProfile({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPwMsg({ type: "success", text: "Parolanız başarıyla değiştirildi." });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: unknown) {
      setPwMsg({ type: "error", text: (err as { detail?: string })?.detail || "Parola değiştirme başarısız." });
    } finally {
      setPwSaving(false);
    }
  };

  const getRoleBadge = (role: string) => {
    switch (role) {
      case "admin": return { label: "Yönetici", color: "bg-red-500/20 text-red-400 border-red-500/30" };
      case "expert": return { label: "Uzman", color: "bg-purple-500/20 text-purple-400 border-purple-500/30" };
      default: return { label: "Kullanıcı", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" };
    }
  };

  const getInitials = (name?: string | null, username?: string) => {
    if (name) return name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);
    if (username) return username.slice(0, 2).toUpperCase();
    return "KU";
  };

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleDateString("tr-TR", {
      day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit"
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-amber-500/30 border-t-amber-500 rounded-full animate-spin"></div>
          <p className="text-sm text-slate-400">Profil yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <p className="text-slate-400 mb-4">Profil bilgileri alınamadı.</p>
          <button onClick={() => router.push("/dashboard")} className="px-4 py-2 bg-amber-500 text-slate-900 rounded-lg font-medium">
            Ana Sayfaya Dön
          </button>
        </div>
      </div>
    );
  }

  const roleBadge = getRoleBadge(user.role);
  const initials = getInitials(user.full_name, user.username);

  const sections: { key: ActiveSection; label: string; icon: string }[] = [
    { key: "overview", label: "Genel Bakış", icon: "👤" },
    { key: "edit", label: "Profili Düzenle", icon: "✏️" },
    { key: "password", label: "Parola Değiştir", icon: "🔒" },
    { key: "activity", label: "Hesap Bilgileri", icon: "📊" },
  ];

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      {/* ── Hero Banner ── */}
      <div className="relative glass-panel border border-amber-500/10 rounded-3xl overflow-hidden mb-8">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-amber-900/30 via-slate-900/50 to-amber-800/20 pointer-events-none" />
        <div className="absolute inset-0 opacity-10 bg-[url('/auth/floral-pattern.png')] bg-repeat-x bg-[length:120px] pointer-events-none" />

        <div className="relative flex flex-col sm:flex-row items-center gap-6 p-8">
          {/* Avatar */}
          <div className="relative group">
            <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center text-white text-3xl font-bold shadow-2xl shadow-amber-500/30 border-2 border-amber-400/30 transition-transform group-hover:scale-105">
              {initials}
            </div>
            <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full border-2 border-slate-900 shadow-lg" title="Aktif" />
          </div>

          {/* User Info */}
          <div className="flex-1 text-center sm:text-left">
            <h1 className="text-2xl font-bold text-slate-100 mb-1">
              {user.full_name || user.username}
            </h1>
            <p className="text-sm text-slate-400 mb-3">@{user.username} · {user.email}</p>
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
              <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${roleBadge.color}`}>
                {roleBadge.label}
              </span>
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                ● Aktif
              </span>
            </div>
          </div>

          {/* Quick Stats */}
          {stats && (
            <div className="flex gap-6 sm:gap-8">
              <div className="text-center">
                <div className="text-2xl font-bold text-amber-500">{stats.total_documents}</div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider mt-1">Belge</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-amber-500">{stats.favorite_documents}</div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider mt-1">Favori</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-amber-500">{stats.archived_documents}</div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider mt-1">Arşiv</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Content Grid ── */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left Nav */}
        <nav className="lg:w-64 flex-shrink-0">
          <div className="glass-panel border border-amber-500/10 rounded-2xl p-3 flex flex-row lg:flex-col gap-2 overflow-x-auto">
            {sections.map(s => (
              <button
                key={s.key}
                onClick={() => setActiveSection(s.key)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all whitespace-nowrap ${
                  activeSection === s.key
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-[0_0_12px_rgba(245,158,11,0.08)]"
                    : "text-slate-300 hover:bg-white/5 hover:text-white border border-transparent"
                }`}
              >
                <span>{s.icon}</span>
                <span>{s.label}</span>
              </button>
            ))}
          </div>
        </nav>

        {/* Right Content */}
        <div className="flex-1 min-w-0">
          {/* ── Overview ── */}
          {activeSection === "overview" && (
            <div className="glass-panel border border-amber-500/10 rounded-2xl p-8">
              <h2 className="text-lg font-bold text-slate-100 mb-6 flex items-center gap-2">
                <span className="text-amber-500">👤</span> Profil Bilgileri
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {[
                  { label: "Tam Ad", value: user.full_name || "Belirtilmemiş", icon: "🏷️" },
                  { label: "Kullanıcı Adı", value: `@${user.username}`, icon: "👤" },
                  { label: "E-Posta", value: user.email, icon: "📧" },
                  { label: "Rol", value: roleBadge.label, icon: "🛡️" },
                  { label: "Hesap Durumu", value: user.status === "active" ? "Aktif" : user.status, icon: "✅" },
                  { label: "Kayıt Tarihi", value: formatDate(user.created_at), icon: "📅" },
                  { label: "Son Giriş", value: formatDate(user.last_login_at), icon: "🕐" },
                ].map(item => (
                  <div key={item.label} className="bg-slate-900/50 rounded-xl p-4 border border-slate-800 hover:border-amber-500/20 transition-colors">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm">{item.icon}</span>
                      <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">{item.label}</span>
                    </div>
                    <p className="text-sm text-slate-200 font-medium">{item.value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Edit Profile ── */}
          {activeSection === "edit" && (
            <div className="glass-panel border border-amber-500/10 rounded-2xl p-8">
              <h2 className="text-lg font-bold text-slate-100 mb-6 flex items-center gap-2">
                <span className="text-amber-500">✏️</span> Profili Düzenle
              </h2>

              <div className="flex flex-col gap-6 max-w-md">
                <div>
                  <label className="block text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">Tam Adınız</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={e => setFullName(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-all placeholder-slate-500"
                    placeholder="Adınız ve Soyadınız"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">E-Posta</label>
                  <input
                    type="email"
                    value={user.email}
                    disabled
                    className="w-full bg-slate-900/50 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-500 cursor-not-allowed"
                  />
                  <p className="text-[10px] text-slate-500 mt-1">E-posta adresi değiştirilemez.</p>
                </div>

                <div>
                  <label className="block text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">Kullanıcı Adı</label>
                  <input
                    type="text"
                    value={user.username}
                    disabled
                    className="w-full bg-slate-900/50 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-500 cursor-not-allowed"
                  />
                  <p className="text-[10px] text-slate-500 mt-1">Kullanıcı adı değiştirilemez.</p>
                </div>

                {saveMsg && (
                  <div className={`p-3 rounded-xl text-sm font-medium border ${
                    saveMsg.type === "success"
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : "bg-red-500/10 text-red-400 border-red-500/20"
                  }`}>
                    {saveMsg.type === "success" ? "✅" : "⚠️"} {saveMsg.text}
                  </div>
                )}

                <button
                  onClick={handleSaveProfile}
                  disabled={saving}
                  className="w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-amber-500 to-amber-600 text-slate-900 font-bold rounded-xl hover:shadow-lg hover:shadow-amber-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? "Kaydediliyor..." : "Değişiklikleri Kaydet"}
                </button>
              </div>
            </div>
          )}

          {/* ── Password ── */}
          {activeSection === "password" && (
            <div className="glass-panel border border-amber-500/10 rounded-2xl p-8">
              <h2 className="text-lg font-bold text-slate-100 mb-6 flex items-center gap-2">
                <span className="text-amber-500">🔒</span> Parola Değiştir
              </h2>

              <div className="flex flex-col gap-6 max-w-md">
                <div>
                  <label className="block text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">Mevcut Parola</label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={e => setCurrentPassword(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-all placeholder-slate-500"
                    placeholder="••••••••"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">Yeni Parola</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-all placeholder-slate-500"
                    placeholder="En az 6 karakter"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">Yeni Parola (Tekrar)</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-all placeholder-slate-500"
                    placeholder="••••••••"
                  />
                </div>

                {pwMsg && (
                  <div className={`p-3 rounded-xl text-sm font-medium border ${
                    pwMsg.type === "success"
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : "bg-red-500/10 text-red-400 border-red-500/20"
                  }`}>
                    {pwMsg.type === "success" ? "✅" : "⚠️"} {pwMsg.text}
                  </div>
                )}

                <button
                  onClick={handleChangePassword}
                  disabled={pwSaving || !currentPassword || !newPassword || !confirmPassword}
                  className="w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-amber-500 to-amber-600 text-slate-900 font-bold rounded-xl hover:shadow-lg hover:shadow-amber-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {pwSaving ? "Değiştiriliyor..." : "Parolayı Değiştir"}
                </button>
              </div>
            </div>
          )}

          {/* ── Activity / Account Info ── */}
          {activeSection === "activity" && stats && (
            <div className="flex flex-col gap-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[
                  { label: "Toplam Belge", value: stats.total_documents, icon: "📄", color: "from-amber-500/20 to-amber-600/10 border-amber-500/20" },
                  { label: "Favori Belgeler", value: stats.favorite_documents, icon: "⭐", color: "from-yellow-500/20 to-yellow-600/10 border-yellow-500/20" },
                  { label: "Arşivlenen", value: stats.archived_documents, icon: "📦", color: "from-blue-500/20 to-blue-600/10 border-blue-500/20" },
                ].map(card => (
                  <div key={card.label} className={`glass-panel bg-gradient-to-br ${card.color} border rounded-2xl p-6 text-center`}>
                    <span className="text-3xl mb-3 block">{card.icon}</span>
                    <div className="text-3xl font-bold text-slate-100 mb-1">{card.value}</div>
                    <div className="text-xs text-slate-400 uppercase tracking-wider">{card.label}</div>
                  </div>
                ))}
              </div>

              {/* Timeline */}
              <div className="glass-panel border border-amber-500/10 rounded-2xl p-8">
                <h2 className="text-lg font-bold text-slate-100 mb-6 flex items-center gap-2">
                  <span className="text-amber-500">📊</span> Hesap Zaman Çizelgesi
                </h2>

                <div className="flex flex-col gap-6 relative">
                  <div className="absolute left-4 top-0 bottom-0 w-px bg-amber-500/20" />
                  
                  {[
                    { label: "Hesap Oluşturuldu", date: stats.member_since, icon: "🎉" },
                    { label: "Son Giriş", date: stats.last_login, icon: "🔑" },
                  ].map((event, i) => (
                    <div key={i} className="flex items-start gap-4 relative pl-4">
                      <div className="w-8 h-8 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-sm z-10 -ml-4">
                        {event.icon}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-200">{event.label}</p>
                        <p className="text-xs text-slate-400 mt-0.5">{formatDate(event.date)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
