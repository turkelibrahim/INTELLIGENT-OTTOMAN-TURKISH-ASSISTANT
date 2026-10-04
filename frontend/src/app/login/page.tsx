"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AuthShell } from "@/components/auth/AuthShell";
import { ApiError, authApi, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");

    if (!email.trim() || !password) {
      setError("E-posta ve şifre alanlarını doldurun.");
      return;
    }

    setIsLoading(true);
    try {
      const result = await authApi.login({ email: email.trim(), password });
      setToken(result.access_token, rememberMe);
      router.push("/dashboard");
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.status === 401 ? "E-posta veya şifre hatalıı." : err.detail || "Giriş yapılamadı.");
      } else if (err instanceof TypeError && err.message === "Failed to fetch") {
        setError("Sunucuya bağlanılamadı. Backend servisinin çalıştığını kontrol edin.");
      } else {
        setError("Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthShell
      mode="login"
      title="Giriş Yap"
      subtitle="Hesabınıza erişmek için bilgilerinizi girin."
    >
      <div className="min-h-[48px] mb-4 w-full">
        {error && (
          <div className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm animate-in fade-in slide-in-from-top-2 duration-300 glass-panel" role="alert">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
            {error}
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="auth-form">
        <AuthField
          id="email"
          label="E-posta"
          type="email"
          value={email}
          autoComplete="email"
          placeholder="ornek@email.com"
          icon="mail"
          disabled={isLoading}
          onChange={setEmail}
        />

        <AuthField
          id="password"
          label="Şifre"
          type={showPassword ? "text" : "password"}
          value={password}
          autoComplete="current-password"
          placeholder="••••••••••"
          icon="lock"
          disabled={isLoading}
          minLength={6}
          trailingButton={{
            label: showPassword ? "Şifreyi gizle" : "Şifreyi göster",
            active: showPassword,
            onClick: () => setShowPassword((value) => !value),
          }}
          onChange={setPassword}
        />

        <div className="auth-form-row">
          <label className="auth-checkbox">
            <input
              type="checkbox"
              checked={rememberMe}
              disabled={isLoading}
              onChange={(event) => setRememberMe(event.target.checked)}
            />
            <span />
            Beni hatırla
          </label>
          <Link href="/login" className="auth-muted-link" aria-disabled="true">
            Şifremi Unuttum
          </Link>
        </div>

        <button type="submit" className="auth-submit" disabled={isLoading}>
          {isLoading ? "Giriş yapılıyor..." : "Giriş Yap"}
        </button>
      </form>
    </AuthShell>
  );
}

function AuthField({
  id,
  label,
  type,
  value,
  placeholder,
  icon,
  disabled,
  autoComplete,
  minLength,
  trailingButton,
  onChange,
}: {
  id: string;
  label: string;
  type: "email" | "password" | "text";
  value: string;
  placeholder: string;
  icon: "mail" | "lock" | "user";
  disabled: boolean;
  autoComplete: string;
  minLength?: number;
  trailingButton?: {
    label: string;
    active: boolean;
    onClick: () => void;
  };
  onChange: (value: string) => void;
}) {
  return (
    <label className="auth-field" htmlFor={id}>
      <span>{label}</span>
      <div className="auth-input-wrap">
        <AuthIcon name={icon} />
        <input
          id={id}
          name={id}
          type={type}
          required
          value={value}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete={autoComplete}
          minLength={minLength}
          onChange={(event) => onChange(event.target.value)}
        />
        {trailingButton && (
          <button
            type="button"
            className={`auth-eye ${trailingButton.active ? "active" : ""}`}
            aria-label={trailingButton.label}
            disabled={disabled}
            onClick={trailingButton.onClick}
          >
            <AuthIcon name="eye" />
          </button>
        )}
      </div>
    </label>
  );
}

function AuthIcon({ name }: { name: "mail" | "lock" | "user" | "eye" }) {
  const paths = {
    mail: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="m3 7 9 6 9-6" />
      </>
    ),
    lock: (
      <>
        <rect x="5" y="10" width="14" height="10" rx="2" />
        <path d="M8 10V7a4 4 0 0 1 8 0v3" />
      </>
    ),
    user: (
      <>
        <path d="M20 21a8 8 0 0 0-16 0" />
        <circle cx="12" cy="7" r="4" />
      </>
    ),
    eye: (
      <>
        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6Z" />
        <circle cx="12" cy="12" r="3" />
      </>
    ),
  };

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      {paths[name]}
    </svg>
  );
}
