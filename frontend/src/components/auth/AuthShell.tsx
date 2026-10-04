"use client";

import Link from "next/link";
import Image from "next/image";
import type { ReactNode } from "react";

type AuthMode = "login" | "register";

interface AuthShellProps {
  mode: AuthMode;
  title: string;
  subtitle: string;
  children: ReactNode;
}

const trustItems = [
  { label: "Güvenli Veri Koruma", icon: "shield" },
  { label: "KVKK Uyumlu", icon: "lock" },
  { label: "Akademik Kullanım İçin Uygundur", icon: "academic" },
] satisfies Array<{ label: string; icon: "shield" | "lock" | "academic" }>;

export function AuthShell({ mode, title, subtitle, children }: AuthShellProps) {
  const isRegister = mode === "register";

  return (
    <main className={`auth-page auth-page-${mode}`}>
      {/* Background & Decorative Elements */}
      <div className="auth-bg-ambient" aria-hidden="true" />
      <div className="auth-particles" aria-hidden="true" />

      {/* Left Area: Ottoman Document */}
      <div className="auth-document-wrapper" aria-hidden="true">
        <Image 
          src="/auth/ottoman-document.png" 
          alt="Ottoman Document" 
          fill 
          className="auth-image-left"
          priority
        />
        <div className="auth-ai-medallion">AI</div>
      </div>

      {/* Right Area: Mosque */}
      <div className="auth-mosque-wrapper" aria-hidden="true">
        <Image 
          src="/auth/mosque-silhouette.png" 
          alt="Mosque Silhouette" 
          fill 
          className="auth-image-right"
          priority
        />
      </div>

      {/* Top Right: Floral */}
      <div className="auth-floral-wrapper" aria-hidden="true">
         <Image 
          src="/auth/floral-pattern.png" 
          alt="Floral Pattern" 
          fill 
          className="auth-image-corner"
        />
      </div>

      <section className="auth-stage" aria-label="Kimlik doğrulama">
        <BrandMark />

        <div className="auth-card">
          <div className="auth-card-header">
            <h1>{title}</h1>
            <div className="auth-ornament" aria-hidden="true">
               <span className="auth-ornament-diamond"></span>
            </div>
            <p>{subtitle}</p>
          </div>

          {children}

          <div className="auth-divider">
            <span className="auth-ornament-diamond"></span>
          </div>

          <div className="auth-switch">
            {isRegister ? (
              <>
                Zaten hesabın var mı? <Link href="/login">Giriş Yap</Link>
              </>
            ) : (
              <>
                Hesabın yok mu? <Link href="/register">Kayıt Ol</Link>
              </>
            )}
          </div>
        </div>
      </section>

      <footer className="auth-footer">
        <div className="auth-trust-row">
          {trustItems.map((item) => (
            <div key={item.label} className="auth-trust-item">
               <TrustIcon name={item.icon} />
               <span>{item.label}</span>
            </div>
          ))}
        </div>
        <small>© 2026 Intelligent Ottoman Turkish Assistant. Tüm hakları saklıdır.</small>
      </footer>
    </main>
  );
}

function BrandMark() {
  return (
    <div className="auth-brand">
      <div className="auth-tughra-wrapper">
         <Image 
          src="/auth/tughra.png" 
          alt="Tughra" 
          fill 
          className="auth-tughra-img"
          priority
        />
      </div>
      <div className="auth-brand-text">
        <span className="brand-line-1">INTELLIGENT</span>
        <strong className="brand-line-2">OTTOMAN TURKISH</strong>
        <em className="brand-line-3">
          <span className="brand-dash"></span>
          ASSISTANT
          <span className="brand-dash"></span>
        </em>
      </div>
    </div>
  );
}

function TrustIcon({ name }: { name: "shield" | "lock" | "academic" }) {
   const paths = {
      shield: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>,
      lock: <><rect x="3" y="11" width="18" height="11" rx="2" ry="2" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><path d="M7 11V7a5 5 0 0110 0v4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></>,
      academic: <><path d="M22 10l-10-5-10 5 10 5 10-5z" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><path d="M6 12v5c3 3 9 3 12 0v-5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></>
   };
   return <svg viewBox="0 0 24 24" width="16" height="16" className="auth-trust-icon">{paths[name]}</svg>;
}
