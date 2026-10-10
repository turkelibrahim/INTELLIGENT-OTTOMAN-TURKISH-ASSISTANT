"use client";

import { useEffect, useState, createContext, useContext } from "react";
import { useRouter } from "next/navigation";
import { authApi, getToken, removeToken, type UserResponse } from "@/lib/api";
import Sidebar from "./Sidebar";
import Header from "./Header";

// Focus Mode Context
interface FocusModeContextType {
  isFocusMode: boolean;
  setIsFocusMode: (v: boolean) => void;
}

const FocusModeContext = createContext<FocusModeContextType | null>(null);

export function useFocusMode() {
  const ctx = useContext(FocusModeContext);
  if (!ctx) throw new Error("useFocusMode must be used within AppShell");
  return ctx;
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isFocusMode, setIsFocusMode] = useState(false);

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
    <FocusModeContext.Provider value={{ isFocusMode, setIsFocusMode }}>
      <div className={`ota-shell font-sans text-[var(--ota-text)] selection:bg-[var(--ota-imperial-gold)]/30 ${isFocusMode ? 'focus-mode-active' : ''}`}>
        <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} isFocusMode={isFocusMode} />
        
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
            {/* Floral pattern overlay for depth */}
            <div className="absolute inset-0 opacity-[0.03] bg-[url('/auth/floral-pattern.png')] bg-repeat pointer-events-none" aria-hidden="true" />
            <div className="relative z-10 w-full h-full p-4 lg:p-6">
              {children}
            </div>
          </main>
        </div>
      </div>
    </FocusModeContext.Provider>
  );
}
