"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, type EntityItem, type FullDocumentAnalysisResponse } from "@/lib/api";
import { loadActiveDocumentContext } from "@/lib/documentContext";
import { EntityKnowledgeModal } from "@/components/historical/EntityKnowledgeModal";
import { Icons } from "@/components/Icons";
import { AlertTriangle, Search } from 'lucide-react';
import StructuredHistoricalAnalysis, { parseHistoricalContent } from "@/components/workspace/StructuredHistoricalAnalysis";

const UNKNOWN = "Tespit edilemedi";

type StoredAnalysis = {
  result: FullDocumentAnalysisResponse;
  saved_at?: string;
  source?: string;
};

type EvidenceRecord = Record<string, unknown>;

const ENTITY_GROUPS: Array<{ key: keyof FullDocumentAnalysisResponse["entities"]; label: string }> = [
  { key: "persons", label: "Kişiler" },
  { key: "places", label: "Yerler" },
  { key: "institutions", label: "Kurumlar" },
  { key: "dates", label: "Tarihler" },
  { key: "titles", label: "Unvanlar" },
  { key: "document_marks", label: "Belge İşaretleri" },
];

function asText(value: unknown): string {
  if (value == null) return UNKNOWN;
  const text = String(value).trim();
  return text || UNKNOWN;
}

function isKnown(value: unknown): boolean {
  const text = asText(value);
  const normalized = text.toLowerCase();
  return text !== UNKNOWN
    && normalized !== "n/a"
    && normalized !== "unknown"
    && normalized !== "none"
    && normalized !== "belirsiz"
    && normalized !== "tespit edilemedi";
}

function isUsefulHistoricalContext(value: unknown): boolean {
  const text = asText(value);
  if (!isKnown(text)) return false;
  if (/doğrulanmış dış kaynaklar bulundu/i.test(text)) return false;
  if (/verified external sources found/i.test(text)) return false;
  return text.length > 24;
}

function entityText(entity: EntityItem): string {
  return asText(entity.value || entity.normalized_value || entity.text);
}

function percent(value?: number | null): string {
  if (typeof value !== "number" || Number.isNaN(value)) return UNKNOWN;
  return `%${Math.round(value * 100)}`;
}

function evidenceField(item: EvidenceRecord, keys: string[]): string {
  for (const key of keys) {
    const value = item[key];
    if (value != null && String(value).trim()) return String(value);
  }
  return UNKNOWN;
}

function confidenceTone(value?: number | null): "high" | "medium" | "low" {
  if (typeof value !== "number") return "low";
  if (value >= 0.75) return "high";
  if (value >= 0.45) return "medium";
  return "low";
}

