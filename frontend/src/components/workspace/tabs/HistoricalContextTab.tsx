"use client";

import { useMemo } from "react";
import type { FullDocumentAnalysisResponse } from "@/lib/api";
import { isLowOcrConfidence, mapConfidenceToPercent } from "@/lib/viewModel";
import EmptyState from "@/components/ui/EmptyState";

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
          <div className="ota-warning-icon">⚠</div>
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

  const paragraphs = hasContext ? splitParagraphs(context) : [];

  return (
    <div className="ota-historical-tab">
      {/* Context paragraphs */}
      {paragraphs.length > 0 && (
        <div className="ota-historical-context">
          {paragraphs.map((p, i) => (
            <p key={i} className="ota-historical-paragraph">{p}</p>
          ))}
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
          <span>⚠</span>
          <span>OCR güveni {pct} — bu tarihsel bağlam kısmen belirsiz olabilir.</span>
        </div>
      )}
    </div>
  );
}
