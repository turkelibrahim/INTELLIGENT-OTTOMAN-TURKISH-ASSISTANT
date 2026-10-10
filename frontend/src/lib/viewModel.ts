/**
 * View Model Layer
 * Backend raw data → Kullanıcıya gösterilecek form
 * Raw enum, API key ve internal field ismlerini Türkçe UI etiketlerine çevirir.
 */

import type { FullDocumentAnalysisResponse, EntityItem, FullAnalysisLine } from "./api";

// ── Status Label Mapping ────────────────────────────────────────────────────

const STATUS_LABELS: Record<string, string> = {
  verified: "Belgeden Tespit Edildi",
  supported_by_external: "Dış Kaynakla Desteklendi",
  SUPPORTED_BY_EXTERNAL_SOURCE: "Dış Kaynakla Desteklendi",
  probable: "Muhtemel",
  possible: "Muhtemel",
  uncertain: "Belirsiz",
  unknown: "Belirsiz",
  not_detected: "Tespit Edilemedi",
  NOT_DETECTED: "Tespit Edilemedi",
  inferred: "Çıkarım",
  external: "Dış Kaynak",
  document: "Belge",
};

export function mapClaimStatus(status: string): { label: string; variant: "success" | "warning" | "neutral" | "error" | "info" } {
  const normalized = status?.toLowerCase().replace(/[_-]/g, "_") ?? "";
  if (normalized === "verified") return { label: "Belgeden Tespit Edildi", variant: "success" };
  if (normalized.includes("external") || normalized.includes("supported")) return { label: "Dış Kaynakla Desteklendi", variant: "info" };
  if (normalized === "probable" || normalized === "possible") return { label: "Muhtemel", variant: "warning" };
  if (normalized === "uncertain" || normalized === "unknown") return { label: "Belirsiz", variant: "neutral" };
  if (normalized.includes("not_detected") || normalized === "not_detected") return { label: "Tespit Edilemedi", variant: "neutral" };
  return { label: STATUS_LABELS[status] ?? status, variant: "neutral" };
}

// ── Field Label Mapping ─────────────────────────────────────────────────────

export const FIELD_LABELS: Record<string, string> = {
  document_type: "Belge Türü",
  date_raw: "Tarih",
  date_normalized: "Tarih (Düzenlenmiş)",
  date_calendar: "Takvim",
  "author/sender": "Yazar / Gönderen",
  possible_author: "Yazar / Gönderen",
  recipient: "Muhatap",
  place: "Yer",
  possible_institution: "Kurum",
  institutions: "Kurumlar",
  persons: "Kişiler",
  locations: "Lokasyonlar",
  "subject/topic": "Konu",
  summary: "Özet",
  seal_presence: "Mühür",
  signature_presence: "İmza",
  tughra_presence: "Tuğra",
  marginal_note_presence: "Kenar Notu",
  possible_period: "Tahmini Dönem",
  possible_sultan_period: "Tahmini Padişah Dönemi",
  historical_context: "Tarihsel Bağlam",
};

export function mapFieldLabel(field: string): string {
  return FIELD_LABELS[field] ?? field.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

export function translateInternalValue(val: string | undefined | null): string {
  if (!val) return "Tespit Edilemedi";
  const lower = val.toLowerCase().trim();
  if (lower === "not_assessed") return "Değerlendirilemedi";
  if (lower === "not_detected" || lower === "none" || lower === "n/a") return "Tespit Edilemedi";
  if (lower === "unknown" || lower === "uncertain") return "Belirsiz";
  if (lower === "possible_period") return "Tahmini Dönem";
  if (lower === "possible_author") return "Muhtemel Yazar";
  if (lower === "possible_sultan_period") return "Tahmini Padişah Dönemi";
  if (lower === "possible_institution") return "Muhtemel Kurum";
  return val;
}

// ── Entity Type Labels ──────────────────────────────────────────────────────

export const ENTITY_TYPE_LABELS: Record<string, string> = {
  PERSON: "Kişi",
  person: "Kişi",
  PLACE: "Yer",
  place: "Yer",
  LOCATION: "Yer",
  location: "Yer",
  ORGANIZATION: "Kurum",
  organization: "Kurum",
  INSTITUTION: "Kurum",
  institution: "Kurum",
  DATE: "Tarih",
  date: "Tarih",
  TITLE: "Unvan",
  title: "Unvan",
  SEAL: "Mühür",
  seal: "Mühür",
  SIGNATURE: "İmza",
  signature: "İmza",
  TUGHRA: "Tuğra",
  tughra: "Tuğra",
  DOCUMENT_MARK: "Belge İşareti",
  document_mark: "Belge İşareti",
};

export function mapEntityType(type: string): string {
  return ENTITY_TYPE_LABELS[type] ?? type;
}

// ── Confidence ──────────────────────────────────────────────────────────────

export function mapConfidenceToPercent(value?: number | null): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "";
  return `%${Math.round(value * 100)}`;
}

export function confidenceVariant(value?: number | null): "high" | "medium" | "low" {
  if (typeof value !== "number" || Number.isNaN(value)) return "low";
  if (value >= 0.75) return "high";
  if (value >= 0.45) return "medium";
  return "low";
}

export function isLowOcrConfidence(confidence?: number | null): boolean {
  return typeof confidence !== "number" || confidence < 0.2;
}

// ── Document Claims ─────────────────────────────────────────────────────────

export interface DisplayClaim {
  field: string;
  label: string;
  value: string;
  statusLabel: string;
  statusVariant: "success" | "warning" | "neutral" | "error" | "info";
  confidence?: number | null;
  isDetected: boolean;
  evidence?: Array<{ line_id?: string; line_no?: string; text_excerpt?: string }>;
}