export default function HistoricalAnalysisPage() {
  const router = useRouter();
  const [stored] = useState<StoredAnalysis | null>(() => {
    if (typeof window === "undefined") return null;
    const context = loadActiveDocumentContext();
    if (!context?.analysisResult?.document || !context.analysisResult.evidence) return null;
    return { result: context.analysisResult, saved_at: context.savedAt, source: context.source };
  });
  const [query, setQuery] = useState("");
  const [copied, setCopied] = useState("");
  const [selectedEntity, setSelectedEntity] = useState<{name: string, description: string} | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
    }
  }, [router]);

  const result = stored?.result || null;
  const externalEvidence = useMemo(() => {
    const items = result?.evidence.historical_external_evidence || [];
    const needle = query.trim().toLowerCase();
    if (!needle) return items;
    return items.filter((item) =>
      ["title", "citation", "source_id", "evidence_text", "source_type", "source_tier"]
        .some((key) => evidenceField(item, [key]).toLowerCase().includes(needle))
    );
  }, [query, result]);

  const entityGroups = useMemo(() => {
    if (!result) return [];
    return ENTITY_GROUPS.map((group) => ({
      ...group,
      items: result.entities[group.key].filter((item) => entityText(item) !== UNKNOWN),
    })).filter((group) => group.items.length > 0);
  }, [result]);

  const timelineItems = useMemo(() => {
    if (!result) return [];
    return result.entities.dates
      .map((item) => ({
        date: entityText(item),
        confidence: item.confidence_score,
        source: "Belgeden çıkarılan tarih",
      }))
      .filter((item) => item.date !== UNKNOWN);
  }, [result]);

  const copyCitation = (id: string, citation: string) => {
    if (!citation || citation === UNKNOWN) return;
    void navigator.clipboard.writeText(citation);
    setCopied(id);
    window.setTimeout(() => setCopied(""), 1500);
  };

  if (!result) {
    return (
      <main className="w-full p-8 animate-in slide-in-from-bottom-4 fade-in duration-700">
        <section className="glass-panel min-h-[80vh] flex flex-col items-center justify-center rounded-2xl border border-[var(--ota-border)] shadow-[var(--glass-shadow)] py-20 text-center relative overflow-hidden">
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[var(--ota-gold)]/5 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/3 pointer-events-none" />
          <div className="text-[var(--ota-gold)] w-16 h-16 mx-auto mb-6 drop-shadow-md opacity-80">{Icons.museum}</div>
          <p className="text-[var(--ota-gold)] font-medium uppercase tracking-wider mb-2 text-sm">Tarihsel Analiz</p>
          <h1 className="text-3xl font-bold text-[var(--ota-text)] mb-4">Henüz aktif bir belge bulunmuyor.</h1>
          <p className="text-[var(--ota-text-muted)] mb-8 max-w-md">Tarihsel analiz için önce bir belge yükleyin ve analiz edin.</p>
          <Link className="px-6 py-3 bg-[var(--ota-gold)] text-[#0A202A] font-semibold rounded-xl hover:bg-[var(--ota-gold)]/90 transition-colors shadow-lg" href="/dashboard">Belgeye Git</Link>
        </section>
      </main>
    );
  }

  const analysis = result.historical_analysis;
  const firstPlace = result.entities.places.map(entityText).find((item) => item !== UNKNOWN) || UNKNOWN;
  const firstDate = result.entities.dates.map(entityText).find((item) => item !== UNKNOWN) || UNKNOWN;
  const verifiedExternalCount = result.evidence.historical_external_evidence.filter((item) => item.verified === true).length;
  const combinedTone = confidenceTone(result.confidence.combined);
  const knownFacts = [
    analysis.document_type || result.document.document_type,
    analysis.possible_period,
    analysis.possible_sultan_period,
    analysis.possible_author,
    analysis.possible_institution,
    firstPlace,
    firstDate,
  ].filter(isKnown);
  const hasEntities = entityGroups.length > 0;
  const hasTimeline = timelineItems.length > 0;
  const hasUsefulContext = isUsefulHistoricalContext(analysis.historical_context);
  const parsedContext = useMemo(() => hasUsefulContext ? parseHistoricalContent(asText(analysis.historical_context)) : null, [hasUsefulContext, analysis.historical_context]);
  const headerContextText = parsedContext ? (parsedContext.summary || parsedContext.historicalAnalysis || parsedContext.detailedAnalysis || asText(analysis.historical_context)) : asText(analysis.historical_context);
  const hasUsableHistoricalInfo = knownFacts.length > 0 || hasEntities || hasTimeline || hasUsefulContext;
  const filteredExternalEvidence = hasUsableHistoricalInfo
    ? result.evidence.historical_external_evidence.filter((item) => item.verified === true)
    : [];
  const visibleExternalEvidence = hasUsableHistoricalInfo ? externalEvidence.filter((item) => item.verified === true) : [];

  return (
    <main className="w-full p-4 lg:p-8 animate-in slide-in-from-bottom-4 fade-in duration-700">
      
      {/* Header Section */}
      <header className="ota-page-header">
        <div className="absolute inset-0 opacity-[0.03] bg-[url('/auth/floral-pattern.png')] bg-repeat pointer-events-none" />
        <div className="relative z-10 flex-1">
          <p className="text-[var(--ota-gold)] font-medium uppercase tracking-wider mb-2 text-xs">Tarihsel Bağlam</p>
          <h1 className="text-3xl font-serif font-bold text-[var(--ota-text)] mb-3">Tarihsel Analiz</h1>
          <p className="text-[var(--ota-text-muted)] max-w-3xl leading-relaxed text-sm">
            {hasUsableHistoricalInfo ? headerContextText : "Bu belge için güvenilir tarihsel bilgi bulunamadı."}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button type="button" onClick={() => router.push("/dashboard")} className="px-4 py-2 bg-[var(--ota-bg-2)] border border-[var(--ota-border)] hover:border-[var(--ota-gold)]/50 hover:bg-[var(--ota-gold-dim)] text-[var(--ota-text)] rounded-lg text-sm transition-all font-medium">Ana Çalışma Alanına Dön</button>
            <button type="button" onClick={() => router.push("/image-processing-lab")} className="px-4 py-2 bg-[var(--ota-bg-2)] border border-[var(--ota-border)] hover:border-[var(--ota-iznik-turquoise)]/50 hover:bg-[var(--ota-iznik-turquoise)]/10 text-[var(--ota-text)] rounded-lg text-sm transition-all font-medium">Görüntü İşlemeyi İncele</button>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-3 relative z-10 w-full md:w-auto">
          <StatusBadge label="OCR Motoru" value={result.ocr.engine} tone={result.ocr.engine.toLowerCase() === "kraken" ? "good" : "warn"} />
          <StatusBadge label="Fallback" value={result.ocr.fallback_used ? "Var" : "Yok"} tone={result.ocr.fallback_used ? "warn" : "good"} />
          <StatusBadge label="Doğrulanmış Kaynak" value={`${hasUsableHistoricalInfo ? verifiedExternalCount : 0} kaynak`} tone={hasUsableHistoricalInfo && verifiedExternalCount > 0 ? "good" : "warn"} />
          <StatusBadge label="Güven" value={result.confidence.combined_provisional ? `Geçici ${percent(result.confidence.combined)}` : percent(result.confidence.combined)} tone={combinedTone} />
        </div>
      </header>

      {hasUsableHistoricalInfo && (
        <section className="flex flex-wrap gap-3 mb-6 px-2" aria-label="Kaynak türleri">
          <span className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full border border-[var(--ota-border)] bg-[var(--ota-bg-2)] text-[var(--ota-text-2)]"><span className="w-2 h-2 rounded-full bg-[var(--ota-gold)]"></span> Belgeden Gelen Bilgi</span>
          <span className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full border border-[var(--ota-border)] bg-[var(--ota-bg-2)] text-[var(--ota-text-2)]"><span className="w-2 h-2 rounded-full bg-[var(--ota-iznik-turquoise)]"></span> Doğrulanmış Harici Kaynak</span>
          <span className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full border border-[var(--ota-border)] bg-[var(--ota-bg-2)] text-[var(--ota-text-2)]"><span className="w-2 h-2 rounded-full bg-[var(--ota-sage)]"></span> Olası Model Çıkarımı</span>
          <span className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full border border-[var(--ota-ruby)]/30 bg-[var(--ota-ruby)]/5 text-[var(--ota-ruby)]"><span className="w-2 h-2 rounded-full bg-[var(--ota-ruby)]"></span> Belirsizlik</span>
        </section>
      )}

      {/* Main Layout Grid */}
      <div className={`flex flex-col lg:flex-row gap-8 items-start ${!hasUsableHistoricalInfo ? "opacity-50" : ""}`}>
        
        {/* Main Content Column */}
        <section className="flex-1 flex flex-col gap-8 min-w-0 w-full lg:max-w-[75%] xl:max-w-[70%]">
          {hasEntities && (
            <Panel title="Varlıklar">
              {entityGroups.length ? entityGroups.map((group) => (
                <div className="mb-5 last:mb-0" key={group.key}>
                  <div className="text-xs font-semibold text-[var(--ota-text-muted)] uppercase tracking-wider mb-3">{group.label}</div>
                  <div className="flex flex-wrap gap-2">
                    {group.items.map((item, index) => {
                      const eName = entityText(item);
                      return (
                        <button 
                          type="button"
                          className="px-3 py-1.5 bg-[var(--ota-bg-2)] border border-[var(--ota-border)] hover:border-[var(--ota-gold)]/50 hover:bg-[var(--ota-gold-dim)] rounded-lg text-sm text-[var(--ota-text)] transition-colors flex items-center gap-2 cursor-pointer group" 
                          key={`${group.key}-${eName}-${index}`}
                          onClick={() => {
                            const encData = result.evidence.historical_external_evidence.find(
                              (e: Record<string, unknown>) => typeof e.title === "string" && (e.title === `Ansiklopedik Bilgi: ${eName}` || (e.title.includes(eName) && e.source_type === "encyclopedia"))
                            );
                            setSelectedEntity({
                              name: eName,
                              description: encData ? (encData.evidence_text as string) : "Bu varlık hakkında detaylı ansiklopedik bilgi bulunamadı."
                            });
                          }}
                        >
                          {eName}
                          <span className="text-[10px] text-[var(--ota-text-muted)] group-hover:text-[var(--ota-gold)]">{percent(item.confidence_score)}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )) : <EmptyText text="Belgeden çıkarılmış varlık yok." />}
            </Panel>
          )}
          {hasUsefulContext && (
            <div className="bg-[var(--ota-bg-2)]/50 border border-[var(--ota-sage)]/30 rounded-xl p-0 relative overflow-hidden mb-8">
              <div className="absolute top-0 left-0 w-1 h-full bg-[var(--ota-sage)]" />
              <div className="p-5 border-b border-[var(--ota-border)]/50 bg-[var(--ota-bg-1)]">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-serif font-bold text-[var(--ota-text)]">Genişletilmiş Tarihsel Bağlam</h3>
                  <span className="inline-block px-2 py-1 bg-[var(--ota-sage)]/10 text-[var(--ota-sage)] text-[10px] font-bold uppercase tracking-wider rounded">Olası Model Çıkarımı</span>
                </div>
                <p className="text-[var(--ota-text-muted)] text-xs italic mt-2">Bu analiz AI modeli tarafından yapılmıştır. Lütfen dış kaynaklarla doğrulayın.</p>
              </div>
              <div className="p-2 lg:p-6">
                <StructuredHistoricalAnalysis rawText={asText(analysis.historical_context)} />
              </div>
            </div>
          )}

          {hasTimeline && (
            <Panel title="Zaman Çizelgesi" wide>
              <div className="relative pl-6 border-l-2 border-[var(--ota-gold)]/30 space-y-6">
                {timelineItems.map((item, index) => (
                  <div key={`${item.date}-${index}`} className="relative">
                    <div className="absolute -left-[31px] top-1 w-4 h-4 rounded-full bg-[var(--ota-bg)] border-2 border-[var(--ota-gold)] shadow-[0_0_8px_rgba(215,165,72,0.5)]" />
                    <strong className="block text-lg font-bold text-[var(--ota-text)] mb-1">{item.date}</strong>
                    <span className="block text-sm text-[var(--ota-text-2)] mb-1">{item.source}</span>
                    <span className="inline-block px-2 py-0.5 bg-[var(--ota-bg-2)] border border-[var(--ota-border)] text-[var(--ota-text-muted)] text-xs rounded">Güven: {percent(item.confidence)}</span>
                  </div>
                ))}
              </div>
            </Panel>
          )}

          {hasUsableHistoricalInfo && (
            <Panel title="Kanıt Karşılaştırması" wide>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <EvidencePreview
                  title="Belge Kanıtı"
                  label="Belgeden Gelen Bilgi"
                  kind="document"
                  items={result.evidence.document_evidence}
                  textKeys={["quote", "text", "source"]}
                />
                <EvidencePreview
                  title="Harici Kanıt"
                  label="Doğrulanmış Harici Kaynak"
                  kind="external"
                  items={filteredExternalEvidence}
                  textKeys={["evidence_text", "title", "citation"]}
                />
              </div>
            </Panel>
          )}


          {hasTimeline && (
            <Panel title="Zaman Çizelgesi" wide>
              <div className="relative pl-6 border-l-2 border-[var(--ota-gold)]/30 space-y-6">
                {timelineItems.map((item, index) => (
                  <div key={`${item.date}-${index}`} className="relative">
                    <div className="absolute -left-[31px] top-1 w-4 h-4 rounded-full bg-[var(--ota-bg)] border-2 border-[var(--ota-gold)] shadow-[0_0_8px_rgba(215,165,72,0.5)]" />
                    <strong className="block text-lg font-bold text-[var(--ota-text)] mb-1">{item.date}</strong>
                    <span className="block text-sm text-[var(--ota-text-2)] mb-1">{item.source}</span>
                    <span className="inline-block px-2 py-0.5 bg-[var(--ota-bg-2)] border border-[var(--ota-border)] text-[var(--ota-text-muted)] text-xs rounded">Güven: {percent(item.confidence)}</span>
                  </div>
                ))}
              </div>
            </Panel>
          )}

          {hasUsableHistoricalInfo && (
            <Panel title="Kanıt Karşılaştırması" wide>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <EvidencePreview
                  title="Belge Kanıtı"
                  label="Belgeden Gelen Bilgi"
                  kind="document"
                  items={result.evidence.document_evidence}
                  textKeys={["quote", "text", "source"]}
                />
                <EvidencePreview
                  title="Harici Kanıt"
                  label="Doğrulanmış Harici Kaynak"
                  kind="external"
                  items={filteredExternalEvidence}
                  textKeys={["evidence_text", "title", "citation"]}
                />
              </div>
            </Panel>
          )}

          {hasUsableHistoricalInfo && result.evidence.model_inference.length > 0 && (
            <Panel title="Model Çıkarımları" wide>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {result.evidence.model_inference.map((item, index) => (
                  <div className="bg-[var(--ota-bg-2)] border border-[var(--ota-sage)]/30 rounded-lg p-4 relative overflow-hidden flex flex-col" key={`${evidenceField(item, ["field"])}-${index}`}>
                    <div className="absolute left-0 top-0 w-1 h-full bg-[var(--ota-sage)]/50" />
                    <span className="text-[9px] font-bold uppercase tracking-wider text-[var(--ota-sage)] mb-1 block">Olası Çıkarım</span>
                    <strong className="block text-sm font-semibold text-[var(--ota-text)] mb-2">{evidenceField(item, ["field"])}</strong>
                    <p className="text-sm text-[var(--ota-text-2)] mb-3 flex-1">{evidenceField(item, ["value"])}</p>
                    <small className="block text-xs text-[var(--ota-text-muted)] p-2 bg-[var(--ota-bg)] rounded border border-[var(--ota-border)]">{evidenceField(item, ["basis"])}</small>
                  </div>
                ))}
              </div>
            </Panel>
          )}
        </section>

        {/* Right Column (Sticky) */}
        <aside className="w-full lg:w-[320px] xl:w-[360px] flex-shrink-0 flex flex-col gap-6 lg:sticky lg:top-8">
          <Panel title="Belge Özeti">
            {hasUsableHistoricalInfo ? (
              <dl className="flex flex-col gap-3">
                <Fact label="Dosya" value={result.document.filename} source="document" />
                {isKnown(analysis.document_type || result.document.document_type) && <Fact label="Belge Türü" value={analysis.document_type || result.document.document_type} source="inference" provisional={analysis.provisional} />}
                {isKnown(analysis.possible_period) && <Fact label="Dönem" value={analysis.possible_period} source="inference" provisional />}
                {isKnown(analysis.possible_sultan_period) && <Fact label="Padişah" value={analysis.possible_sultan_period} source="inference" provisional />}
                {isKnown(analysis.possible_author) && <Fact label="Yazar" value={analysis.possible_author} source="inference" provisional />}
                {isKnown(analysis.possible_institution) && <Fact label="Kurum" value={analysis.possible_institution} source="inference" provisional />}
                {isKnown(firstPlace) && <Fact label="Yer" value={firstPlace} source="document" />}
                {isKnown(firstDate) && <Fact label="Tarih" value={firstDate} source="document" />}
              </dl>
            ) : (
              <EmptyText text="Bilgi Yok" />
            )}
          </Panel>
          {hasUsableHistoricalInfo && filteredExternalEvidence.length > 0 && (
            <Panel title="Kaynak Denetimi">
              <div className="relative mb-4">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--ota-text-muted)] text-sm"><Search className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>
                <input
                  className="w-full bg-[var(--ota-bg-2)] border border-[var(--ota-border)] text-[var(--ota-text)] text-sm rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:border-[var(--ota-gold)]/50 transition-colors"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Kaynaklarda ara"
                  aria-label="Harici kaynaklarda ara"
                />
              </div>
              <div className="flex flex-col gap-3 custom-scrollbar max-h-[400px] overflow-y-auto pr-2">
                {visibleExternalEvidence.length ? visibleExternalEvidence.map((item, index) => {
                  const sourceId = evidenceField(item, ["source_id"]);
                  const citation = evidenceField(item, ["citation"]);
                  const hasCitation = citation !== UNKNOWN;
                  const domId = `source-${index}`;
                  const verified = item.verified === true;
                  return (
                    <details className="bg-[var(--ota-bg-2)] border border-[var(--ota-border)] rounded-xl overflow-hidden group" key={`${sourceId}-${index}`}>
                      <summary className="p-3 cursor-pointer select-none flex flex-col gap-2 hover:bg-[var(--ota-bg-2)]/80 transition-colors">
                        <div className="flex items-start justify-between gap-2">
                          <span className="font-semibold text-sm text-[var(--ota-text)] group-open:text-[var(--ota-gold)] transition-colors">{evidenceField(item, ["title", "citation", "source_id"])}</span>
                          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded flex-shrink-0 ${verified ? "bg-[var(--ota-iznik-turquoise)]/10 text-[var(--ota-iznik-turquoise)]" : "bg-[var(--ota-ruby)]/10 text-[var(--ota-ruby)]"}`}>
                            {verified ? "Doğrulanmış" : "Doğrulanmamış"}
                          </span>
                        </div>
                      </summary>
                      <div className="p-3 pt-0 border-t border-[var(--ota-border)]/50 bg-[var(--ota-bg)]/50 mt-2">
                        <dl className="flex flex-col gap-2 my-3">
                          <Fact label="Kaynak Türü" value={evidenceField(item, ["source_type"])} source="external" />
                          <Fact label="Kaynak Kademesi" value={evidenceField(item, ["source_tier"])} source="external" />
                        </dl>
                        <p className="text-xs text-[var(--ota-text-2)] leading-relaxed mb-3 p-3 bg-[var(--ota-bg-2)] rounded-lg border border-[var(--ota-border)]">
                          {evidenceField(item, ["evidence_text", "text", "quote"])}
                        </p>
                        <button 
                          type="button" 
                          onClick={() => copyCitation(domId, citation)} 
                          disabled={!hasCitation}
                          className="w-full py-1.5 text-xs font-medium bg-[var(--ota-bg-2)] border border-[var(--ota-border)] hover:border-[var(--ota-gold)] hover:text-[var(--ota-gold)] rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {copied === domId ? "✓ Kopyalandı" : "Atıfı Kopyala"}
                        </button>
                      </div>
                    </details>
                  );
                }) : <EmptyText text="Sorguyla eşleşen doğrulanmış harici kaynak yok." />}
              </div>
            </Panel>
          )}

          {hasUsableHistoricalInfo && (
            <Panel title="Güven ve Belirsizlik">
              <div className="flex flex-col gap-3 mb-5">
                <Meter label="OCR" value={result.confidence.ocr} />
                <Meter label="Transliterasyon" value={result.confidence.transliteration} />
                <Meter label="Modern Türkçe" value={result.confidence.modern_turkish} />
                <Meter label="Varlıklar" value={result.confidence.entities} />
                <Meter label="Retrieval" value={result.confidence.retrieval_strength} />
                <Meter label="Kanıt Kapsamı" value={result.confidence.evidence_coverage} />
              </div>
              <div className="flex flex-col gap-2 pt-4 border-t border-[var(--ota-border)]">
                {result.uncertainties.length ? result.uncertainties.map((item, index) => (
                  <span key={`${item}-${index}`} className="text-xs p-2 bg-[var(--ota-ruby)]/10 text-[var(--ota-ruby)] border border-[var(--ota-ruby)]/20 rounded flex items-start gap-2">
                    <span><AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> {item}
                  </span>
                )) : <span className="text-xs p-2 bg-[var(--ota-success)]/10 text-[var(--ota-success)] border border-[var(--ota-success)]/20 rounded flex items-center gap-2">
                  <span>✓</span> Önemli bir belirsizlik bildirilmedi.
                </span>}
                {result.warnings.map((item, index) => (
                  <span key={`${item}-${index}`} className="text-xs p-2 bg-[var(--ota-ruby)]/10 text-[var(--ota-ruby)] border border-[var(--ota-ruby)]/20 rounded flex items-start gap-2">
                    <span><AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> {item}
                  </span>
                ))}
              </div>
            </Panel>
          )}

        </aside>
      </div>

      {selectedEntity && (
        <EntityKnowledgeModal 
          isOpen={!!selectedEntity}
          onClose={() => setSelectedEntity(null)}
          entityName={selectedEntity.name}
          description={selectedEntity.description}
        />
      )}
    </main>
  );
}

function StatusBadge({ label, value, tone }: { label: string; value: string; tone: "good" | "warn" | "high" | "medium" | "low" }) {
  const getColors = () => {
    switch(tone) {
      case "good":
      case "high": return "bg-[var(--ota-success)]/10 border-[var(--ota-success)]/30 text-[var(--ota-success)]";
      case "warn":
      case "medium": return "bg-[var(--ota-gold-dim)] border-[var(--ota-gold)]/30 text-[var(--ota-gold)]";
      case "low": return "bg-[var(--ota-ruby)]/10 border-[var(--ota-ruby)]/30 text-[var(--ota-ruby)]";
      default: return "bg-[var(--ota-bg-2)] border-[var(--ota-border)] text-[var(--ota-text)]";
    }
  };

  return (
    <div className={`p-4 rounded-xl border flex flex-col items-center justify-center text-center ${getColors()}`}>
      <span className="text-xs uppercase tracking-wider font-semibold opacity-80 mb-1">{label}</span>
      <strong className="text-lg font-bold">{value}</strong>
    </div>
  );
}

function Panel({ title, children, wide = false }: { title: string; children: React.ReactNode; wide?: boolean }) {
  return (
    <article className={`glass-panel p-6 rounded-2xl border border-[var(--ota-border)] shadow-[var(--glass-shadow)] flex flex-col h-full bg-[var(--ota-surface)]`}>
      <header className="mb-5 pb-3 border-b border-[var(--ota-border)]">
        <h2 className="text-lg font-bold text-[var(--ota-text)] flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--ota-gold)]"></span>
          {title}
        </h2>
      </header>
      <div className="flex-1">
        {children}
      </div>
    </article>
  );
}

function Fact({ label, value, source, provisional = false }: { label: string; value: unknown; source: "document" | "external" | "inference" | "uncertainty"; provisional?: boolean }) {
  const text = asText(value);
  const empty = text === UNKNOWN;
  
  const getSourceStyle = () => {
    if (empty) return "bg-[var(--ota-ruby)]/10 text-[var(--ota-ruby)] border-[var(--ota-ruby)]/20";
    if (source === "document") return "bg-[var(--ota-gold)]/10 text-[var(--ota-gold)] border-[var(--ota-gold)]/20";
    if (source === "external") return "bg-[var(--ota-iznik-turquoise)]/10 text-[var(--ota-iznik-turquoise)] border-[var(--ota-iznik-turquoise)]/20";
    return "bg-[var(--ota-sage)]/10 text-[var(--ota-sage)] border-[var(--ota-sage)]/20";
  };
  
  const getSourceLabel = () => {
    if (empty) return "Belirsiz";
    if (provisional) return "Olası";
    if (source === "document") return "Belge";
    if (source === "external") return "Harici";
    return "Çıkarım";
  };

  return (
    <div className={`flex flex-col sm:flex-row sm:items-start sm:justify-between py-2 border-b border-[var(--ota-border)]/50 last:border-0 gap-2 ${empty ? "opacity-60" : ""}`}>
      <dt className="text-xs font-semibold text-[var(--ota-text-muted)] uppercase tracking-wider pt-1 sm:w-1/3">{label}</dt>
      <dd className="flex flex-col sm:items-end gap-1 sm:w-2/3">
        <span className="text-sm text-[var(--ota-text)] font-medium sm:text-right">{text}</span>
        <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${getSourceStyle()}`}>
          {getSourceLabel()}
        </span>
      </dd>
    </div>
  );
}

function EvidencePreview({ title, label, kind, items, textKeys }: { title: string; label: string; kind: "document" | "external"; items: EvidenceRecord[]; textKeys: string[] }) {
  const isDoc = kind === "document";
  const colorToken = isDoc ? "var(--ota-gold)" : "var(--ota-iznik-turquoise)";
  
  return (
    <div className="flex flex-col h-full bg-[var(--ota-bg-2)]/50 rounded-xl border border-[var(--ota-border)] overflow-hidden">
      <div className="p-4 border-b border-[var(--ota-border)] flex flex-col gap-1" style={{ borderTop: `3px solid ${colorToken}`}}>
        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full self-start" style={{ backgroundColor: `color-mix(in srgb, ${colorToken} 15%, transparent)`, color: colorToken }}>
          {label}
        </span>
        <h3 className="text-base font-bold text-[var(--ota-text)] mt-1">{title}</h3>
      </div>
      <div className="p-4 flex-1 flex flex-col gap-3">
        {items.slice(0, 3).map((item, index) => (
          <div key={`${title}-${index}`} className="p-3 bg-[var(--ota-bg)] rounded-lg border border-[var(--ota-border)] text-xs text-[var(--ota-text-2)] leading-relaxed">
            {evidenceField(item, textKeys)}
          </div>
        ))}
        {!items.length && <EmptyText text="Bu kaynak türü için kanıt yok." />}
      </div>
    </div>
  );
}

function Meter({ label, value }: { label: string; value?: number | null }) {
  const safeValue = typeof value === "number" && !Number.isNaN(value) ? Math.max(0, Math.min(1, value)) : 0;
  
  const getColor = () => {
    if (safeValue >= 0.75) return "bg-[var(--ota-success)] shadow-[0_0_8px_var(--ota-success)]";
    if (safeValue >= 0.45) return "bg-[var(--ota-gold)] shadow-[0_0_8px_var(--ota-gold)]";
    return "bg-[var(--ota-ruby)] shadow-[0_0_8px_var(--ota-ruby)]";
  };

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex justify-between items-end">
        <span className="text-xs font-medium text-[var(--ota-text-2)] uppercase tracking-wider">{label}</span>
        <strong className="text-xs font-bold text-[var(--ota-text)]">{percent(value)}</strong>
      </div>
      <div className="h-1.5 w-full bg-[var(--ota-bg-2)] rounded-full overflow-hidden border border-[var(--ota-border)]">
        <div className={`h-full rounded-full transition-all duration-1000 ease-out ${getColor()}`} style={{ width: `${safeValue * 100}%` }} />
      </div>
    </div>
  );
}

function EmptyText({ text }: { text: string }) {
  return <p className="text-sm text-[var(--ota-text-muted)] italic p-4 text-center bg-[var(--ota-bg-2)]/30 rounded-lg border border-dashed border-[var(--ota-border)]">{text}</p>;
}
