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

export default function Sidebar({ isOpen, onClose }: { isOpen?: boolean; onClose?: () => void }) {
  return (
    <aside className={`ota-sidebar ${isOpen ? 'open' : ''}`} aria-label="Ana gezinme">
      {/* Logo */}
      <div className="ota-sidebar-logo justify-between">
        <div className="flex items-center gap-3">
          <div className="ota-logo-icon" aria-hidden="true">
            {Icons.tughra}
          </div>
          <div className="ota-logo-text">
            <span className="ota-logo-main">OSMANLICA</span>
            <span className="ota-logo-sub">BELGE ASİSTANI</span>
          </div>
        </div>
        {onClose && (
          <button className="lg:hidden text-[var(--ota-text-muted)] hover:text-[var(--ota-text)]" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="ota-sidebar-nav custom-scrollbar">
        <NavGroup label="ANA" items={NAV_MAIN} />
        <NavGroup label="ARAÇLAR" items={NAV_TOOLS} />
      </nav>

      {/* Footer pattern */}
      <div className="ota-sidebar-footer" aria-hidden="true">
        <div className="ota-sidebar-pattern" />
      </div>
    </aside>
  );
}
