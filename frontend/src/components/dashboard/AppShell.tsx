"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authApi, getToken, removeToken, type UserResponse } from "@/lib/api";
import Sidebar from "./Sidebar";
import Header from "./Header";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);

  useEffect(() => {
    if (!getToken()) {
      // router.replace("/login");
      // return;
    }
    let cancelled = false;
    authApi.getMe()
      .then((u) => {
        if (!cancelled) setUser(u);
      })
      .catch(() => {
        if (!cancelled) {
          removeToken();
          // router.replace("/login");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  const handleLogout = async () => {
    try { await authApi.logout(); } catch { /* silent */ }
    removeToken();
    router.replace("/login");
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-200 selection:bg-amber-500/30 font-sans">
      <Sidebar />
      <div className="flex flex-col flex-1 lg:pl-[260px] min-h-screen relative w-full transition-all duration-300">
        <Header user={user} onLogout={handleLogout} />
        <main className="flex-1 overflow-x-hidden relative focus:outline-none bg-[url('/auth/particles.png')] bg-repeat" id="main-content" tabIndex={-1}>
          <div className="absolute inset-0 bg-slate-950/80 pointer-events-none" aria-hidden="true" />
          <div className="relative z-10 w-full h-full p-4 lg:p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