const UNKNOWN_VALUES = new Set([
  "not_detected", "NOT_DETECTED", "n/a", "N/A", "unknown", "Unknown",
  "none", "None", "", "tespit edilemedi", "Tespit edilemedi",
]);

function isDetected(value: unknown): boolean {
  if (value == null) return false;
  const str = String(value).trim();
  return str.length > 0 && !UNKNOWN_VALUES.has(str) && !/^not_detected$/i.test(str);
}

export function mapDocumentClaims(claims: Array<Record<string, unknown>>): DisplayClaim[] {
  return claims.map((claim) => {
    const field = String(claim.field ?? "");
    const rawValue = claim.value;
    const detected = isDetected(rawValue);
    const displayValue = detected ? String(rawValue).trim() : "";
    const status = String(claim.status ?? "unknown");
    const mapped = mapClaimStatus(status);

    return {
      field,
      label: mapFieldLabel(field),
      value: displayValue,
      statusLabel: mapped.label,
      statusVariant: mapped.variant,
      confidence: typeof claim.confidence === "number" ? claim.confidence : null,
      isDetected: detected,
      evidence: Array.isArray(claim.evidence) ? claim.evidence as DisplayClaim["evidence"] : [],
    };
  });
}

// ── Source Cards ────────────────────────────────────────────────────────────

export interface DisplaySource {
  id: string;
  title: string;
  sourceType: string;
  claim: string;
  relevance: string;
  isVerified: boolean;
  citation: string;
  url?: string;
}

export function mapSourceCard(evidence: Record<string, unknown>, index: number): DisplaySource {
  const title = String(evidence.title ?? evidence.citation ?? evidence.source_id ?? `Kaynak ${index + 1}`).trim();
  const rawType = String(evidence.source_type ?? evidence.source_tier ?? "").trim();
  const sourceType = rawType || "Harici Kaynak";
  const claim = String(evidence.evidence_text ?? evidence.text ?? evidence.quote ?? "").trim();
  const retrieval = typeof evidence.retrieval_score === "number"
    ? mapConfidenceToPercent(evidence.retrieval_score as number)
    : typeof evidence.score === "number"
    ? mapConfidenceToPercent(evidence.score as number)
    : "";
  return {
    id: String(evidence.source_id ?? index),
    title,
    sourceType,
    claim,
    relevance: retrieval,
    isVerified: evidence.verified === true,
    citation: String(evidence.citation ?? "").trim(),
    url: evidence.url ? String(evidence.url).trim() : undefined,
  };
}

// ── Entity text helper ──────────────────────────────────────────────────────

export function entityDisplayText(entity: EntityItem): string {
  const text = entity.value ?? entity.normalized_value ?? entity.text ?? "";
  return String(text).trim();
}

export function entityIsKnown(entity: EntityItem): boolean {
  const text = entityDisplayText(entity);
  return text.length > 0 && !UNKNOWN_VALUES.has(text) && !/^not_detected$/i.test(text);
}

// ── Line normalization ──────────────────────────────────────────────────────

export function normalizeLine(line: FullAnalysisLine, index: number): FullAnalysisLine & { text: string } {
  return { ...line, text: line.text || line.ocr_text || line.latin_text || line.modern_text || `Satır ${index + 1}` };
}

// ── Progress Step Labels ────────────────────────────────────────────────────

export const PROGRESS_STEPS = [
  { key: "UPLOADING",      label: "Belge Hazırlanıyor", desc: "Dosya yükleniyor" },
  { key: "PREPROCESSING",  label: "OCR",                desc: "Metin tanıma çalışıyor" },
  { key: "OCR",            label: "OCR",                desc: "Metin tanıma çalışıyor" },
  { key: "TRANSLITERATION",label: "Dil Dönüşümü",       desc: "Latin yazıya çevriliyor" },
  { key: "MODERNIZATION",  label: "Dil Dönüşümü",       desc: "Günümüz Türkçesine aktarılıyor" },
  { key: "ENTITY_ANALYSIS",label: "Analiz",              desc: "Varlıklar ve bilgiler çıkarılıyor" },
  { key: "HISTORICAL_RAG", label: "Analiz",              desc: "Tarihsel kaynaklar araştırılıyor" },
  { key: "COMPLETE",       label: "Tamamlandı",          desc: "Sonuç hazır" },
] as const;

// ── Modern Turkish confidence badge ────────────────────────────────────────

export function modernConfidenceBadge(result: FullDocumentAnalysisResponse): { label: string; tooltip: string; variant: "success" | "warning" | "neutral" } {
  if (result.confidence.combined_provisional) {
    return {
      label: "Geçici Sonuç",
      tooltip: "Metin düşük OCR güveni nedeniyle kesin sonuç olarak değerlendirilmemiştir.",
      variant: "warning",
    };
  }
  return {
    label: "Doğrulandı",
    tooltip: "Yeterli OCR güveniyle doğrulanmış sonuç.",
    variant: "success",
  };
}

// ── Image processing status label ──────────────────────────────────────────

export function imageProcessingStatusLabel(ocrSafe: boolean, applied: string[]): { label: string; variant: "success" | "warning" | "neutral" } {
  if (ocrSafe || applied.includes("ocr_safe_final")) {
    return { label: "OCR İçin Hazır", variant: "success" };
  }
  if (applied.length > 0) {
    return { label: "İşlendi", variant: "neutral" };
  }
  return { label: "Hazırlanmadı", variant: "warning" };
}
