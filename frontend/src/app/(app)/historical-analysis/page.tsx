"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, type EntityItem, type FullDocumentAnalysisResponse } from "@/lib/api";
import { loadActiveDocumentContext } from "@/lib/documentContext";
import { EntityKnowledgeModal } from "@/components/historical/EntityKnowledgeModal";

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
      <main className="ha-page">
        <section className="ha-empty-state">
          <p className="ha-eyebrow">Tarihsel Analiz</p>
          <h1>Henüz aktif bir belge bulunmuyor.</h1>
          <p>Tarihsel analiz için önce bir belge yükleyin ve analiz edin.</p>
          <Link className="ha-primary-link" href="/dashboard">Belgeye Git</Link>
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
  const hasUsableHistoricalInfo = knownFacts.length > 0 || hasEntities || hasTimeline || hasUsefulContext;
  const filteredExternalEvidence = hasUsableHistoricalInfo
    ? result.evidence.historical_external_evidence.filter((item) => item.verified === true)
    : [];
  const visibleExternalEvidence = hasUsableHistoricalInfo ? externalEvidence.filter((item) => item.verified === true) : [];

  return (
    <main className="ha-page">
      <section className="ha-header">
        <div>
          <p className="ha-eyebrow">Tarihsel Bağlam</p>
          <h1>Tarihsel Analiz</h1>
          <p>{hasUsableHistoricalInfo ? asText(analysis.historical_context) : "Bu belge için güvenilir tarihsel bilgi bulunamadı."}</p>
          <div className="ha-nav-actions">
            <button type="button" onClick={() => router.push("/dashboard")}>Ana Çalışma Alanına Dön</button>
            <button type="button" onClick={() => router.push("/image-processing-lab")}>Görüntü İşlemeyi İncele</button>
          </div>
        </div>
        <div className="ha-status-grid" data-testid="historical-status-grid">
          <StatusBadge label="OCR Motoru" value={result.ocr.engine} tone={result.ocr.engine.toLowerCase() === "kraken" ? "good" : "warn"} />
          <StatusBadge label="Fallback" value={result.ocr.fallback_used ? "Var" : "Yok"} tone={result.ocr.fallback_used ? "warn" : "good"} />
          <StatusBadge label="Doğrulanmış Kaynak" value={`${hasUsableHistoricalInfo ? verifiedExternalCount : 0} kaynak`} tone={hasUsableHistoricalInfo && verifiedExternalCount > 0 ? "good" : "warn"} />
          <StatusBadge label="Güven" value={result.confidence.combined_provisional ? `Geçici ${percent(result.confidence.combined)}` : percent(result.confidence.combined)} tone={combinedTone} />
        </div>
      </section>

      {hasUsableHistoricalInfo && <section className="ha-source-legend" aria-label="Kaynak türleri">
        <span className="ha-pill document">Belgeden Gelen Bilgi</span>
        <span className="ha-pill external">Doğrulanmış Harici Kaynak</span>
        <span className="ha-pill inference">Olası Model Çıkarımı</span>
        <span className="ha-pill uncertainty">Belirsizlik</span>
      </section>}

      <section className={`ha-layout ${hasUsableHistoricalInfo ? "" : "no-info"}`}>
        <aside className="ha-column">
          <Panel title="Belge Özeti">
            {hasUsableHistoricalInfo ? (
              <dl className="ha-facts">
                <Fact label="Dosya" value={result.document.filename} source="document" />
                {isKnown(analysis.document_type || result.document.document_type) && <Fact label="Belge Türü" value={analysis.document_type || result.document.document_type} source="inference" provisional={analysis.provisional} />}
                {isKnown(analysis.possible_period) && <Fact label="Tahmini Dönem" value={analysis.possible_period} source="inference" provisional />}
                {isKnown(analysis.possible_sultan_period) && <Fact label="Tahmini Padişah Dönemi" value={analysis.possible_sultan_period} source="inference" provisional />}
                {isKnown(analysis.possible_author) && <Fact label="Yazar" value={analysis.possible_author} source="inference" provisional />}
                {isKnown(analysis.possible_institution) && <Fact label="Kurum" value={analysis.possible_institution} source="inference" provisional />}
                {isKnown(firstPlace) && <Fact label="Yer" value={firstPlace} source="document" />}
                {isKnown(firstDate) && <Fact label="Tarih" value={firstDate} source="document" />}
              </dl>
            ) : (
              <div className="ha-no-info">
                <strong>Bilgi yok</strong>
                <p>Bu fotoğraftan güvenilir belge türü, dönem, kişi, kurum, yer veya tarih bilgisi çıkarılamadı.</p>
                <small>Dosya: {asText(result.document.filename)}</small>
              </div>
            )}
          </Panel>

          {hasEntities && <Panel title="Varlıklar">
            {entityGroups.length ? entityGroups.map((group) => (
              <div className="ha-entity-group" key={group.key}>
                <div className="ha-mini-heading">{group.label}</div>
                <div className="ha-chip-row">
                  {group.items.map((item, index) => {
                    const eName = entityText(item);
                    return (
                      <button 
                        type="button"
                        className="ha-entity-chip hover:bg-amber-500/20 hover:border-amber-500/40 cursor-pointer transition-colors" 
                        key={`${group.key}-${eName}-${index}`}
                        onClick={() => {
                          const encData = result.evidence.historical_external_evidence.find(
                            // eslint-disable-next-line @typescript-eslint/no-explicit-any
                            (e: any) => e.title === `Ansiklopedik Bilgi: ${eName}` || (e.title.includes(eName) && e.source_type === "encyclopedia")
                          );
                          setSelectedEntity({
                            name: eName,
                            description: encData ? (encData.evidence_text as string) : "Bu varlık hakkında detaylı ansiklopedik bilgi bulunamadı."
                          });
                        }}
                      >
                        {eName}
                        <small>{percent(item.confidence_score)}</small>
                      </button>
                    );
                  })}
                </div>
              </div>
            )) : <EmptyText text="Belgeden çıkarılmış varlık yok." />}
          </Panel>}
        </aside>

        <section className="ha-center">
          {hasUsefulContext && <Panel title="Tarihsel Bağlam" wide>
            <div className="ha-context-card">
              <span className="ha-pill inference">Olası Model Çıkarımı</span>
              <p>{asText(analysis.historical_context)}</p>
              <small>Bu yorum, backend analiz cevabındaki `historical_analysis` alanından gelir ve harici kaynakla desteklenmediği sürece doğrulanmış bilgi olarak gösterilmez.</small>
            </div>
          </Panel>}

          {hasTimeline && <Panel title="Zaman Çizelgesi" wide>
            <ol className="ha-timeline">
              {timelineItems.map((item, index) => (
                <li key={`${item.date}-${index}`}>
                  <strong>{item.date}</strong>
                  <span>{item.source}</span>
                  <small>Güven: {percent(item.confidence)}</small>
                </li>
              ))}
            </ol>
          </Panel>}

          {hasUsableHistoricalInfo && <Panel title="Kanıt Karşılaştırması" wide>
            <div className="ha-comparison">
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
          </Panel>}
        </section>

        <aside className="ha-column">
          {hasUsableHistoricalInfo && filteredExternalEvidence.length > 0 && <Panel title="Kaynak Denetimi">
            <input
              className="ha-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Kaynaklarda ara"
              aria-label="Harici kaynaklarda ara"
            />
            <div className="ha-source-list" data-testid="historical-external-evidence">
              {visibleExternalEvidence.length ? visibleExternalEvidence.map((item, index) => {
                const sourceId = evidenceField(item, ["source_id"]);
                const citation = evidenceField(item, ["citation"]);
                const hasCitation = citation !== UNKNOWN;
                const domId = `source-${index}`;
                const verified = item.verified === true;
                return (
                  <details className="ha-source-card" key={`${sourceId}-${index}`}>
                    <summary>
                      <span>{evidenceField(item, ["title", "citation", "source_id"])}</span>
                      <small className={verified ? "ha-verified" : "ha-warning"}>{verified ? "Doğrulanmış" : "Doğrulanmamış"}</small>
                    </summary>
                    <dl className="ha-source-meta">
                      <Fact label="Kaynak Türü" value={evidenceField(item, ["source_type"])} source="external" />
                      <Fact label="Kaynak Kademesi" value={evidenceField(item, ["source_tier"])} source="external" />
                    </dl>
                    <p>{evidenceField(item, ["evidence_text", "text", "quote"])}</p>
                    <button type="button" onClick={() => copyCitation(domId, citation)} disabled={!hasCitation}>
                      {copied === domId ? "Kopyalandı" : "Atıfı Kopyala"}
                    </button>
                  </details>
                );
              }) : <EmptyText text="Sorguyla eşleşen doğrulanmış harici kaynak yok." />}
            </div>
          </Panel>}

          {hasUsableHistoricalInfo && <Panel title="Güven ve Belirsizlik">
            <div className="ha-meter-list">
              <Meter label="OCR" value={result.confidence.ocr} />
              <Meter label="Transliterasyon" value={result.confidence.transliteration} />
              <Meter label="Modern Türkçe" value={result.confidence.modern_turkish} />
              <Meter label="Varlıklar" value={result.confidence.entities} />
              <Meter label="Retrieval" value={result.confidence.retrieval_strength} />
              <Meter label="Kanıt Kapsamı" value={result.confidence.evidence_coverage} />
            </div>
            <div className="ha-warning-list" data-testid="historical-uncertainties">
              {result.uncertainties.length ? result.uncertainties.map((item, index) => (
                <span key={`${item}-${index}`} className="ha-warning-item">{item}</span>
              )) : <span className="ha-ok-item">Önemli bir belirsizlik bildirilmedi.</span>}
              {result.warnings.map((item, index) => (
                <span key={`${item}-${index}`} className="ha-warning-item">{item}</span>
              ))}
            </div>
          </Panel>}

          {hasUsableHistoricalInfo && result.evidence.model_inference.length > 0 && <Panel title="Model Çıkarımları">
            <div className="ha-inference-list" data-testid="historical-model-inference">
              {result.evidence.model_inference.map((item, index) => (
                <div className="ha-inference-card" key={`${evidenceField(item, ["field"])}-${index}`}>
                  <span className="ha-pill inference">Olası Çıkarım</span>
                  <strong>{evidenceField(item, ["field"])}</strong>
                  <p>{evidenceField(item, ["value"])}</p>
                  <small>{evidenceField(item, ["basis"])}</small>
                </div>
              ))}
            </div>
          </Panel>}
        </aside>
      </section>

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
  return (
    <div className={`ha-status ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Panel({ title, children, wide = false }: { title: string; children: React.ReactNode; wide?: boolean }) {
  return (
    <article className={`ha-panel ${wide ? "wide" : ""}`}>
      <header>
        <h2>{title}</h2>
      </header>
      {children}
    </article>
  );
}

function Fact({ label, value, source, provisional = false }: { label: string; value: unknown; source: "document" | "external" | "inference" | "uncertainty"; provisional?: boolean }) {
  const text = asText(value);
  const empty = text === UNKNOWN;
  return (
    <div className={empty ? "missing" : ""}>
      <dt>{label}</dt>
      <dd>
        <span>{text}</span>
        <small className={`ha-source-tag ${empty ? "uncertainty" : source}`}>
          {empty ? "Belirsiz" : provisional ? "Olası" : source === "document" ? "Belge" : source === "external" ? "Harici" : "Çıkarım"}
        </small>
      </dd>
    </div>
  );
}

function EvidencePreview({ title, label, kind, items, textKeys }: { title: string; label: string; kind: "document" | "external"; items: EvidenceRecord[]; textKeys: string[] }) {
  return (
    <div className={`ha-evidence-preview ${kind}`}>
      <span className={`ha-pill ${kind}`}>{label}</span>
      <h3>{title}</h3>
      {items.slice(0, 3).map((item, index) => (
        <p key={`${title}-${index}`}>{evidenceField(item, textKeys)}</p>
      ))}
      {!items.length && <EmptyText text="Bu kaynak türü için kanıt yok." />}
    </div>
  );
}

function Meter({ label, value }: { label: string; value?: number | null }) {
  const safeValue = typeof value === "number" && !Number.isNaN(value) ? Math.max(0, Math.min(1, value)) : 0;
  return (
    <div className="ha-meter">
      <div>
        <span>{label}</span>
        <strong>{percent(value)}</strong>
      </div>
      <span className="ha-meter-track">
        <span style={{ width: `${safeValue * 100}%` }} />
      </span>
    </div>
  );
}

function EmptyText({ text }: { text: string }) {
  return <p className="ha-empty-text">{text}</p>;
}
