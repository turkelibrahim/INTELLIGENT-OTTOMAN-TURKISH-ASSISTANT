"use client";

import { useState, useMemo } from "react";
import type { FullDocumentAnalysisResponse } from "@/lib/api";
import { entityDisplayText, entityIsKnown } from "@/lib/viewModel";
import { EntityKnowledgeModal } from "@/components/historical/EntityKnowledgeModal";

interface Props {
  result: FullDocumentAnalysisResponse;
}

type FilterKey = "all" | "persons" | "places" | "institutions" | "dates" | "document_marks";

const FILTERS: Array<{ key: FilterKey; label: string; icon: string }> = [
  { key: "all",            label: "Tümü", icon: "📑" },
  { key: "persons",        label: "Kişiler", icon: "👤" },
  { key: "places",         label: "Yerler", icon: "🌍" },
  { key: "institutions",   label: "Kurumlar", icon: "🏛️" },
  { key: "dates",          label: "Tarihler", icon: "📅" },
  { key: "document_marks", label: "Belge İşaretleri", icon: "✒️" },
];

export default function EntitiesTab({ result }: Props) {
  const [activeFilter, setActiveFilter] = useState<FilterKey>("all");
  const [selectedEntity, setSelectedEntity] = useState<{name: string, desc: string} | null>(null);

  const entityGroups = useMemo(() => ({
    persons:        { label: "Kişi",           color: "bg-blue-500",      items: (result.entities?.persons ?? []).filter(entityIsKnown) },
    places:         { label: "Yer",            color: "bg-emerald-500",   items: (result.entities?.places ?? []).filter(entityIsKnown) },
    institutions:   { label: "Kurum",          color: "bg-purple-500",    items: (result.entities?.institutions ?? []).filter(entityIsKnown) },
    dates:          { label: "Tarih",          color: "bg-amber-500",     items: (result.entities?.dates ?? []).filter(entityIsKnown) },
    document_marks: { label: "Belge İş.",      color: "bg-rose-500",      items: (result.entities?.document_marks ?? []).filter(entityIsKnown) },
  }), [result]);

  const totalCount = Object.values(entityGroups).reduce((sum, g) => sum + g.items.length, 0);

  if (totalCount === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center bg-slate-900/50 rounded-xl">
        <span className="text-4xl mb-4">🔍</span>
        <h3 className="text-lg font-semibold text-slate-200 mb-2">Kayıt Bulunamadı</h3>
        <p className="text-sm text-slate-400">Belge içerisinde belirgin bir kişi, yer, kurum veya tarih tespit edilemedi.</p>
      </div>
    );
  }

  const displayGroups = activeFilter === "all"
    ? Object.entries(entityGroups).filter(([, g]) => g.items.length > 0)
    : Object.entries(entityGroups).filter(([k, g]) => k === activeFilter && g.items.length > 0);

  return (
    <div className="p-6 h-full overflow-y-auto custom-scrollbar bg-slate-900/50 relative">
      
      <div className="mb-6">
        <h3 className="text-xl font-bold text-slate-100 mb-2">Belgede Geçen Kişi ve Yerler</h3>
        <p className="text-sm text-slate-400">Okunan belge içerisinde yapay zeka tarafından tespit edilen tarihi şahıslar, mekanlar ve olay tarihleri. <strong className="text-amber-500">Tarihsel analiz için kartlara tıklayın.</strong></p>
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-2 mb-8" role="toolbar">
        {FILTERS.map((f) => {
          const count = f.key === "all" ? totalCount : entityGroups[f.key as Exclude<FilterKey, "all">]?.items.length ?? 0;
          if (f.key !== "all" && count === 0) return null;
          const isActive = activeFilter === f.key;
          
          return (
            <button
              key={f.key}
              type="button"
              onClick={() => setActiveFilter(f.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                isActive 
                  ? "bg-amber-500 text-slate-900 shadow-[0_0_15px_rgba(245,158,11,0.3)]" 
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700"
              }`}
            >
              <span>{f.icon}</span>
              <span>{f.label}</span>
              <span className={`px-2 py-0.5 rounded-full text-xs ${isActive ? "bg-amber-600/20 text-slate-900" : "bg-slate-900 text-slate-400"}`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Entity grids */}
      <div className="flex flex-col gap-8">
        {displayGroups.map(([key, group]) => (
          <div key={key}>
            <div className="flex items-center gap-3 mb-4">
              <h4 className="text-lg font-semibold text-slate-200">{group.label} Listesi</h4>
              <div className="flex-1 h-px bg-slate-800"></div>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {group.items.map((entity, i) => {
                const text = entityDisplayText(entity);
                const score = entity.confidence_score ? Math.round(entity.confidence_score * 100) : 0;
                
                return (
                  <div 
                    key={`${key}-${text}-${i}`}
                    onClick={() => setSelectedEntity({ name: text, desc: (entity.metadata?.description || (entity as Record<string, string>).meaning || entity.normalized_value || "") as string })}
                    className="group relative bg-slate-800/80 hover:bg-slate-800 border border-slate-700 hover:border-amber-500/50 p-4 rounded-xl cursor-pointer transition-all duration-300 shadow-md hover:shadow-lg hover:shadow-amber-500/10 overflow-hidden"
                  >
                    {/* Hover Glow Effect */}
                    <div className="absolute inset-0 bg-gradient-to-br from-amber-500/0 via-amber-500/0 to-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    
                    <div className="relative z-10 flex flex-col h-full justify-between">
                      <div>
                        <div className="flex justify-between items-start mb-2">
                          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-md ${group.color} text-white shadow-sm`}>
                            {group.label}
                          </span>
                          {score > 0 && (
                            <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${score >= 80 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>
                              %{score} Güven
                            </span>
                          )}
                        </div>
                        
                        <h5 className="text-lg font-bold text-slate-100 group-hover:text-amber-400 transition-colors mb-1 truncate" title={text}>
                          {text}
                        </h5>
                      </div>
                      
                      {(entity.start_offset != null || Boolean(entity.metadata?.line_no)) && (
                        <p className="text-xs text-slate-400 flex items-center gap-1 mt-4">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                          {entity.metadata?.line_no ? `Satır ${String(entity.metadata.line_no)}'de geçiyor` : "Belgede tespit edildi"}
                        </p>
                      )}
                    </div>
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
