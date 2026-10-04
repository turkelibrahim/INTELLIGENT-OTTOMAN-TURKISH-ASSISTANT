"use client";

import { useMemo, useState } from "react";
import type { FullDocumentAnalysisResponse } from "@/lib/api";
import { mapSourceCard } from "@/lib/viewModel";

interface Props {
  result: FullDocumentAnalysisResponse;
}

export default function SourcesTab({ result }: Props) {
  const [copiedId, setCopiedId] = useState("");

  const sources = useMemo(() => {
    const all = result.evidence?.historical_external_evidence ?? [];
    // Deduplicate by source_id/title
    const seen = new Set<string>();
    return all
      .map((item, i) => mapSourceCard(item as Record<string, unknown>, i))
      .filter((s) => {
        const key = `${s.id}-${s.title}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
  }, [result]);

  const copyCitation = (id: string, citation: string) => {
    if (!citation) return;
    void navigator.clipboard.writeText(citation);
    setCopiedId(id);
    setTimeout(() => setCopiedId(""), 2000);
  };

  if (sources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center bg-slate-900/50 rounded-xl">
        <span className="text-5xl mb-4">📚</span>
        <h3 className="text-lg font-semibold text-slate-200 mb-2">Kaynak Bulunamadı</h3>
        <p className="text-sm text-slate-400">Yapay zeka, belgeyi incelerken doğrulanmış herhangi bir harici kaynak, kitap veya veri tabanı verisi tespit edemedi.</p>
      </div>
    );
  }

  return (
    <div className="p-6 h-full overflow-y-auto custom-scrollbar bg-slate-900/50">
      
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xl font-bold text-slate-100">Yapay Zeka Referans Kaynakları</h3>
          <span className="bg-amber-500/20 text-amber-500 px-3 py-1 rounded-full text-sm font-semibold border border-amber-500/30">
            {sources.length} Kaynak
          </span>
        </div>
        <p className="text-sm text-slate-400">
          Bu analiz hazırlanırken yapay zekanın kullandığı ve doğruladığı akademik metinler, veri tabanları ve harici bilgiler. 
          Araştırmalarınızda kullanmak için referansları kopyalayabilirsiniz.
        </p>
      </div>

      <div className="flex flex-col gap-6">
        {sources.map((source) => {
          const isVerified = source.isVerified;
          
          return (
            <div key={source.id} className="bg-slate-800/80 border border-slate-700 hover:border-amber-500/30 rounded-2xl p-5 shadow-lg transition-all">
              
              {/* Başlık ve Durum Rozeti */}
              <div className="flex justify-between items-start mb-4 gap-4">
                <h4 className="text-lg font-semibold text-slate-200 leading-snug flex items-start gap-2">
                  <span className="mt-0.5 text-amber-500">📖</span>
                  <span>{source.title}</span>
                </h4>
                
                <span className={`shrink-0 px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wide border ${
                  isVerified 
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" 
                    : "bg-slate-700 text-slate-400 border-slate-600"
                }`}>
                  {isVerified ? "✓ Doğrulandı" : "Doğrulanmamış"}
                </span>
              </div>

              {/* Meta Etiketleri */}
              <div className="flex flex-wrap gap-2 mb-4">
                {source.sourceType && (
                  <span className="bg-slate-900/80 text-slate-300 px-2 py-1 rounded text-xs font-medium border border-slate-700/50 flex items-center gap-1">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
                    Tür: {source.sourceType}
                  </span>
                )}
                {source.relevance && (
                  <span className="bg-slate-900/80 text-slate-300 px-2 py-1 rounded text-xs font-medium border border-slate-700/50 flex items-center gap-1">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>
                    İlgililik: {source.relevance}
                  </span>
                )}
              </div>

              {/* Yapay Zekanın Desteklediği Bilgi (Quote) */}
              {source.claim && (
                <div className="bg-slate-900/60 rounded-xl p-4 border-l-2 border-amber-500 mb-4">
                  <span className="block text-xs font-semibold text-amber-500 uppercase tracking-wider mb-2">Desteklenen Tarihi Bilgi</span>
                  <p className="text-sm text-slate-300 italic leading-relaxed">&ldquo;{source.claim}&rdquo;</p>
                </div>
              )}

              {/* Atıfı Kopyala Bölümü */}
              {(source.citation || source.url) && (
                <div className="mt-4 pt-4 border-t border-slate-700/50 flex flex-wrap justify-between items-center gap-4">
                  {source.citation && (
                    <div className="text-xs text-slate-500 truncate flex-1 font-mono min-w-[200px]" title={source.citation}>
                      {source.citation}
                    </div>
                  )}
                  
                  <div className="flex items-center gap-2 shrink-0 ml-auto">
                    {source.url && (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all bg-blue-500/10 text-blue-400 border border-blue-500/30 hover:bg-blue-500/20"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                        Kaynağa Git
                      </a>
                    )}
                    
                    {source.citation && (
                      <button
                        type="button"
                        onClick={() => copyCitation(source.id, source.citation!)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                          copiedId === source.id
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : "bg-slate-800 text-slate-300 border border-slate-600 hover:bg-slate-700 hover:text-white"
                        }`}
                      >
                        {copiedId === source.id ? (
                          <>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                            Kopyalandı
                          </>
                        ) : (
                          <>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>
                            Atıfı Kopyala
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
