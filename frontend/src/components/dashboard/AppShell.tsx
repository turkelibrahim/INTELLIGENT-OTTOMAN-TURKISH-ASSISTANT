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

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="ota-shell font-sans text-[var(--ota-text)] selection:bg-[var(--ota-imperial-gold)]/30">
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      
      {/* Mobile overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-sm" 
          onClick={() => setIsSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <div className="ota-main-wrapper transition-all duration-300">
        <Header user={user} onLogout={handleLogout} onMenuToggle={() => setIsSidebarOpen(!isSidebarOpen)} />
        <main className="ota-content-area relative focus:outline-none" id="main-content" tabIndex={-1}>
          {/* Particles overlay for depth */}
          <div className="absolute inset-0 opacity-[0.03] bg-[url('/auth/particles.png')] bg-repeat pointer-events-none" aria-hidden="true" />
          <div className="relative z-10 w-full h-full p-4 lg:p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
