"use client";

import type { FullDocumentAnalysisResponse } from "@/lib/api";
import { mapConfidenceToPercent } from "@/lib/viewModel";
import { Brain, Settings, BarChart2 } from 'lucide-react';


interface Props {
  result: FullDocumentAnalysisResponse;
}

// Kompakt metrik satırı
function CompactMetricRow({ label, valueRaw }: { label: string; valueRaw?: number | null }) {
  if (valueRaw == null) {
    return (
      <div className="flex items-center gap-3 py-1.5 border-b border-[var(--ota-border)]/50 last:border-0">
        <div className="w-28 text-[10px] font-bold text-[var(--ota-text-muted)] uppercase tracking-wider truncate" title={label}>
          {label}
        </div>
        <div className="flex-1 text-[10px] font-medium text-[var(--ota-text-muted)] italic">
          Hesaplanıyor...
        </div>
        <div className="w-10 text-right text-xs font-mono font-medium text-[var(--ota-text-muted)]">
          -
        </div>
      </div>
    );
  }
  const pctStr = mapConfidenceToPercent(valueRaw);
  const numValue = parseInt(pctStr.replace("%", ""), 10) || 0;
  
  const isLow = numValue < 30;

  // Düşük değerler için progress bar veya hata rengi yerine nötr metin (Örn: Retrieval Confidence: %5)
  if (isLow) {
    return (
      <div className="flex items-center justify-between py-1.5 border-b border-[var(--ota-border)]/50 last:border-0">
        <div className="text-[10px] font-bold text-[var(--ota-text-muted)] uppercase tracking-wider truncate" title={`${label} Confidence`}>
          {label} Confidence
        </div>
        <div className="text-[10px] font-mono font-medium text-[var(--ota-text-muted)]">
          {pctStr}
        </div>
      </div>
    );
  }

  // Yüksek/Orta değerler için progress bar
  let barColor = "bg-[var(--ota-gold)]";
  let status = "Orta";
  let statusColor = "text-[var(--ota-gold)]";
  
  if (numValue >= 80) {
    barColor = "bg-[var(--ota-success)]";
    status = "Yüksek";
    statusColor = "text-[var(--ota-success)]";
  }

  return (
    <div className="flex items-center gap-3 py-1.5 border-b border-[var(--ota-border)]/50 last:border-0">
      <div className="w-28 text-[10px] font-bold text-[var(--ota-text-2)] uppercase tracking-wider truncate" title={label}>
        {label}
      </div>
      <div className="flex-1 bg-[var(--ota-bg)] h-1.5 rounded-full overflow-hidden border border-[var(--ota-border)]/50">
        <div className={`h-full ${barColor} transition-all duration-1000 ease-out`} style={{ width: `${numValue}%` }}></div>
      </div>
      <div className={`w-10 text-right text-xs font-mono font-medium ${statusColor}`}>
        {pctStr}
      </div>
      <div className={`w-14 text-right text-[9px] uppercase tracking-wider font-semibold ${statusColor}`}>
        {status}
      </div>
    </div>
  );
}

// Kompakt motor bilgisi satırı
function CompactEngineInfoRow({ label, value }: { label: string; value?: string | boolean | null }) {
  if (value == null || value === "") return null;
  const displayVal = typeof value === "boolean" ? (value ? "Aktif" : "Pasif") : value;
  
  return (
    <div className="flex justify-between items-center py-1.5 border-b border-[var(--ota-border)]/50 last:border-0">
      <span className="text-[10px] font-semibold text-[var(--ota-text-muted)] uppercase tracking-wider">{label}</span>
      <span className="text-xs font-medium text-[var(--ota-text)] truncate max-w-[200px]" title={String(displayVal)}>{displayVal}</span>
    </div>
  );
}

