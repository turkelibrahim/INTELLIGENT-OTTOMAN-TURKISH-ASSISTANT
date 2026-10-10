"use client";

import { useMemo } from "react";
import type { FullDocumentAnalysisResponse } from "@/lib/api";
import { isLowOcrConfidence, mapConfidenceToPercent, translateInternalValue } from "@/lib/viewModel";
import StructuredHistoricalAnalysis from "./StructuredHistoricalAnalysis";
import { AlertTriangle, ScrollText } from 'lucide-react';


function renderMetaCard(label: string, value: string | undefined | null) {
  let cleanValue = translateInternalValue(value);
  const isMissing = cleanValue === "Tespit Edilemedi" || cleanValue.toLowerCase().includes("tespit edilemedi") || cleanValue.toLowerCase().includes("tespit yok") || cleanValue.toLowerCase().includes("bilinmiyor") || cleanValue.toLowerCase() === "yok";
  const isProbable = cleanValue.toLowerCase().includes("muhtemel") || cleanValue.toLowerCase().includes("tahmini") || cleanValue.toLowerCase().includes("belirsiz");

  const badgeStr = isMissing ? "Tespit Yok" : isProbable ? "Muhtemel" : "Kesin";
  const badgeColor = isMissing ? "bg-[var(--ota-ruby)]/10 text-[var(--ota-ruby)] border-[var(--ota-ruby)]/20" : 
                   isProbable ? "bg-[var(--ota-gold)]/10 text-[var(--ota-gold)] border-[var(--ota-gold)]/20" : 
                   "bg-[var(--ota-success)]/10 text-[var(--ota-success)] border-[var(--ota-success)]/20";
  
  if (isProbable) {
    cleanValue = cleanValue.replace(/muhtemel|tahmini/i, "").trim();
  }
  if (!cleanValue || isMissing) cleanValue = "Tespit Yok";

  return (
    <div className="bg-[var(--ota-bg-2)]/50 p-2.5 rounded-lg border border-[var(--ota-border)] flex flex-col gap-1.5 min-w-0">
       <div className="flex items-center justify-between gap-2">
         <span className="text-[10px] text-[var(--ota-text-muted)] uppercase tracking-wider">{label}</span>
         <span className={`text-[9px] px-1.5 py-0.5 rounded border font-medium ${badgeColor}`}>
           {badgeStr}
         </span>
       </div>
       <span className={`text-xs font-medium truncate ${isMissing ? 'text-[var(--ota-text-muted)] italic' : 'text-[var(--ota-text)]'}`} title={cleanValue}>
         {cleanValue}
       </span>
    </div>
  );
}

interface Props {
  result: FullDocumentAnalysisResponse;
  onGoToOcr?: () => void;
}

function isUsefulContext(text: string): boolean {
  if (!text || text.trim().length < 10) return false;
  const lower = text.toLowerCase().trim();
  return lower !== "tespit edilemedi" &&
         lower !== "not_detected" &&
         lower !== "unknown" &&
         lower !== "n/a";
}

