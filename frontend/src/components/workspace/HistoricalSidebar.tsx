"use client";

import { useMemo } from "react";
import type { FullDocumentAnalysisResponse } from "@/lib/api";
import { isLowOcrConfidence, mapConfidenceToPercent } from "@/lib/viewModel";

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

function splitParagraphs(text: string): string[] {
  return text.split(/\n+/).map((l) => l.trim()).filter(Boolean);
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

  return (
    <aside className="w-[340px] flex-shrink-0 flex flex-col h-[560px] max-h-[560px] glass-panel border border-amber-500/10 rounded-2xl overflow-hidden shadow-lg ml-4 hidden xl:flex">
      {/* Header */}
      <div className="bg-slate-900/80 px-5 py-4 border-b border-amber-500/10 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center border border-amber-500/30 text-amber-500">
          🏛️
        </div>
        <div>
          <h2 className="font-semibold text-slate-100 text-sm">Tarihsel Analiz</h2>
          <span className="text-[10px] text-amber-400 font-medium tracking-wide uppercase">Bağlam ve Dönem</span>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 min-h-0 overflow-y-auto p-5 custom-scrollbar text-sm text-slate-300">
        
        {isLowOcr && !hasContext ? (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-center">
            <div className="text-2xl mb-2">⚠</div>
            <h3 className="font-semibold text-red-400 mb-1 text-sm">Tarihsel analiz sınırlandırıldı</h3>
            <p className="text-xs text-slate-400 mb-3">
              Belge metni henüz güvenilir tarihsel çıkarım için yeterli doğrulukta
              çözümlenmedi.{pct ? ` OCR güveni: ${pct}.` : ""}
            </p>
            {onGoToOcr && (
              <button type="button" className="text-xs font-semibold px-3 py-1.5 bg-red-500/20 text-red-300 hover:bg-red-500/30 rounded-md transition-colors" onClick={onGoToOcr}>
                OCR Metnini İncele
              </button>
            )}
          </div>
        ) : !hasContext && externalSourceCount === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center opacity-70 mt-10">
            <span className="text-4xl mb-3">📜</span>
            <h3 className="font-medium text-slate-200 mb-1">Tarihsel bilgi bulunamadı</h3>
            <p className="text-xs text-slate-400 max-w-[200px]">
              Bu belge için güvenilir tarihsel bağlam oluşturulamadı.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-5">
            {/* Context paragraphs */}
            {hasContext && (
              <div className="flex flex-col gap-3 leading-relaxed">
                {splitParagraphs(context).map((p, i) => (
                  <p key={i} className="text-justify border-l-2 border-amber-500/30 pl-3 py-0.5">{p}</p>
                ))}
              </div>
            )}

            {/* Low OCR notice */}
            {isLowOcr && hasContext && (
              <div className="flex items-start gap-2 bg-amber-500/10 text-amber-300/80 p-3 rounded-lg text-xs">
                <span>⚠</span>
                <span>OCR güveni {pct} — bu tarihsel bağlam kısmen belirsiz olabilir.</span>
              </div>
            )}

            {/* Stats row */}
            <div className="grid grid-cols-2 gap-3 mt-4 border-t border-slate-700/50 pt-4">
              {externalSourceCount > 0 && (
                <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-800 text-center flex flex-col items-center justify-center">
                  <span className="text-xl font-bold text-emerald-400 mb-1">{externalSourceCount}</span>
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">Doğrulanmış Kaynak</span>
                </div>
              )}
              {typeof result.confidence?.combined === "number" && (
                <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-800 text-center flex flex-col items-center justify-center">
                  <span className="text-xl font-bold text-amber-500 mb-1">{mapConfidenceToPercent(result.confidence.combined)}</span>
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">Analiz Güveni</span>
                </div>
              )}
              {analysis.provisional && (
                <div className="col-span-2 bg-amber-500/10 p-2 rounded-lg border border-amber-500/20 text-center">
                  <span className="text-xs font-medium text-amber-400 tracking-wide uppercase">Geçici Sonuç</span>
                </div>
              )}
            </div>
            
            {/* Meta bilgileri */}
            <div className="mt-4 flex flex-col gap-2">
               {analysis.possible_period && (
                 <div className="flex justify-between items-center text-xs border-b border-slate-800 pb-2">
                   <span className="text-slate-500">Dönem</span>
                   <span className="text-slate-300 font-medium text-right max-w-[150px]">{analysis.possible_period}</span>
                 </div>
               )}
               {analysis.possible_sultan_period && (
                 <div className="flex justify-between items-center text-xs border-b border-slate-800 pb-2">
                   <span className="text-slate-500">Padişah</span>
                   <span className="text-slate-300 font-medium text-right max-w-[150px]">{analysis.possible_sultan_period}</span>
                 </div>
               )}
               {analysis.document_type && (
                 <div className="flex justify-between items-center text-xs border-b border-slate-800 pb-2">
                   <span className="text-slate-500">Tür</span>
                   <span className="text-slate-300 font-medium text-right max-w-[150px]">{analysis.document_type}</span>
                 </div>
               )}
               
               {/* Ekstra veriler: belge tipi alt tür vs varsa */}
               {!!(analysis as unknown as Record<string, string[]>).themes?.length && (
                 <div className="flex flex-col gap-1 text-xs pt-2">
                   <span className="text-slate-500">Temalar</span>
                   <div className="flex flex-wrap gap-1">
                     {(analysis as unknown as Record<string, string[]>).themes.map((theme: string, i: number) => (
                       <span key={i} className="px-2 py-1 bg-slate-800 rounded-md text-slate-300">{theme}</span>
                     ))}
                   </div>
                 </div>
               )}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
