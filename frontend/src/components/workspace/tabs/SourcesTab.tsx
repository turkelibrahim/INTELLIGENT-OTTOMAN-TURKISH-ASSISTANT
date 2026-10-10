"use client";

import { useMemo, useState } from "react";
import type { FullDocumentAnalysisResponse } from "@/lib/api";
import { mapSourceCard } from "@/lib/viewModel";
import { BookCopy } from 'lucide-react';

interface Props {
  result: FullDocumentAnalysisResponse;
}

export default function SourcesTab({ result }: Props) {
  const [copiedId, setCopiedId] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [sortBy, setSortBy] = useState("relevance");

  const baseSources = useMemo(() => {
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

  const sourceTypes = useMemo(() => {
    const types = new Set(baseSources.map(s => s.sourceType).filter(Boolean));
    return Array.from(types).sort();
  }, [baseSources]);

  const sources = useMemo(() => {
    let filtered = baseSources;

    // Text search
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(s => 
        s.title.toLowerCase().includes(q) || 
        s.claim.toLowerCase().includes(q) || 
        s.citation.toLowerCase().includes(q)
      );
    }

    // Type filter
    if (typeFilter !== "all") {
      filtered = filtered.filter(s => s.sourceType === typeFilter);
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
      if (sortBy === "title") {
        return a.title.localeCompare(b.title);
      }
      // "relevance" descending
      const parseRel = (val: string) => parseInt(val.replace(/\D/g, "")) || 0;
      return parseRel(b.relevance) - parseRel(a.relevance);
    });

    return filtered;
  }, [baseSources, searchQuery, typeFilter, sortBy]);

  const copyCitation = (id: string, citation: string) => {
    if (!citation) return;
    void navigator.clipboard.writeText(citation);
    setCopiedId(id);
    setTimeout(() => setCopiedId(""), 2000);
  };

  if (baseSources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center bg-[var(--ota-bg-2)] rounded-xl opacity-70">
        <span className="text-[var(--ota-gold)] mb-3 opacity-50"><BookCopy className="w-10 h-10 text-current" /></span>
        <h3 className="text-base font-semibold text-[var(--ota-text)] mb-1">Kaynak Bulunamadı</h3>
        <p className="text-xs text-[var(--ota-text-muted)] max-w-[250px]">Yapay zeka, belgeyi incelerken doğrulanmış herhangi bir harici kaynak, kitap veya veri tabanı verisi tespit edemedi.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[var(--ota-bg)]">
      
      {/* Header & Controls */}
      <div className="p-4 border-b border-[var(--ota-border)] shrink-0 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-[var(--ota-text)]">Yapay Zeka Referans Kaynakları</h3>
          <span className="bg-[var(--ota-gold)]/10 text-[var(--ota-gold)] px-2 py-0.5 rounded text-[10px] font-bold border border-[var(--ota-gold)]/30 uppercase tracking-wide">
            {baseSources.length} Kaynak
          </span>
        </div>

        {/* Filters Row */}
        <div className="flex flex-col md:flex-row gap-2 text-xs">
          <input 
            type="text" 
            placeholder="Kaynaklarda ara..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 bg-[var(--ota-bg-2)] border border-[var(--ota-border)] rounded-md px-3 py-1.5 text-[var(--ota-text)] placeholder:text-[var(--ota-text-muted)] outline-none focus:border-[var(--ota-gold)]/50 transition-colors"
          />
          <select 
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-[var(--ota-bg-2)] border border-[var(--ota-border)] rounded-md px-2 py-1.5 text-[var(--ota-text)] outline-none focus:border-[var(--ota-gold)]/50 cursor-pointer"
          >
            <option value="all">Tüm Türler</option>
            {sourceTypes.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <select 
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-[var(--ota-bg-2)] border border-[var(--ota-border)] rounded-md px-2 py-1.5 text-[var(--ota-text)] outline-none focus:border-[var(--ota-gold)]/50 cursor-pointer shrink-0"
          >
            <option value="relevance">İlgililik (Önce Yüksek)</option>
            <option value="title">İsim (A-Z)</option>
          </select>
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-3 flex flex-col gap-3">
        {sources.length === 0 ? (
           <div className="text-center p-6 text-[var(--ota-text-muted)] text-xs">Filtrelere uygun kaynak bulunamadı.</div>
        ) : sources.map((source) => {
          const isVerified = source.isVerified;
          
          return (
            <div key={source.id} className="bg-[var(--ota-bg-2)]/50 border border-[var(--ota-border)] hover:border-[var(--ota-gold)]/40 rounded-lg p-3 shadow-sm transition-all flex flex-col gap-2">
              
              <div className="flex justify-between items-start gap-3">
                <h4 className="text-sm font-semibold text-[var(--ota-text)] leading-tight truncate flex-1" title={source.title}>
                  {source.title}
                </h4>
                {isVerified && (
                  <span className="shrink-0 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-[var(--ota-success)]/10 text-[var(--ota-success)] border border-[var(--ota-success)]/30">
                    Doğrulandı
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-2 text-[10px] mt-1">
                {source.sourceType && (
                  <div className="flex flex-col gap-0.5">
                    <span className="text-[var(--ota-text-muted)] uppercase font-semibold">Tür</span>
                    <span className="text-[var(--ota-text-2)] truncate" title={source.sourceType}>{source.sourceType}</span>
                  </div>
                )}
                {source.relevance && (
                  <div className="flex flex-col gap-0.5">
                    <span className="text-[var(--ota-text-muted)] uppercase font-semibold">İlgililik</span>
                    <span className="text-[var(--ota-gold)] font-medium">{source.relevance}</span>
                  </div>
                )}
              </div>

              {source.claim && (
                <div className="mt-1 flex flex-col gap-0.5">
                  <span className="text-[9px] font-bold text-[var(--ota-text-muted)] uppercase tracking-wider">Desteklenen Bilgi</span>
                  <p className="text-[11px] text-[var(--ota-text)]/90 italic leading-snug line-clamp-2" title={source.claim}>
                    &ldquo;{source.claim}&rdquo;
                  </p>
                </div>
              )}

              {/* Actions */}
              {(source.citation || source.url) && (
                <div className="mt-2 pt-2 border-t border-[var(--ota-border)] flex items-center justify-end gap-2">
                  {source.url && (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 px-2 py-1 rounded bg-[var(--ota-bg)] border border-[var(--ota-border)] text-[var(--ota-iznik-turquoise)] hover:border-[var(--ota-iznik-turquoise)]/50 text-[10px] font-semibold transition-colors"
                    >
                      Kaynağı Gör
                    </a>
                  )}
                  {source.citation && (
                    <button
                      type="button"
                      onClick={() => copyCitation(source.id, source.citation!)}
                      className={`flex items-center gap-1 px-2 py-1 rounded text-[10px] font-semibold transition-colors border ${
                        copiedId === source.id
                          ? "bg-[var(--ota-success)]/10 text-[var(--ota-success)] border-[var(--ota-success)]/30"
                          : "bg-[var(--ota-bg)] text-[var(--ota-text-2)] border-[var(--ota-border)] hover:border-[var(--ota-gold)]/50 hover:text-[var(--ota-text)]"
                      }`}
                    >
                      {copiedId === source.id ? "Kopyalandı" : "Atıfı Kopyala"}
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
