"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Icons } from "@/components/Icons";
import type { UserResponse } from "@/lib/api";
import { Settings, Star, User, LogOut } from 'lucide-react';


/** Yaklaşık Hicri tarih hesaplama (civil approximation) */
function toHijri(date: Date): { year: number; month: string; day: number } {
  const HIJRI_MONTHS = [
    "Muharrem", "Safer", "Rebiülevvel", "Rebiülahir",
    "Cemaziyelevvel", "Cemaziyelahir", "Recep", "Şaban",
    "Ramazan", "Şevval", "Zilkade", "Zilhicce",
  ];
  const jd = Math.floor((date.getTime() / 86400000) + 2440587.5);
  const l = jd - 1948440 + 10632;
  const n = Math.floor((l - 1) / 10631);
  const ll = l - 10631 * n + 354;
  const j = Math.floor((10985 - ll) / 5316) * Math.floor((50 * ll) / 17719) +
            Math.floor(ll / 5670) * Math.floor((43 * ll) / 15238);
  const lll = ll - Math.floor((30 - j) / 15) * Math.floor((17719 * j) / 50) -
              Math.floor(j / 16) * Math.floor((15238 * j) / 43) + 29;
  const month = Math.floor((24 * lll) / 709);
  const day = lll - Math.floor((709 * month) / 24);
  const year = 30 * n + j - 30;
  return { year, month: HIJRI_MONTHS[month - 1] ?? "", day };
}

export default function Header({
  user,
  onLogout,
  onMenuToggle,
}: {
  user: UserResponse | null;
  onLogout: () => void;
  onMenuToggle?: () => void;
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [now, setNow] = useState<Date>(() => new Date());
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowProfileMenu(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
  };

  const miladi = now.toLocaleDateString("tr-TR", {
    day: "numeric", month: "long", year: "numeric",
  });

  const hicri = toHijri(now);
  const hicriStr = `${hicri.day} ${hicri.month} ${hicri.year} H.`;

  const getInitials = () => {
    if (user?.full_name) return user.full_name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);
    if (user?.username) return user.username.slice(0, 2).toUpperCase();
    return "KU";
  };

  return (
    <header className="ota-header" role="banner">
      <div className="ota-header-pattern" aria-hidden="true" />

      {/* Left — Title */}
      <div className="ota-header-left">
        {onMenuToggle && (
          <button 
            className="lg:hidden ota-icon-btn mr-2 flex-shrink-0" 
            onClick={onMenuToggle}
            aria-label="Menüyü aç/kapat"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
          </button>
        )}
        <div>
          <h1 className="ota-header-title hidden sm:block">Yapay Zekâ Destekli Osmanlıca Belge Asistanı</h1>
          <h1 className="ota-header-title sm:hidden">Belge Asistanı</h1>
          {user && (
            <p className="ota-header-subtitle">
              {user.full_name || user.username}
            </p>
          )}
        </div>
      </div>

      {/* Center — Search */}
      <div className="ota-header-center hidden md:block relative z-10">
        <form className="ota-search-form group" onSubmit={handleSearch} role="search">
          <span className="ota-search-icon group-focus-within:text-[var(--ota-gold)] transition-colors duration-200" aria-hidden="true">
            {Icons.search}
          </span>
          <input
            id="global-search"
            type="search"
            className="ota-search-input"
            placeholder="Belge, içerik veya anahtar kelime ara..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Belge arama"
            autoComplete="off"
          />
        </form>
      </div>

      {/* Right — Date, Notifications, Profile */}
      <div className="ota-header-right relative z-10">
        {/* Date card */}
        <div className="hidden lg:flex ota-date-card" aria-label={`Tarihler: ${hicriStr}, ${miladi}`}>
          <span className="ota-date-icon" aria-hidden="true">{Icons.moon}</span>
          <div className="ota-date-info">
            <span className="ota-date-hijri">{hicriStr}</span>
            <span className="ota-date-miladi">{miladi}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="ota-header-actions">
          <button
            className="ota-icon-btn"
            aria-label="Bildirimler"
            type="button"
          >
            {Icons.bell}
            <span className="ota-notif-dot" aria-hidden="true" />
          </button>

          {/* Profile Dropdown */}
          <div className="relative" ref={menuRef}>
            <button
              className="flex items-center justify-center w-[36px] h-[36px] rounded-lg bg-gradient-to-br from-[var(--ota-imperial-gold)] to-[var(--ota-bronze)] text-[#0A0A0C] shadow-md hover:shadow-lg hover:shadow-[var(--ota-gold)]/20 transition-all border border-[var(--ota-gold)]/30 focus:outline-none focus:ring-2 focus:ring-[var(--ota-gold)]/50 text-xs font-bold ml-1"
              aria-label={`Kullanıcı menüsü: ${user?.full_name || user?.username || "Kullanıcı"}`}
              type="button"
              onClick={() => setShowProfileMenu(!showProfileMenu)}
            >
              {getInitials()}
            </button>

            {showProfileMenu && (
              <div className="absolute right-0 top-full mt-2 w-64 glass-panel rounded-xl shadow-2xl overflow-hidden animate-in slide-in-from-top-2 fade-in duration-200 z-50">
                {/* User info */}
                <div className="px-5 py-4 border-b border-[var(--ota-border)] bg-[var(--ota-bg-2)]/80">
                  <p className="text-sm font-semibold text-[var(--ota-text)] truncate">{user?.full_name || user?.username}</p>
                  <p className="text-xs text-[var(--ota-text-muted)] truncate">{user?.email}</p>
                </div>

                {/* Menu items */}
                <div className="py-2">
                  <Link
                    href="/profile"
                    onClick={() => setShowProfileMenu(false)}
                    className="flex items-center gap-3 px-5 py-2.5 text-sm text-[var(--ota-text-2)] hover:bg-[var(--ota-teal-active)] hover:text-[var(--ota-gold)] transition-colors"
                  >
                    <span><User className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> Profilim
                  </Link>
                  <Link
                    href="/settings"
                    onClick={() => setShowProfileMenu(false)}
                    className="flex items-center gap-3 px-5 py-2.5 text-sm text-[var(--ota-text-2)] hover:bg-[var(--ota-teal-active)] hover:text-[var(--ota-gold)] transition-colors"
                  >
                    <span><Settings className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> Ayarlar
                  </Link>
                  <Link
                    href="/favorites"
                    onClick={() => setShowProfileMenu(false)}
                    className="flex items-center gap-3 px-5 py-2.5 text-sm text-[var(--ota-text-2)] hover:bg-[var(--ota-teal-active)] hover:text-[var(--ota-gold)] transition-colors"
                  >
                    <span><Star className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> Favorilerim
                  </Link>
                </div>

                {/* Logout */}
                <div className="border-t border-[var(--ota-border)] py-2">
                  <button
                    onClick={() => { setShowProfileMenu(false); onLogout(); }}
                    className="flex items-center gap-3 px-5 py-2.5 text-sm text-[var(--ota-ruby)] hover:bg-[var(--ota-ruby)]/10 transition-colors w-full text-left"
                  >
                    <span><LogOut className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> Çıkış Yap
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
