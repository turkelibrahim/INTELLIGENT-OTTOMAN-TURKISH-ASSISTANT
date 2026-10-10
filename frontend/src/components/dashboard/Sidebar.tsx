"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icons } from "@/components/Icons";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const NAV_MAIN: NavItem[] = [
  { label: "Analizlerim",     href: "/dashboard",            icon: Icons.dashboard },
  { label: "Tarihsel Analiz", href: "/historical-analysis",  icon: Icons.history },
  { label: "Yeni Belge",      href: "/upload",               icon: Icons.upload },
  { label: "Arşiv",           href: "/archive",              icon: Icons.archive },
  { label: "Favoriler",       href: "/favorites",            icon: Icons.star },
  { label: "Sözlük",          href: "/dictionary",           icon: Icons.book },
];

const NAV_TOOLS: NavItem[] = [
  { label: "Görüntü İşleme",  href: "/image-processing-lab", icon: Icons.settings },
  { label: "Profilim",        href: "/profile",              icon: Icons.user },
  { label: "Ayarlar",         href: "/settings",             icon: Icons.settings },
  { label: "Yardım",          href: "/help",                 icon: Icons.help },
];

function NavGroup({ label, items }: { label: string; items: NavItem[] }) {
  const pathname = usePathname();
  return (
    <div className="ota-nav-group">
      <span className="ota-nav-group-label">{label}</span>
      <div className="space-y-[2px] mt-1">
        {items.map((item) => {
          const isActive =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname === item.href ||
                (item.href !== "/dashboard" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`ota-nav-item ${isActive ? "active" : ""}`}
              aria-current={isActive ? "page" : undefined}
            >
              {isActive && <span className="ota-nav-indicator" aria-hidden="true" />}
              <span className="ota-nav-icon">{item.icon}</span>
              <span className="ota-nav-label">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

export default function Sidebar({ isOpen, onClose, isFocusMode }: { isOpen?: boolean; onClose?: () => void; isFocusMode?: boolean }) {
  return (
    <aside className={`ota-sidebar ${isOpen ? 'open' : ''} ${isFocusMode ? 'collapsed' : ''}`} aria-label="Ana gezinme">
      {/* Logo */}
      <div className="ota-sidebar-logo justify-between">
        <div className="flex items-center gap-3">
          <div className="ota-logo-icon" aria-hidden="true">
            {Icons.tughra}
          </div>
          {!isFocusMode && (
            <div className="ota-logo-text flex flex-col justify-center">
              <span className="text-[10px] font-bold tracking-[0.2em] text-[var(--ota-gold)] leading-tight">INTELLIGENT</span>
              <span className="text-[13px] font-serif font-bold text-[var(--ota-text)] leading-tight">OTTOMAN TURKISH</span>
              <span className="text-[8px] tracking-[0.3em] text-[var(--ota-text-muted)] leading-tight uppercase flex items-center justify-between w-full">
                <span className="h-px bg-[var(--ota-border)] flex-1 mr-1"></span>
                ASSISTANT
                <span className="h-px bg-[var(--ota-border)] flex-1 ml-1"></span>
              </span>
            </div>
          )}
        </div>
        {onClose && (
          <button className="lg:hidden text-[var(--ota-text-muted)] hover:text-[var(--ota-text)]" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="ota-sidebar-nav custom-scrollbar">
        {!isFocusMode && (
          <>
            <NavGroup label="ANA" items={NAV_MAIN} />
            <NavGroup label="ARAÇLAR" items={NAV_TOOLS} />
          </>
        )}
        {isFocusMode && (
          <div className="px-2 py-4 space-y-2">
            {NAV_MAIN.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="ota-nav-item-compact"
                title={item.label}
                aria-label={item.label}
              >
                <span className="ota-nav-icon">{item.icon}</span>
              </a>
            ))}
            {NAV_TOOLS.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="ota-nav-item-compact"
                title={item.label}
                aria-label={item.label}
              >
                <span className="ota-nav-icon">{item.icon}</span>
              </a>
            ))}
          </div>
        )}
      </nav>

      {/* Footer pattern */}
      {!isFocusMode && (
        <div className="ota-sidebar-footer" aria-hidden="true">
          <div className="ota-sidebar-pattern" />
        </div>
      )}
    </aside>
  );
}
