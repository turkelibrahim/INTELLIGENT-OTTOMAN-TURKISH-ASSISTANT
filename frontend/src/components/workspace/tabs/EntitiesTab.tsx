"use client";

import { useState, useMemo } from "react";
import type { FullDocumentAnalysisResponse, EntityItem } from "@/lib/api";
import { entityDisplayText, translateInternalValue } from "@/lib/viewModel";
import { EntityKnowledgeModal } from "@/components/historical/EntityKnowledgeModal";
import { Landmark, Search } from 'lucide-react';


interface Props {
  result: FullDocumentAnalysisResponse;
}

type FilterKey = "all" | "persons" | "places" | "institutions";

const FILTERS: Array<{ key: FilterKey; label: string; icon: React.ReactNode }> = [
  { key: "all",            label: "Tümü", icon: <Search className="w-4 h-4 inline-block mr-1 align-text-bottom" /> },
  { key: "persons",        label: "Kişiler", icon: <Search className="w-4 h-4 inline-block mr-1 align-text-bottom" /> },
  { key: "places",         label: "Yerler", icon: <Search className="w-4 h-4 inline-block mr-1 align-text-bottom" /> },
  { key: "institutions",   label: "Kurumlar", icon: <Landmark className="w-5 h-5 inline-block mr-1 align-text-bottom" /> },
];

