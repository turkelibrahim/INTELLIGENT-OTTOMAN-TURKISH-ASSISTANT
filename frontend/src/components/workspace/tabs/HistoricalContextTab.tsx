"use client";

import { useMemo } from "react";
import type { FullDocumentAnalysisResponse } from "@/lib/api";
import { isLowOcrConfidence, mapConfidenceToPercent } from "@/lib/viewModel";
import EmptyState from "@/components/ui/EmptyState";
import StructuredHistoricalAnalysis from "../StructuredHistoricalAnalysis";
import { AlertTriangle } from 'lucide-react';


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

export default function HistoricalContextTab({ result, onGoToOcr }: Props) {
  const analysis = result.historical_analysis || {};
  const ocrConfidence = result.confidence?.ocr;
  const isLowOcr = isLowOcrConfidence(ocrConfidence);
  const pct = mapConfidenceToPercent(ocrConfidence);
  const context = analysis.historical_context ?? "";
  const hasContext = isUsefulContext(context);

  const externalSourceCount = useMemo(() => {
    return (result.evidence?.historical_external_evidence ?? []).filter((e) => e.verified === true).length;
  }, [result]);

  // If OCR is too low to trust historical analysis
  if (isLowOcr && !hasContext) {
    return (
      <div className="ota-historical-tab">
        <div className="ota-low-confidence-warning">
          <div className="ota-warning-icon"><AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" /></div>
          <h3>Tarihsel analiz sınırlandırıldı</h3>
          <p>
            Belge metni henüz güvenilir tarihsel çıkarım için yeterli doğrulukta
            çözümlenmedi.{pct ? ` OCR güveni: ${pct}.` : ""}
          </p>
          <p className="ota-warning-suggestion">
            OCR metnini inceleyerek ya da düzelterek sonucu iyileştirebilirsiniz.
          </p>
          {onGoToOcr && (
            <button type="button" className="ota-btn-secondary" onClick={onGoToOcr}>
              OCR Metnini İncele
            </button>
          )}
        </div>
      </div>
    );
  }

  if (!hasContext && externalSourceCount === 0) {
    return (
      <EmptyState
        title="Tarihsel bilgi bulunamadı"
        description="Bu belge için güvenilir tarihsel bağlam oluşturulamadı. Belge metni iyileştirildiğinde tarihsel analiz yeniden çalıştırılabilir."
      />
    );
  }

  return (
    <div className="ota-historical-tab">
      {/* Key Historical Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {analysis.possible_period && analysis.possible_period.toLowerCase() !== "tespit edilemedi" && (
          <div className="bg-[var(--ota-bg-2)]/50 p-4 rounded-xl border border-[var(--ota-border)]">
            <span className="text-[10px] uppercase text-[var(--ota-text-muted)] font-bold">Dönem Tahmini</span>
            <div className="text-sm font-medium text-[var(--ota-text)] mt-1">{analysis.possible_period}</div>
          </div>
        )}
        {analysis.possible_sultan_period && analysis.possible_sultan_period.toLowerCase() !== "tespit edilemedi" && (
          <div className="bg-[var(--ota-bg-2)]/50 p-4 rounded-xl border border-[var(--ota-border)]">
            <span className="text-[10px] uppercase text-[var(--ota-text-muted)] font-bold">Padişah Dönemi</span>
            <div className="text-sm font-medium text-[var(--ota-text)] mt-1">{analysis.possible_sultan_period}</div>
          </div>
        )}
        {analysis.document_type && analysis.document_type.toLowerCase() !== "tespit edilemedi" && (
          <div className="bg-[var(--ota-bg-2)]/50 p-4 rounded-xl border border-[var(--ota-border)]">
            <span className="text-[10px] uppercase text-[var(--ota-text-muted)] font-bold">Belge Türü</span>
            <div className="text-sm font-medium text-[var(--ota-text)] mt-1">{analysis.document_type}</div>
          </div>
        )}
        {(analysis.possible_author && analysis.possible_author.toLowerCase() !== "tespit edilemedi") ? (
          <div className="bg-[var(--ota-bg-2)]/50 p-4 rounded-xl border border-[var(--ota-border)]">
            <span className="text-[10px] uppercase text-[var(--ota-text-muted)] font-bold">Muhtemel Yazar</span>
            <div className="text-sm font-medium text-[var(--ota-text)] mt-1">{analysis.possible_author}</div>
          </div>
        ) : (analysis.possible_institution && analysis.possible_institution.toLowerCase() !== "tespit edilemedi") ? (
          <div className="bg-[var(--ota-bg-2)]/50 p-4 rounded-xl border border-[var(--ota-border)]">
            <span className="text-[10px] uppercase text-[var(--ota-text-muted)] font-bold">Muhtemel Kurum</span>
            <div className="text-sm font-medium text-[var(--ota-text)] mt-1">{analysis.possible_institution}</div>
          </div>
        ) : null}
      </div>

      {/* Context paragraphs via structured component */}
      {hasContext && (
        <StructuredHistoricalAnalysis rawText={context} />
      )}

      {/* Evidence List */}
      {result.evidence?.historical_external_evidence && result.evidence.historical_external_evidence.length > 0 && (
        <div className="mt-8 border-t border-[var(--ota-border)] pt-6">
          <h4 className="text-xs font-bold text-[var(--ota-gold)] mb-4 uppercase tracking-wider">Destekleyici Harici Kaynaklar</h4>
          <div className="space-y-3">
            {result.evidence.historical_external_evidence.map((ev, idx) => (
              <div key={idx} className="bg-[var(--ota-bg-2)]/50 p-4 rounded-xl border border-[var(--ota-border)] shadow-sm">
                <div className="flex justify-between items-start mb-2 gap-4">
                  <span className="font-semibold text-[var(--ota-text)] text-sm">{String(ev.title || ev.citation || `Kaynak ${idx + 1}`)}</span>
                  {ev.verified === true && <span className="text-[10px] font-bold text-[var(--ota-success)] uppercase border border-[var(--ota-success)]/30 bg-[var(--ota-success)]/10 px-2 py-0.5 rounded shrink-0">Doğrulandı</span>}
                </div>
                {Boolean(ev.evidence_text || ev.text) && <p className="text-xs text-[var(--ota-text-2)] leading-relaxed">{String(ev.evidence_text || ev.text)}</p>}
                {Boolean(ev.url) && (
                  <a href={String(ev.url)} target="_blank" rel="noopener noreferrer" className="text-[10px] font-medium text-[var(--ota-iznik-turquoise)] hover:underline mt-2 inline-block">
                    Kaynağa Git ↗
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stats row */}
      <div className="ota-historical-stats">
        {externalSourceCount > 0 && (
          <div className="ota-historical-stat">
            <span className="ota-stat-value">{externalSourceCount}</span>
            <span className="ota-stat-label">Doğrulanmış Kaynak</span>
          </div>
        )}
        {typeof result.confidence?.combined === "number" && (
          <div className="ota-historical-stat">
            <span className="ota-stat-value">{mapConfidenceToPercent(result.confidence.combined)}</span>
            <span className="ota-stat-label">Analiz Güveni</span>
          </div>
        )}
        {analysis.provisional && (
          <div className="ota-historical-stat">
            <span className="ota-stat-badge warning">Geçici Sonuç</span>
          </div>
        )}
      </div>

      {/* Low OCR notice (but context exists) */}
      {isLowOcr && hasContext && (
        <div className="ota-historical-notice">
          <span><AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>
          <span>OCR güveni {pct} — bu tarihsel bağlam kısmen belirsiz olabilir.</span>
        </div>
      )}
    </div>
  );
}
