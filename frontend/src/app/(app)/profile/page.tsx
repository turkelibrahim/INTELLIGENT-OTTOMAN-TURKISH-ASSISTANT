"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { authApi, type UserResponse } from "@/lib/api";
import { AlertTriangle, CheckCircle, BarChart, User, Lock, Monitor } from 'lucide-react';


interface UserStats {
  total_documents: number;
  favorite_documents: number;
  archived_documents: number;
  member_since: string | null;
  last_login: string | null;
}


export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
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
      case "admin": return { label: "Yönetici", color: "bg-[var(--ota-ruby)]/20 text-[var(--ota-ruby)] border-[var(--ota-ruby)]/30" };
      case "expert": return { label: "Uzman", color: "bg-[var(--ota-gold-dim)] text-[var(--ota-gold)] border-[var(--ota-gold)]/30" };
      default: return { label: "Kullanıcı", color: "bg-[var(--ota-iznik-turquoise)]/20 text-[var(--ota-iznik-turquoise)] border-[var(--ota-iznik-turquoise)]/30" };
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
      <div className="max-w-6xl mx-auto py-8 px-4 w-full animate-in fade-in duration-500">
        <div className="glass-panel border border-[var(--ota-border)] rounded-3xl p-8 mb-8 flex gap-8">
          <div className="w-28 h-28 rounded-2xl bg-[var(--ota-bg-2)] animate-pulse"></div>
          <div className="flex-1 flex flex-col justify-center gap-3">
            <div className="w-48 h-8 bg-[var(--ota-bg-2)] rounded animate-pulse"></div>
            <div className="w-32 h-4 bg-[var(--ota-bg-2)] rounded animate-pulse"></div>
            <div className="w-64 h-8 bg-[var(--ota-bg-2)] rounded mt-2 animate-pulse"></div>
          </div>
        </div>
        <div className="flex gap-8">
          <div className="w-64 h-64 glass-panel border border-[var(--ota-border)] rounded-2xl bg-[var(--ota-bg-2)] animate-pulse hidden lg:block"></div>
          <div className="flex-1 h-96 glass-panel border border-[var(--ota-border)] rounded-2xl bg-[var(--ota-bg-2)] animate-pulse"></div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] p-4">
        <div className="glass-panel border border-[var(--ota-border)] shadow-[var(--glass-shadow)] rounded-2xl p-8 max-w-md w-full text-center bg-[var(--ota-surface)] flex flex-col items-center">
          <div className="w-16 h-16 bg-[var(--ota-ruby)]/10 text-[var(--ota-ruby)] rounded-full flex items-center justify-center text-2xl mb-4 border border-[var(--ota-ruby)]/20">
            <AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" />
          </div>
          <h2 className="text-xl font-bold text-[var(--ota-text)] mb-2">Profil Bilgileri Yüklenemedi</h2>
          <p className="text-[var(--ota-text-muted)] mb-6 text-sm leading-relaxed">
            Sunucuyla iletişim kurulurken bir sorun oluştu veya oturumunuz sonlanmış olabilir.
          </p>
          <div className="flex items-center gap-3 w-full">
            <button onClick={loadData} className="flex-1 py-3 bg-[var(--ota-bg-2)] border border-[var(--ota-border)] hover:border-[var(--ota-gold)]/50 hover:text-[var(--ota-gold)] text-[var(--ota-text)] rounded-xl font-medium transition-colors text-sm">
              Yeniden Dene
            </button>
            <button onClick={() => router.push("/dashboard")} className="flex-1 py-3 bg-[var(--ota-gold)] border border-[var(--ota-gold)] hover:bg-[var(--ota-gold)]/90 text-[#0A202A] rounded-xl font-bold transition-colors text-sm shadow-sm">
              Ana Sayfaya Dön
            </button>
          </div>
        </div>
      </div>
    );
  }

  const roleBadge = getRoleBadge(user.role);
  const initials = getInitials(user.full_name, user.username);

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 w-full animate-in slide-in-from-bottom-4 fade-in duration-700 space-y-8">
      {/* ── Profil Başlığı ── */}
      <div className="relative glass-panel border border-[var(--ota-border)] rounded-3xl overflow-hidden bg-[var(--ota-surface-dark)]/80 shadow-[var(--glass-shadow)]">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-[var(--ota-gold)]/5 via-transparent to-[var(--ota-gold)]/10 pointer-events-none" />
        <div className="absolute inset-0 opacity-[0.03] bg-[url('/auth/floral-pattern.png')] bg-repeat-x bg-[length:120px] pointer-events-none" />

        <div className="relative flex flex-col sm:flex-row items-center gap-8 p-8 lg:p-10">
          {/* Avatar */}
          <div className="relative group flex-shrink-0">
            <div className="w-28 h-28 rounded-2xl bg-gradient-to-br from-[var(--ota-gold)] to-[#8A6F33] flex items-center justify-center text-[#0A202A] text-4xl font-serif font-bold shadow-lg border border-[var(--ota-gold)]/30 transition-transform group-hover:scale-105">
              {initials}
            </div>
            <div className="absolute -bottom-2 -right-2 w-7 h-7 bg-[var(--ota-success)] rounded-full border-[3px] border-[var(--ota-bg)] shadow-md" title="Aktif" />
          </div>

          {/* User Info */}
          <div className="flex-1 text-center sm:text-left">
            <h1 className="text-3xl font-serif font-bold text-[var(--ota-text)] mb-2 drop-shadow-sm">
              {user.full_name || user.username}
            </h1>
            <p className="text-sm text-[var(--ota-text-muted)] mb-4 font-mono opacity-80">{user.email}</p>
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-3">
              <span className={`px-3 py-1 rounded text-xs font-bold uppercase tracking-wider border ${roleBadge.color}`}>
                {roleBadge.label}
              </span>
              <span className="px-3 py-1 rounded text-xs font-bold uppercase tracking-wider bg-[var(--ota-success)]/10 text-[var(--ota-success)] border border-[var(--ota-success)]/20 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--ota-success)]"></span> Aktif
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-3 w-full sm:w-auto">
            <button
              onClick={() => {
                const el = document.getElementById("hesap-bilgileri");
                if (el) el.scrollIntoView({ behavior: "smooth" });
              }}
              className="px-6 py-3 bg-[var(--ota-bg-2)] border border-[var(--ota-gold)]/50 hover:bg-[var(--ota-gold)]/10 text-[var(--ota-gold)] rounded-xl font-bold transition-all shadow-sm text-sm"
            >
              Profili Düzenle
            </button>
          </div>
        </div>
      </div>

      {/* ── Hesap Özeti ── */}
      {stats && (
        <div className="glass-panel border border-[var(--ota-border)] rounded-2xl p-8 bg-[var(--ota-surface)] shadow-[var(--glass-shadow)]">
          <h2 className="text-xl font-serif font-bold text-[var(--ota-text)] mb-6 flex items-center gap-3 pb-4 border-b border-[var(--ota-border)]">
            <span className="text-[var(--ota-gold)]"><BarChart className="w-6 h-6" /></span> Hesap Özeti
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[var(--ota-bg-2)]/50 border border-[var(--ota-border)] rounded-xl p-5 text-center group hover:border-[var(--ota-gold)]/30 transition-colors">
              <div className="text-3xl font-serif font-bold text-[var(--ota-text)] mb-2 group-hover:scale-110 transition-transform">{stats.total_documents}</div>
              <div className="text-[10px] text-[var(--ota-text-muted)] font-bold uppercase tracking-wider">Toplam Belge</div>
            </div>
            <div className="bg-[var(--ota-gold-dim)] border border-[var(--ota-gold)]/30 rounded-xl p-5 text-center group transition-colors">
              <div className="text-3xl font-serif font-bold text-[var(--ota-gold)] mb-2 group-hover:scale-110 transition-transform">{stats.total_documents}</div>
              <div className="text-[10px] text-[var(--ota-text-muted)] font-bold uppercase tracking-wider text-[var(--ota-gold)]">Toplam Analiz</div>
            </div>
            <div className="bg-[var(--ota-bg-2)]/50 border border-[var(--ota-border)] rounded-xl p-5 text-center group hover:border-[var(--ota-gold)]/30 transition-colors flex flex-col justify-center">
              <div className="text-sm font-bold text-[var(--ota-text)] mb-1">{formatDate(stats.last_login)}</div>
              <div className="text-[10px] text-[var(--ota-text-muted)] font-bold uppercase tracking-wider">Son Aktivite</div>
            </div>
            <div className="bg-[var(--ota-bg-2)]/50 border border-[var(--ota-border)] rounded-xl p-5 text-center group hover:border-[var(--ota-gold)]/30 transition-colors flex flex-col justify-center">
              <div className="text-sm font-bold text-[var(--ota-text)] mb-1">{formatDate(stats.member_since)}</div>
              <div className="text-[10px] text-[var(--ota-text-muted)] font-bold uppercase tracking-wider">Hesap Tarihi</div>
            </div>
          </div>
        </div>
      )}

      {/* ── Hesap Bilgileri ── */}
      <div id="hesap-bilgileri" className="glass-panel border border-[var(--ota-border)] rounded-2xl p-8 bg-[var(--ota-surface)] shadow-[var(--glass-shadow)] scroll-mt-24">
        <h2 className="text-xl font-serif font-bold text-[var(--ota-text)] mb-6 flex items-center gap-3 pb-4 border-b border-[var(--ota-border)]">
          <span className="text-[var(--ota-gold)]"><User className="w-6 h-6" /></span> Hesap Bilgileri
        </h2>

        <div className="flex flex-col gap-6 max-w-lg">
          <div>
            <label className="block text-[10px] text-[var(--ota-text-muted)] uppercase tracking-wider font-bold mb-2">Ad Soyad</label>
            <input
              type="text"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              className="w-full bg-[var(--ota-bg-2)] border border-[var(--ota-border)] rounded-xl px-4 py-3 text-sm text-[var(--ota-text)] focus:outline-none focus:border-[var(--ota-gold)] focus:ring-1 focus:ring-[var(--ota-gold)] transition-all placeholder-[var(--ota-text-muted)] shadow-inner"
              placeholder="Adınız ve Soyadınız"
            />
          </div>

          <div>
            <label className="block text-[10px] text-[var(--ota-text-muted)] uppercase tracking-wider font-bold mb-2">E-Posta</label>
            <input
              type="email"
              value={user.email}
              disabled
              className="w-full bg-[var(--ota-bg-2)]/50 border border-[var(--ota-border)] rounded-xl px-4 py-3 text-sm text-[var(--ota-text-muted)] cursor-not-allowed opacity-70"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] text-[var(--ota-text-muted)] uppercase tracking-wider font-bold mb-2">Rol</label>
              <div className="w-full bg-[var(--ota-bg-2)]/50 border border-[var(--ota-border)] rounded-xl px-4 py-3 text-sm text-[var(--ota-text-muted)] opacity-70 flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${user.role === 'admin' ? 'bg-[var(--ota-ruby)]' : 'bg-[var(--ota-gold)]'}`}></span>
                {roleBadge.label}
              </div>
            </div>
            <div>
              <label className="block text-[10px] text-[var(--ota-text-muted)] uppercase tracking-wider font-bold mb-2">Kayıt Tarihi</label>
              <div className="w-full bg-[var(--ota-bg-2)]/50 border border-[var(--ota-border)] rounded-xl px-4 py-3 text-sm text-[var(--ota-text-muted)] opacity-70">
                {formatDate(user.created_at)}
              </div>
            </div>
          </div>

          {saveMsg && (
            <div className={`p-4 rounded-xl text-sm font-medium border ${
              saveMsg.type === "success"
                ? "bg-[var(--ota-success)]/10 text-[var(--ota-success)] border-[var(--ota-success)]/20"
                : "bg-[var(--ota-ruby)]/10 text-[var(--ota-ruby)] border-[var(--ota-ruby)]/20"
            }`}>
              {saveMsg.type === "success" ? <CheckCircle className="w-5 h-5 inline-block mr-1 align-text-bottom" /> : <AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" />} {saveMsg.text}
            </div>
          )}

          <button
            onClick={handleSaveProfile}
            disabled={saving}
            className="w-full sm:w-auto mt-2 px-6 py-3 bg-[var(--ota-gold)] text-[#0A202A] font-bold rounded-xl hover:bg-[var(--ota-gold)]/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg text-sm"
          >
            {saving ? "Kaydediliyor..." : "Değişiklikleri Kaydet"}
          </button>
        </div>
      </div>

      {/* ── Güvenlik ── */}
      <div className="glass-panel border border-[var(--ota-border)] rounded-2xl p-8 bg-[var(--ota-surface)] shadow-[var(--glass-shadow)]">
        <h2 className="text-xl font-serif font-bold text-[var(--ota-text)] mb-6 flex items-center gap-3 pb-4 border-b border-[var(--ota-border)]">
          <span className="text-[var(--ota-gold)]"><Lock className="w-6 h-6" /></span> Güvenlik
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Şifre */}
          <div className="flex flex-col gap-6">
            <h3 className="text-sm font-bold text-[var(--ota-text)] mb-2">Şifre Değiştir</h3>
            <div>
              <label className="block text-[10px] text-[var(--ota-text-muted)] uppercase tracking-wider font-bold mb-2">Mevcut Şifre</label>
              <input
                type="password"
                value={currentPassword}
                onChange={e => setCurrentPassword(e.target.value)}
                className="w-full bg-[var(--ota-bg-2)] border border-[var(--ota-border)] rounded-xl px-4 py-3 text-sm text-[var(--ota-text)] focus:outline-none focus:border-[var(--ota-gold)] focus:ring-1 focus:ring-[var(--ota-gold)] transition-all placeholder-[var(--ota-text-muted)] shadow-inner"
                placeholder="••••••••"
              />
            </div>

            <div>
              <label className="block text-[10px] text-[var(--ota-text-muted)] uppercase tracking-wider font-bold mb-2">Yeni Şifre</label>
              <input
                type="password"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                className="w-full bg-[var(--ota-bg-2)] border border-[var(--ota-border)] rounded-xl px-4 py-3 text-sm text-[var(--ota-text)] focus:outline-none focus:border-[var(--ota-gold)] focus:ring-1 focus:ring-[var(--ota-gold)] transition-all placeholder-[var(--ota-text-muted)] shadow-inner"
                placeholder="En az 6 karakter"
              />
            </div>

            <div>
              <label className="block text-[10px] text-[var(--ota-text-muted)] uppercase tracking-wider font-bold mb-2">Yeni Şifre (Tekrar)</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                className="w-full bg-[var(--ota-bg-2)] border border-[var(--ota-border)] rounded-xl px-4 py-3 text-sm text-[var(--ota-text)] focus:outline-none focus:border-[var(--ota-gold)] focus:ring-1 focus:ring-[var(--ota-gold)] transition-all placeholder-[var(--ota-text-muted)] shadow-inner"
                placeholder="••••••••"
              />
            </div>

            {pwMsg && (
              <div className={`p-4 rounded-xl text-sm font-medium border ${
                pwMsg.type === "success"
                  ? "bg-[var(--ota-success)]/10 text-[var(--ota-success)] border-[var(--ota-success)]/20"
                  : "bg-[var(--ota-ruby)]/10 text-[var(--ota-ruby)] border-[var(--ota-ruby)]/20"
              }`}>
                {pwMsg.type === "success" ? <CheckCircle className="w-5 h-5 inline-block mr-1 align-text-bottom" /> : <AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" />} {pwMsg.text}
              </div>
            )}

            <button
              onClick={handleChangePassword}
              disabled={pwSaving || !currentPassword || !newPassword || !confirmPassword}
              className="w-full sm:w-auto px-6 py-3 bg-[var(--ota-bg-2)] border border-[var(--ota-border)] hover:border-[var(--ota-gold)] hover:text-[var(--ota-gold)] text-[var(--ota-text)] font-bold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm text-sm"
            >
              {pwSaving ? "Değiştiriliyor..." : "Şifreyi Güncelle"}
            </button>
          </div>
          
          {/* Oturumlar & API */}
          <div className="flex flex-col gap-8">
            <div>
              <h3 className="text-sm font-bold text-[var(--ota-text)] mb-4">Oturumlar</h3>
              <div className="bg-[var(--ota-bg-2)]/50 rounded-xl p-5 border border-[var(--ota-border)]">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="text-[var(--ota-gold)]"><Monitor className="w-6 h-6" /></div>
                    <div>
                      <div className="text-sm font-bold text-[var(--ota-text)]">Mevcut Cihaz (Bu Tarayıcı)</div>
                      <div className="text-xs text-[var(--ota-text-muted)] mt-1">Son Aktivite: Şimdi</div>
                    </div>
                  </div>
                  <span className="px-2 py-1 bg-[var(--ota-success)]/10 text-[var(--ota-success)] border border-[var(--ota-success)]/20 text-[10px] font-bold uppercase rounded">Aktif</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-bold text-[var(--ota-text)] mb-4">API Erişimi</h3>
              <div className="bg-[var(--ota-bg-2)]/50 rounded-xl p-5 border border-[var(--ota-border)]">
                <div className="flex items-center justify-between mb-4 pb-4 border-b border-[var(--ota-border)]">
                  <div className="flex flex-col gap-1">
                    <span className="text-sm font-bold text-[var(--ota-text)]">Gelişmiş AI Analizi</span>
                    <span className="text-xs text-[var(--ota-text-muted)]">NVIDIA NIM, GPT-4o-mini entegrasyonu</span>
                  </div>
                  {user.role === "admin" || user.role === "expert" ? (
                    <span className="px-2 py-1 bg-[var(--ota-gold-dim)] text-[var(--ota-gold)] border border-[var(--ota-gold)]/30 text-[10px] font-bold uppercase rounded">Yetkili</span>
                  ) : (
                    <span className="px-2 py-1 bg-[var(--ota-bg)] text-[var(--ota-text-muted)] border border-[var(--ota-border)] text-[10px] font-bold uppercase rounded">Yetkisiz</span>
                  )}
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex flex-col gap-1">
                    <span className="text-sm font-bold text-[var(--ota-text)]">Toplu OCR & RAG</span>
                    <span className="text-xs text-[var(--ota-text-muted)]">Limitsiz belge tarama</span>
                  </div>
                  <span className="px-2 py-1 bg-[var(--ota-success)]/10 text-[var(--ota-success)] border border-[var(--ota-success)]/20 text-[10px] font-bold uppercase rounded">Yetkili</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
