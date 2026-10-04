"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Icons } from "@/components/Icons";
import type { UserResponse } from "@/lib/api";

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
}: {
  user: UserResponse | null;
  onLogout: () => void;
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
    <header className="sticky top-0 z-30 flex items-center justify-between h-[72px] px-6 glass-panel border-b border-amber-500/10 shadow-md" role="banner">
      <div className="absolute inset-0 opacity-5 pointer-events-none bg-[url('/auth/floral-pattern.png')] bg-repeat-x bg-[length:120px]" aria-hidden="true" />

      {/* Left — Title */}
      <div className="flex-1 min-w-0 pr-4">
        <h1 className="text-sm font-semibold tracking-wide text-slate-100 truncate md:text-base">
          Yapay Zekâ Destekli Osmanlıca Belge Asistanıı
        </h1>
        {user && (
          <p className="text-xs font-medium text-amber-500 truncate">
            {user.full_name || user.username}
          </p>
        )}
      </div>

      {/* Center — Search */}
      <div className="flex-1 max-w-md mx-4 hidden md:block relative z-10">
        <form className="relative group" onSubmit={handleSearch} role="search">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-amber-500 transition-colors duration-200" aria-hidden="true">
            {Icons.search}
          </span>
          <input
            id="global-search"
            type="search"
            className="w-full h-10 pl-10 pr-4 text-sm bg-slate-900/50 border border-slate-700 rounded-full text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500/50 transition-all shadow-[inset_0_2px_4px_rgba(0,0,0,0.2)]"
            placeholder="Belge, içerik veya anahtar kelime ara..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Belge arama"
            autoComplete="off"
          />
        </form>
      </div>

      {/* Right — Date, Notifications, Profile */}
      <div className="flex items-center gap-4 flex-shrink-0 z-10">
        {/* Date card */}
        <div className="hidden lg:flex items-center gap-3 px-4 py-2 bg-slate-900/40 border border-amber-500/10 rounded-xl shadow-[inset_0_1px_4px_rgba(255,255,255,0.02)]" aria-label={`Tarihler: ${hicriStr}, ${miladi}`}>
          <span className="text-amber-500" aria-hidden="true">{Icons.moon}</span>
          <div className="flex flex-col">
            <span className="text-xs font-semibold text-amber-400 whitespace-nowrap">{hicriStr}</span>
            <span className="text-[10px] text-slate-400 whitespace-nowrap">{miladi}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            className="relative flex items-center justify-center w-10 h-10 rounded-full bg-slate-800/50 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700/50 transition-all hover:shadow-[0_0_10px_rgba(255,255,255,0.1)] focus:outline-none focus:ring-2 focus:ring-amber-500/50"
            aria-label="Bildirimler"
            type="button"
          >
            {Icons.bell}
            <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-red-500 shadow-[0_0_4px_rgba(239,68,68,0.8)]" aria-hidden="true" />
          </button>

          {/* Profile Dropdown */}
          <div className="relative" ref={menuRef}>
            <button
              className="flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-amber-600 to-amber-800 text-white shadow-md hover:shadow-lg hover:shadow-amber-500/20 transition-all border border-amber-500/30 focus:outline-none focus:ring-2 focus:ring-amber-500/50 text-xs font-bold"
              aria-label={`Kullanıcı menüsü: ${user?.full_name || user?.username || "Kullanıcı"}`}
              type="button"
              onClick={() => setShowProfileMenu(!showProfileMenu)}
            >
              {getInitials()}
            </button>

            {showProfileMenu && (
              <div className="absolute right-0 top-full mt-2 w-64 glass-panel border border-amber-500/20 rounded-2xl shadow-2xl overflow-hidden animate-in slide-in-from-top-2 fade-in duration-200 z-50">
                {/* User info */}
                <div className="px-5 py-4 border-b border-slate-800 bg-slate-900/50">
                  <p className="text-sm font-semibold text-slate-100 truncate">{user?.full_name || user?.username}</p>
                  <p className="text-xs text-slate-400 truncate">{user?.email}</p>
                </div>

                {/* Menu items */}
                <div className="py-2">
                  <Link
                    href="/profile"
                    onClick={() => setShowProfileMenu(false)}
                    className="flex items-center gap-3 px-5 py-2.5 text-sm text-slate-300 hover:bg-amber-500/10 hover:text-amber-400 transition-colors"
                  >
                    <span>👤</span> Profilim
                  </Link>
                  <Link
                    href="/settings"
                    onClick={() => setShowProfileMenu(false)}
                    className="flex items-center gap-3 px-5 py-2.5 text-sm text-slate-300 hover:bg-amber-500/10 hover:text-amber-400 transition-colors"
                  >
                    <span>⚙️</span> Ayarlar
                  </Link>
                  <Link
                    href="/favorites"
                    onClick={() => setShowProfileMenu(false)}
                    className="flex items-center gap-3 px-5 py-2.5 text-sm text-slate-300 hover:bg-amber-500/10 hover:text-amber-400 transition-colors"
                  >
                    <span>⭐</span> Favorilerim
                  </Link>
                </div>

                {/* Logout */}
                <div className="border-t border-slate-800 py-2">
                  <button
                    onClick={() => { setShowProfileMenu(false); onLogout(); }}
                    className="flex items-center gap-3 px-5 py-2.5 text-sm text-red-400 hover:bg-red-500/10 transition-colors w-full text-left"
                  >
                    <span>🚪</span> Çıkış Yap
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
