"use client";

import { useState, useMemo } from "react";
import type { FullDocumentAnalysisResponse } from "@/lib/api";
import { mapDocumentClaims, translateInternalValue } from "@/lib/viewModel";
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
      additions.push({ label: "Belge Türü", value: translateInternalValue(ha.document_type) });
    }
    if (ha.possible_period && ha.possible_period !== "tespit edilemedi") {
      additions.push({ label: "Tahmini Dönem", value: translateInternalValue(ha.possible_period) });
    }
    if (ha.possible_sultan_period) {
      additions.push({ label: "Tahmini Padişah Dönemi", value: translateInternalValue(ha.possible_sultan_period) });
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
    <div className="ota-doc-info-tab p-4 md:p-6 space-y-6">
      {/* Detected claims table */}
      {sortedDetected.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedDetected.map((claim, idx) => (
            <div key={`${claim.field}-${idx}`} className="flex flex-col bg-[var(--ota-surface-2)] p-4 rounded-xl border border-[var(--ota-border)] shadow-sm hover:border-[var(--ota-gold)]/50 transition-colors">
              <span className="text-[10px] uppercase tracking-wider text-[var(--ota-text-muted)] font-semibold mb-1">{claim.label}</span>
              <span className="text-[var(--ota-text)] font-medium text-sm mb-3 flex-1">{claim.value}</span>
              <div className="flex items-center gap-2 mt-auto pt-2 border-t border-[var(--ota-border)]">
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
        <div className="mt-8">
          <span className="text-xs uppercase tracking-wider text-[var(--ota-gold)] font-bold mb-4 block">Tarihsel Çıkarım (Harici Kaynak Desteğiyle)</span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {historicalFields.map((f) => (
              <div key={f.label} className="flex flex-col bg-[var(--ota-surface-2)]/50 p-4 rounded-xl border border-[var(--ota-border)]">
                <span className="text-[10px] uppercase tracking-wider text-[var(--ota-text-muted)] font-semibold mb-1">{f.label}</span>
                <span className="text-[var(--ota-text)] font-medium text-sm mb-3">{f.value}</span>
                <div className="flex items-center gap-2 mt-auto pt-2 border-t border-[var(--ota-border)]">
                  <StatusBadge variant="info" label="Sistem Çıkarımı" small />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Not detected summary */}
      {notDetected.length > 0 && (
        <div className="mt-8 border-t border-[var(--ota-border)] pt-6">
          {!showAll ? (
            <div className="flex items-center justify-between bg-[var(--ota-surface-2)]/30 p-3 rounded-lg border border-[var(--ota-border)]">
              <span className="text-xs text-[var(--ota-text-muted)]">
                {notDetected.length} belge bilgisi güvenilir şekilde tespit edilemedi.
              </span>
              <button
                type="button"
                className="text-xs font-medium text-[var(--ota-gold)] hover:text-[var(--ota-gold-light)] transition-colors"
                onClick={() => setShowAll(true)}
              >
                Tüm Alanları Gör
              </button>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-4">
                {notDetected.map((claim, idx) => (
                  <div key={`${claim.field}-${idx}`} className="flex flex-col bg-[var(--ota-surface-2)]/20 p-3 rounded-lg border border-[var(--ota-border)] opacity-60">
                    <span className="text-[10px] uppercase tracking-wider text-[var(--ota-text-muted)] font-semibold mb-1">{claim.label}</span>
                    <span className="text-[var(--ota-text-muted)] font-medium text-sm mb-2">—</span>
                    <div className="mt-auto pt-2 border-t border-[var(--ota-border)]/50">
                      <span className="text-[9px] uppercase tracking-widest text-[var(--ota-text-muted)]">Tespit Edilemedi</span>
                    </div>
                  </div>
                ))}
              </div>
              <button
                type="button"
                className="text-xs font-medium text-[var(--ota-text-muted)] hover:text-[var(--ota-text)] transition-colors"
                onClick={() => setShowAll(false)}
              >
                Gizle ▲
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