export default function TechnicalDetailsTab({ result }: Props) {
  // Model extract helpers
  const extractModel = (keywords: string[]) => {
    const found = result.models_used?.find(m => keywords.some(k => m.toLowerCase().includes(k)));
    return found || "Belirtilmedi";
  };

  const nerModel = extractModel(["ner", "entity", "bert"]);
  const embeddingModel = extractModel(["embed", "bge", "minilm"]);
  const vectorDb = extractModel(["qdrant", "chroma", "pinecone", "milvus"]);

  type AINoteCategory = "Uyarı" | "Belirsizlik" | "Tespit" | "Model Notu" | "Kaynak Notu";

  const aiNotes: Array<{ category: AINoteCategory; text: string }> = [
    ...(result.image_processing?.warnings || []).map(text => ({ category: "Uyarı" as AINoteCategory, text })),
    ...(result.warnings || []).map(text => ({ category: "Uyarı" as AINoteCategory, text })),
    ...(result.uncertainties || []).map(text => ({ category: "Belirsizlik" as AINoteCategory, text })),
  ];

  return (
    <div className="flex flex-col h-full bg-[var(--ota-bg)]">
      
      {/* Header */}
      <div className="p-4 border-b border-[var(--ota-border)] shrink-0">
        <h3 className="text-base font-bold text-[var(--ota-text)] mb-1">Teknik Detay — Engineering View</h3>
        <p className="text-xs text-[var(--ota-text-muted)]">
          İleri düzey sistem analizi, yapay zeka puanları ve motor yapılandırmaları.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 flex flex-col gap-4">
        
        {/* ANA METRİKLER & Puanlar */}
        <section className="bg-[var(--ota-bg-2)]/50 p-4 rounded-xl border border-[var(--ota-border)] shadow-sm">
          <h4 className="text-xs font-semibold text-[var(--ota-gold)] mb-3 flex items-center gap-1.5 uppercase tracking-wider">
            <span><Brain className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> Yapay Zeka Puanları
          </h4>
          <div className="flex flex-col">
            <CompactMetricRow label="OCR" valueRaw={result.confidence?.ocr} />
            <CompactMetricRow label="Transliteration" valueRaw={result.confidence?.transliteration} />
            <CompactMetricRow label="Modern Turkish" valueRaw={result.confidence?.modern_turkish} />
            <CompactMetricRow label="Evidence" valueRaw={result.confidence?.evidence_coverage} />
            <CompactMetricRow label="Retrieval" valueRaw={result.confidence?.retrieval_strength} />
          </div>
        </section>

        {/* MOTOR BİLGİLERİ */}
        <section className="bg-[var(--ota-bg-2)]/50 p-4 rounded-xl border border-[var(--ota-border)] shadow-sm">
          <h4 className="text-xs font-semibold text-[var(--ota-iznik-turquoise)] mb-3 flex items-center gap-1.5 uppercase tracking-wider">
            <span><Settings className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> Motor Bilgileri
          </h4>
          <div className="flex flex-col">
            <CompactEngineInfoRow label="OCR Engine" value={result.ocr.engine} />
            <CompactEngineInfoRow label="Translation Provider" value={result.modern_turkish.provider} />
            <CompactEngineInfoRow label="NER" value={nerModel} />
            <CompactEngineInfoRow label="Embedding" value={embeddingModel} />
            <CompactEngineInfoRow label="Vector DB" value={vectorDb} />
            <CompactEngineInfoRow label="Fallback" value={result.ocr.fallback_used} />
            <CompactEngineInfoRow label="Doğrulama" value={result.verification_status === "nvidia_nim" ? "NVIDIA NIM Onaylı" : "Yerel"} />
            {result.models_used && result.models_used.length > 0 && (
              <CompactEngineInfoRow label="Kullanılan Modeller" value={result.models_used.join(", ")} />
            )}
          </div>
        </section>

        {/* AI NOTLARI */}
        <section className="bg-[var(--ota-bg-2)]/50 p-4 rounded-xl border border-[var(--ota-border)] shadow-sm">
          <h4 className="text-xs font-semibold text-[var(--ota-text)] mb-3 flex items-center gap-1.5 uppercase tracking-wider">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--ota-gold)]">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
            </svg>
            AI Notları
          </h4>
          
          {aiNotes.length > 0 ? (
            <div className="flex flex-col gap-2">
              {aiNotes.map((note, idx) => (
                <div key={idx} className={`flex items-start gap-3 p-3 rounded-lg border ${
                  note.category === "Uyarı" ? "bg-[var(--ota-ruby)]/10 border-[var(--ota-ruby)]/20 text-[var(--ota-ruby)]" :
                  note.category === "Belirsizlik" ? "bg-[var(--ota-gold)]/10 border-[var(--ota-gold)]/20 text-[var(--ota-gold)]" :
                  note.category === "Tespit" ? "bg-[var(--ota-success)]/10 border-[var(--ota-success)]/20 text-[var(--ota-success)]" :
                  note.category === "Model Notu" ? "bg-[var(--ota-iznik-turquoise)]/10 border-[var(--ota-iznik-turquoise)]/20 text-[var(--ota-iznik-turquoise)]" :
                  note.category === "Kaynak Notu" ? "bg-[var(--ota-sage)]/10 border-[var(--ota-sage)]/20 text-[var(--ota-sage)]" :
                  "bg-[var(--ota-bg-2)] border-[var(--ota-border)] text-[var(--ota-text)]"
                }`}>
                  <div className="shrink-0 mt-0.5">
                    {note.category === "Uyarı" && (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
                    )}
                    {note.category === "Belirsizlik" && (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>
                    )}
                    {note.category === "Tespit" && (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>
                    )}
                    {note.category === "Model Notu" && (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 7v10"/><path d="M11 7v10"/><path d="M15 7v10"/></svg>
                    )}
                    {note.category === "Kaynak Notu" && (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                    )}
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider opacity-80">{note.category}</span>
                    <span className="text-xs font-medium">{note.text}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-4 p-4 bg-[var(--ota-bg)]/50 border border-[var(--ota-border)] border-dashed rounded-lg">
              <div className="w-10 h-10 rounded-full bg-[var(--ota-bg-2)] flex items-center justify-center border border-[var(--ota-border)]/50 shrink-0 shadow-sm">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--ota-text-muted)]">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="15" x2="15" y2="15"/>
                </svg>
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="text-sm font-semibold text-[var(--ota-text-muted)]">Bu analiz için ek AI notu bulunmuyor.</span>
                <p className="text-[10px] text-[var(--ota-text-muted)]/70">
                  Tespit, uyarı veya model belirsizlikleri oluştuğunda burada listelenir.
                </p>
              </div>
            </div>
          )}
        </section>

        {/* MODEL KARŞILAŞTIRMASI */}
        <section className="bg-[var(--ota-bg-2)]/50 p-4 rounded-xl border border-[var(--ota-border)] shadow-sm">
          <h4 className="text-xs font-semibold text-[var(--ota-sage)] mb-3 flex items-center gap-1.5 uppercase tracking-wider">
            <span><BarChart2 className="w-4 h-4 mr-1 inline-block" /></span> Model Karşılaştırması
          </h4>
          
          <div className="flex flex-col items-center justify-center p-4 bg-[var(--ota-bg)]/50 border border-[var(--ota-border)] border-dashed rounded-lg text-center">
            <span className="text-sm font-semibold text-[var(--ota-text-muted)]">Bu belge için model karşılaştırması bulunmuyor.</span>
            <p className="text-[10px] text-[var(--ota-text-muted)]/70 mt-1.5 max-w-[250px]">
              Model karşılaştırması yalnızca birden fazla OCR/model sonucu mevcut olduğunda gösterilir.
            </p>
          </div>
        </section>

      </div>
    </div>
  );
}
