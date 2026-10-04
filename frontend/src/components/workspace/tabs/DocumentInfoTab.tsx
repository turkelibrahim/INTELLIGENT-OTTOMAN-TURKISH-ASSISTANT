"use client";

import { useState, useMemo } from "react";
import type { FullDocumentAnalysisResponse } from "@/lib/api";
import { mapDocumentClaims } from "@/lib/viewModel";
import StatusBadge from "@/components/ui/StatusBadge";
import ConfidenceBadge from "@/components/ui/ConfidenceBadge";
import EmptyState from "@/components/ui/EmptyState";

interface Props {
  result: FullDocumentAnalysisResponse;
}

// Priority field order for display
const PRIORITY_FIELDS = [
  "document_type", "date_raw", "date_normalized",
  "author/sender", "possible_author",
  "recipient", "place", "possible_institution", "institutions",
  "subject/topic", "summary",
  "seal_presence", "signature_presence", "tughra_presence",
];

export default function DocumentInfoTab({ result }: Props) {
  const [showAll, setShowAll] = useState(false);

  const claims = useMemo(() => {
    const raw = (result.evidence?.document_claims ?? []) as Array<Record<string, unknown>>;
    return mapDocumentClaims(raw);
  }, [result]);

  const detected = useMemo(() => claims.filter((c) => c.isDetected), [claims]);
  const notDetected = useMemo(() => claims.filter((c) => !c.isDetected), [claims]);

  // Also add historical analysis known fields
  const historicalFields = useMemo(() => {
    const ha = result.historical_analysis || {};
    const additions: Array<{ label: string; value: string }> = [];
    if (ha.document_type && ha.document_type !== "tespit edilemedi") {
      additions.push({ label: "Belge Türü", value: ha.document_type });
    }
    if (ha.possible_period && ha.possible_period !== "tespit edilemedi") {
      additions.push({ label: "Tahmini Dönem", value: ha.possible_period });
    }
    if (ha.possible_sultan_period) {
      additions.push({ label: "Tahmini Padişah Dönemi", value: ha.possible_sultan_period });
    }
    return additions;
  }, [result]);

  if (claims.length === 0 && historicalFields.length === 0) {
    return (
      <EmptyState
        title="Belge bilgisi bulunamadı"
        description="Belge içeriği incelendi, ancak yapılandırılmış bilgi çıkarılamadı."
      />
    );
  }

  // Sort by priority
  const sortedDetected = [...detected].sort((a, b) => {
    const ai = PRIORITY_FIELDS.indexOf(a.field);
    const bi = PRIORITY_FIELDS.indexOf(b.field);
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });

  return (
    <div className="ota-doc-info-tab">
      {/* Detected claims table */}
      {sortedDetected.length > 0 && (
        <div className="ota-info-grid">
          {sortedDetected.map((claim, idx) => (
            <div key={`${claim.field}-${idx}`} className="ota-info-row">
              <span className="ota-info-label">{claim.label}</span>
              <span className="ota-info-value">{claim.value}</span>
              <div className="ota-info-badges">
                <StatusBadge
                  variant={claim.statusVariant}
                  label={claim.statusLabel}
                  small
                />
                {claim.confidence != null && (
                  <ConfidenceBadge value={claim.confidence} small />
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Historical analysis fields (inferred) */}
      {historicalFields.length > 0 && (
        <div className="ota-info-inferred-section">
          <span className="ota-info-section-label">Çıkarım (Harici Kaynak Desteğiyle)</span>
          <div className="ota-info-grid">
            {historicalFields.map((f) => (
              <div key={f.label} className="ota-info-row">
                <span className="ota-info-label">{f.label}</span>
                <span className="ota-info-value">{f.value}</span>
                <div className="ota-info-badges">
                  <StatusBadge variant="neutral" label="Muhtemel" small />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Not detected summary */}
      {notDetected.length > 0 && (
        <div className="ota-info-missing-section">
          {!showAll ? (
            <div className="ota-info-missing-summary">
              <span className="ota-info-missing-text">
                {notDetected.length} belge bilgisi güvenilir şekilde tespit edilemedi.
              </span>
              <button
                type="button"
                className="ota-btn-ghost small"
                onClick={() => setShowAll(true)}
              >
                Tüm Alanları Gör
              </button>
            </div>
          ) : (
            <>
              <div className="ota-info-grid muted">
                {notDetected.map((claim, idx) => (
                  <div key={`${claim.field}-${idx}`} className="ota-info-row missing">
                    <span className="ota-info-label">{claim.label}</span>
                    <span className="ota-info-value muted">—</span>
                    <div className="ota-info-badges">
                      <StatusBadge variant="neutral" label="Tespit Edilemedi" small />
                    </div>
                  </div>
                ))}
              </div>
              <button
                type="button"
                className="ota-btn-ghost small"
                onClick={() => setShowAll(false)}
              >
                Gizle
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