export default function EntitiesTab({ result }: Props) {
  const [activeFilter, setActiveFilter] = useState<FilterKey>("all");
  const [selectedEntity, setSelectedEntity] = useState<{name: string, desc: string} | null>(null);

  const entityGroups = useMemo(() => {
    const persons = (result.entities?.persons ?? []);
    const places = (result.entities?.places ?? []);
    const institutions = (result.entities?.institutions ?? []);

    return {
      persons: { label: "Kişi", color: "bg-[var(--ota-ocean)]/10 text-[var(--ota-ocean)] border-[var(--ota-ocean)]/30", items: persons },
      places: { label: "Yer", color: "bg-[var(--ota-iznik-turquoise)]/10 text-[var(--ota-iznik-turquoise)] border-[var(--ota-iznik-turquoise)]/30", items: places },
      institutions: { label: "Kurum", color: "bg-[var(--ota-gold)]/10 text-[var(--ota-gold)] border-[var(--ota-gold)]/30", items: institutions },
    };
  }, [result]);

  const totalCount = Object.values(entityGroups).reduce((sum, g) => sum + g.items.length, 0);

  if (totalCount === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center bg-[var(--ota-bg-2)]/50 rounded-xl border border-[var(--ota-border)] m-4">
        <span className="text-4xl mb-4 opacity-50"><Search className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>
        <h3 className="text-lg font-semibold text-[var(--ota-text)] mb-2">Kayıt Bulunamadı</h3>
        <p className="text-sm text-[var(--ota-text-muted)]">Belge içerisinde belirgin bir kişi, yer veya kurum tespit edilemedi.</p>
      </div>
    );
  }

  const displayGroups = activeFilter === "all"
    ? Object.entries(entityGroups).filter(([, g]) => g.items.length > 0)
    : Object.entries(entityGroups).filter(([k, g]) => k === activeFilter && g.items.length > 0);

  return (
    <div className="p-4 lg:p-6 h-full overflow-y-auto custom-scrollbar relative bg-[var(--ota-bg-1)]">
      
      <div className="mb-6">
        <h3 className="text-2xl font-serif font-bold text-[var(--ota-text)] mb-2">Kişiler ve Yerler</h3>
        <p className="text-sm text-[var(--ota-text-muted)] leading-relaxed">
          Osmanlı belgesi üzerinde yapay zeka tarafından tespit edilen tarihi şahıslar, mekanlar ve kurumlar listesi. <strong className="text-[var(--ota-gold)] font-medium">Tarihsel referans detayları için kartlara tıklayın.</strong>
        </p>
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-2 lg:gap-3 mb-8 border-b border-[var(--ota-border)] pb-6" role="toolbar">
        {FILTERS.map((f) => {
          const count = f.key === "all" ? totalCount : entityGroups[f.key as Exclude<FilterKey, "all">]?.items.length ?? 0;
          if (f.key !== "all" && count === 0) return null;
          const isActive = activeFilter === f.key;
          
          return (
            <button
              key={f.key}
              type="button"
              onClick={() => setActiveFilter(f.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                isActive 
                  ? "bg-[var(--ota-gold)]/10 text-[var(--ota-gold)] border border-[var(--ota-gold)] shadow-sm" 
                  : "bg-[var(--ota-surface-dark)] text-[var(--ota-text-muted)] hover:text-[var(--ota-text)] border border-[var(--ota-border)] hover:border-[var(--ota-border-hover)]"
              }`}
            >
              <span className="text-lg">{f.icon}</span>
              <span>{f.label}</span>
              <span className={`px-2 py-0.5 rounded-md text-xs font-bold ${isActive ? "bg-[var(--ota-gold)]/20 text-[var(--ota-gold)]" : "bg-[var(--ota-bg-2)] text-[var(--ota-text-muted)]"}`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Entity grids */}
      <div className="flex flex-col gap-10">
        {displayGroups.map(([key, group]) => (
          <div key={key}>
            <div className="flex items-center gap-4 mb-5">
              <h4 className="text-sm font-bold uppercase tracking-[0.15em] text-[var(--ota-text)]">{group.label} Envanteri</h4>
              <div className="flex-1 h-px bg-[var(--ota-border)]/50"></div>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 lg:gap-6">
              {group.items.map((entity: EntityItem, i: number) => {
                const rawText = entityDisplayText(entity);
                const text = translateInternalValue(rawText);
                const score = entity.confidence_score ? Math.round(entity.confidence_score * 100) : 0;
                const isError = score > 0 && score < 30; // Only red for critical uncertainty (<30%)
                
                const confidenceBadgeColor = isError 
                  ? 'bg-[var(--ota-ruby)]/10 text-[var(--ota-ruby)] border-[var(--ota-ruby)]/20'
                  : score >= 80 ? 'bg-[var(--ota-success)]/10 text-[var(--ota-success)] border-[var(--ota-success)]/20' 
                  : 'bg-[var(--ota-gold)]/10 text-[var(--ota-gold)] border-[var(--ota-gold)]/20';

                // Format metadata
                const source = entity.metadata?.source || "Belge";
                const desc = (entity.metadata?.description || (entity as Record<string, string>).meaning || entity.normalized_value || "") as string;

                return (
                  <div 
                    key={`${key}-${rawText}-${i}`}
                    onClick={() => setSelectedEntity({ name: text, desc })}
                    className="group relative flex flex-col justify-between glass-panel bg-[var(--ota-surface)] hover:bg-[var(--ota-bg-2)] border border-[var(--ota-border)] hover:border-[var(--ota-gold)]/50 p-5 lg:p-6 rounded-xl cursor-pointer transition-all duration-300 shadow-sm hover:shadow-md"
                  >
                    <div>
                      {/* Top Header: Ad */}
                      <h5 className="text-lg font-serif font-semibold text-[var(--ota-text)] group-hover:text-[var(--ota-gold)] transition-colors line-clamp-2 leading-snug mb-3" title={text}>
                        {text}
                      </h5>

                      <div className="flex flex-col gap-2 mt-4">
                        {/* Row: Tür */}
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-[var(--ota-text-muted)]">Tür</span>
                          <span className={`font-medium px-2 py-0.5 rounded border ${group.color}`}>
                            {group.label}
                          </span>
                        </div>

                        {/* Row: Confidence */}
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-[var(--ota-text-muted)]">Güven</span>
                          <span className={`font-medium px-2 py-0.5 rounded border ${score > 0 ? confidenceBadgeColor : 'bg-[var(--ota-bg-2)] text-[var(--ota-text-muted)] border-[var(--ota-border)]'}`}>
                            {score > 0 ? `%${score}` : "N/A"}
                          </span>
                        </div>

                        {/* Row: Kaynak */}
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-[var(--ota-text-muted)]">Kaynak</span>
                          <span className="font-medium text-[var(--ota-text)] px-2 py-0.5 bg-[var(--ota-bg-2)] rounded border border-[var(--ota-border)] truncate max-w-[120px]" title={String(source)}>
                            {String(source)}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Bottom Indicator for Document Position */}
                    {(entity.start_offset != null || Boolean(entity.metadata?.line_no)) && (
                      <div className="mt-5 pt-3 border-t border-[var(--ota-border)]/40 flex justify-between items-center">
                        <p className="text-[10px] uppercase tracking-wider text-[var(--ota-text-muted)] flex items-center gap-1">
                          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                          {entity.metadata?.line_no ? `Satır ${String(entity.metadata.line_no)}` : "Belgede"}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Etkileşimli Tarihsel Analiz Penceresi (Modal) */}
      <EntityKnowledgeModal 
        isOpen={!!selectedEntity}
        entityName={selectedEntity?.name || ""}
        description={selectedEntity?.desc || ""}
        onClose={() => setSelectedEntity(null)} 
      />
    </div>
  );
}