export default function HistoricalSidebar({ result, onGoToOcr }: Props) {
  const analysis = result.historical_analysis || {};
  const ocrConfidence = result.confidence?.ocr;
  const isLowOcr = isLowOcrConfidence(ocrConfidence);
  const pct = mapConfidenceToPercent(ocrConfidence);
  const context = analysis.historical_context ?? "";
  const hasContext = isUsefulContext(context);

  const externalSourceCount = useMemo(() => {
    return (result.evidence?.historical_external_evidence ?? []).filter((e) => e.verified === true).length;
  }, [result]);

  const getEntitiesStr = (arr: unknown) => {
    if (!Array.isArray(arr)) return undefined;
    const vals = arr.map((a: Record<string, unknown>) => (a.value || a.normalized_value || a.text) as string | undefined)
      .filter((v): v is string => typeof v === "string" && !v.toLowerCase().includes("tespit edilemedi"));
    return vals.length > 0 ? vals.join(", ") : undefined;
  };

  const cografya = getEntitiesStr(result.entities?.places);
  const kurumlar = getEntitiesStr(result.entities?.institutions);
  const siyasiBaglam = (analysis as Record<string, unknown>).political_context as string | undefined;
  const ilgiliOlaylar = getEntitiesStr((analysis as Record<string, unknown>).events) || (analysis as Record<string, unknown>).related_events as string | undefined;
  const tarihselKonular = Array.isArray((analysis as Record<string, unknown>).historical_topics) ? ((analysis as Record<string, unknown>).historical_topics as string[]).join(", ") : undefined;

  return (
    <article className="ota-panel" aria-label="Tarihsel Analiz">
      {/* Header */}
      <header className="ota-panel-header">
        <div>
          <h2 className="ota-panel-title">Tarihsel Analiz</h2>
          <span className="ota-panel-subtitle">Bağlam ve Dönem</span>
        </div>
      </header>

      {/* Body */}
      <div className="ota-panel-body">
        
        {isLowOcr && !hasContext ? (
          <div className="bg-[var(--ota-ruby)]/10 border border-[var(--ota-ruby)]/20 rounded-xl p-4 text-center">
            <div className="text-2xl mb-2"><AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" /></div>
            <h3 className="font-semibold text-[var(--ota-ruby)] mb-1 text-sm">Tarihsel analiz sınırlandırıldı</h3>
            <p className="text-xs text-[var(--ota-text-muted)] mb-3">
              Belge metni henüz güvenilir tarihsel çıkarım için yeterli doğrulukta
              çözümlenmedi.{pct ? ` OCR güveni: ${pct}.` : ""}
            </p>
            {onGoToOcr && (
              <button type="button" className="text-xs font-semibold px-3 py-1.5 bg-[var(--ota-ruby)]/20 text-[var(--ota-ruby)] hover:bg-[var(--ota-ruby)]/30 rounded-md transition-colors" onClick={onGoToOcr}>
                OCR Metnini İncele
              </button>
            )}
          </div>
        ) : !hasContext && externalSourceCount === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center opacity-70 mt-10">
            <span className="text-4xl mb-3"><ScrollText className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>
            <h3 className="font-medium text-[var(--ota-text)] mb-1">Tarihsel bağlam henüz oluşturulmadı</h3>
            <p className="text-xs text-[var(--ota-text-muted)] max-w-[200px]">
              Bu belge için genişletilmiş tarihsel bağlam verisi mevcut değil.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-5">
            {/* Context structured render */}
            {hasContext && (
              <StructuredHistoricalAnalysis rawText={context} />
            )}

            {/* Low OCR notice */}
            {isLowOcr && hasContext && (
              <div className="flex items-start gap-2 bg-[var(--ota-gold-dim)] text-[var(--ota-gold)]/80 p-3 rounded-lg text-xs border border-[var(--ota-border)]">
                <span><AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>
                <span>OCR güveni {pct} — bu tarihsel bağlam kısmen belirsiz olabilir.</span>
              </div>
            )}

            {/* Stats row */}
            <div className="grid grid-cols-2 gap-3 mt-4 border-t border-[var(--ota-border)] pt-4">
              {externalSourceCount > 0 && (
                <div className="bg-[var(--ota-bg-2)]/50 p-3 rounded-lg border border-[var(--ota-border)] text-center flex flex-col items-center justify-center">
                  <span className="text-xl font-bold text-[var(--ota-iznik-turquoise)] mb-1">{externalSourceCount}</span>
                  <span className="text-[10px] text-[var(--ota-text-muted)] uppercase tracking-wider">Doğrulanmış Kaynak</span>
                </div>
              )}
              {typeof result.confidence?.combined === "number" && (
                <div className="bg-[var(--ota-bg-2)]/50 p-3 rounded-lg border border-[var(--ota-border)] text-center flex flex-col items-center justify-center">
                  <span className="text-xl font-bold text-[var(--ota-gold)] mb-1">{mapConfidenceToPercent(result.confidence.combined)}</span>
                  <span className="text-[10px] text-[var(--ota-text-muted)] uppercase tracking-wider">Analiz Güveni</span>
                </div>
              )}
              {analysis.provisional && (
                <div className="col-span-2 bg-[var(--ota-gold-dim)] p-2 rounded-lg border border-[var(--ota-border)] text-center">
                  <span className="text-xs font-medium text-[var(--ota-gold)] tracking-wide uppercase">Geçici Sonuç</span>
                </div>
              )}
            </div>
            
            {/* Meta bilgileri */}
            <div className="mt-2 flex flex-col gap-3">
               <h4 className="text-[10px] font-bold uppercase tracking-wider text-[var(--ota-text-muted)] px-1">Belge Künyesi</h4>
               <div className="grid grid-cols-2 gap-2">
                 {renderMetaCard("Dönem", analysis.possible_period)}
                 {renderMetaCard("Padişah", analysis.possible_sultan_period)}
                 {renderMetaCard("Belge Türü", analysis.document_type)}
                 {cografya && renderMetaCard("Coğrafya", cografya)}
                 {siyasiBaglam && renderMetaCard("Siyasi Bağlam", siyasiBaglam)}
                 {kurumlar && renderMetaCard("Kurumlar", kurumlar)}
                 {ilgiliOlaylar && renderMetaCard("İlgili Olaylar", ilgiliOlaylar)}
                 {tarihselKonular && renderMetaCard("Tarihsel Konular", tarihselKonular)}
                 {renderMetaCard("Dil", "Osmanlıca")}
               </div>
               
               {/* Eksik Bilgi Banner */}
               {(!analysis.possible_period || !analysis.possible_sultan_period || !analysis.document_type) && (
                 <div className="flex items-start gap-2 p-2.5 bg-[var(--ota-ruby)]/10 border border-[var(--ota-ruby)]/20 rounded-lg mt-1">
                   <span className="text-[10px] leading-relaxed text-[var(--ota-ruby)]/90 font-medium">
                     Bazı belge bilgileri (künye) güvenilir şekilde tespit edilemedi.
                   </span>
                 </div>
               )}
               
               {/* Ekstra veriler: belge tipi alt tür vs varsa */}
               {!!(analysis as unknown as Record<string, string[]>).themes?.length && (
                 <div className="flex flex-col gap-2 mt-2">
                   <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--ota-text-muted)] px-1">Temalar</span>
                   <div className="flex flex-wrap gap-1.5">
                     {(analysis as unknown as Record<string, string[]>).themes.map((theme: string, i: number) => (
                       <span key={i} className="px-2 py-1 bg-[var(--ota-bg-2)] border border-[var(--ota-border)] rounded-md text-[var(--ota-text-2)] text-xs">{theme}</span>
                     ))}
                   </div>
                 </div>
               )}
            </div>
          </div>
        )}
      </div>
    </article>
  );
}
