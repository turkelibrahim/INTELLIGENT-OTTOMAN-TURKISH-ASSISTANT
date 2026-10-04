import type { FullDocumentAnalysisResponse } from "@/lib/api";

const ACTIVE_DOCUMENT_CONTEXT_KEY = "active-document-context:v1";
const HISTORICAL_ANALYSIS_STORAGE_KEY = "historical-analysis:last-result";

export interface ActiveDocumentContext {
  documentId: number | null;
  pageId?: number | null;
  filename: string;
  analysisResult: FullDocumentAnalysisResponse;
  savedAt: string;
  source: "document-analyze-full";
}

function parseContext(raw: string | null): ActiveDocumentContext | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as ActiveDocumentContext;
    if (!parsed?.analysisResult?.document || !parsed.filename) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function loadActiveDocumentContext(): ActiveDocumentContext | null {
  if (typeof window === "undefined") return null;
  const current = parseContext(sessionStorage.getItem(ACTIVE_DOCUMENT_CONTEXT_KEY));
  if (current) return current;

  const historical = parseContextFromHistorical(sessionStorage.getItem(HISTORICAL_ANALYSIS_STORAGE_KEY));
  if (historical) {
    saveActiveDocumentContext(historical.analysisResult);
    return historical;
  }
  return null;
}

function parseContextFromHistorical(raw: string | null): ActiveDocumentContext | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as { result?: FullDocumentAnalysisResponse };
    if (!parsed?.result?.document) return null;
    return buildContext(parsed.result);
  } catch {
    return null;
  }
}

export function saveActiveDocumentContext(result: FullDocumentAnalysisResponse): ActiveDocumentContext | null {
  if (typeof window === "undefined") return null;
  const context = buildContext(result);
  try {
    const payload = JSON.stringify(context);
    sessionStorage.setItem(ACTIVE_DOCUMENT_CONTEXT_KEY, payload);
    sessionStorage.setItem(
      HISTORICAL_ANALYSIS_STORAGE_KEY,
      JSON.stringify({
        result,
        saved_at: context.savedAt,
        source: context.source,
      })
    );
  } catch {
    return null;
  }
  return context;
}

export function clearActiveDocumentContext(): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(ACTIVE_DOCUMENT_CONTEXT_KEY);
  sessionStorage.removeItem(HISTORICAL_ANALYSIS_STORAGE_KEY);
}

function buildContext(result: FullDocumentAnalysisResponse): ActiveDocumentContext {
  return {
    documentId: result.document.document_id ?? null,
    filename: result.document.filename,
    analysisResult: result,
    savedAt: new Date().toISOString(),
    source: "document-analyze-full",
  };
}
