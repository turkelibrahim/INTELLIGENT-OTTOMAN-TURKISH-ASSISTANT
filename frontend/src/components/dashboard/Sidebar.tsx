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
    <div className="mb-6">
      <span className="block px-4 py-2 text-xs font-semibold tracking-wider text-slate-400/80 uppercase">
        {label}
      </span>
      <div className="space-y-1 mt-1">
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
              className={`group flex items-center gap-3 px-4 py-2.5 mx-2 rounded-xl transition-all duration-300 relative overflow-hidden ${
                isActive
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-[inset_0_0_12px_rgba(245,158,11,0.05)]"
                  : "text-slate-300 hover:bg-white/5 hover:text-white border border-transparent"
              }`}
              aria-current={isActive ? "page" : undefined}
            >
              {isActive && (
                <span className="absolute left-0 top-0 bottom-0 w-1 bg-amber-400 rounded-r-md shadow-[0_0_8px_rgba(251,191,36,0.6)]" aria-hidden="true" />
              )}
              <span className={`flex-shrink-0 transition-transform duration-300 ${isActive ? "scale-110" : "group-hover:scale-110"}`}>
                {item.icon}
              </span>
              <span className="font-medium text-sm tracking-wide">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

export default function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-40 w-[260px] flex flex-col glass-panel border-r border-amber-500/10" aria-label="Ana gezinme">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 h-[72px] border-b border-amber-500/10 bg-slate-900/20 backdrop-blur-md">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center shadow-lg shadow-amber-500/20 text-white" aria-hidden="true">
          {Icons.tughra}
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-bold tracking-widest text-slate-100 uppercase">OSMANLICA</span>
          <span className="text-[10px] font-semibold tracking-[0.2em] text-amber-400 uppercase">BELGE ASİSTANI</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-6 custom-scrollbar">
        <NavGroup label="ANA" items={NAV_MAIN} />
        <NavGroup label="ARAÇLAR" items={NAV_TOOLS} />
      </nav>

      {/* Footer pattern */}
      <div className="p-4 border-t border-amber-500/10 bg-slate-900/20" aria-hidden="true">
        <div className="h-20 w-full opacity-20 bg-[url('/auth/floral-pattern.png')] bg-contain bg-center bg-no-repeat" />
      </div>
    </aside>
  );
}
