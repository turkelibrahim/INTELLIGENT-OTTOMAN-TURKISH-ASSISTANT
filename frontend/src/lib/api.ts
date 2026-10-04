/**
 * API İstemcisi — Backend ile iletişim katmanı.
 * JWT token yönetimi, hata işleme ve tip güvenli istekler.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

/** Token yönetimi */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
}

export function setToken(token: string, remember: boolean = true): void {
  if (remember) {
    sessionStorage.removeItem("access_token");
    localStorage.setItem("access_token", token);
    return;
  }
  localStorage.removeItem("access_token");
  sessionStorage.setItem("access_token", token);
}

export function removeToken(): void {
  localStorage.removeItem("access_token");
  sessionStorage.removeItem("access_token");
}

/** API Hata sınıfı */
export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

/** Temel fetch wrapper */
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  retries = 1,
  timeoutMs = 15000
): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    ...options.headers,
  };

  if (!(options.body instanceof FormData)) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      cache: "no-store",
      ...options,
      headers,
      signal: controller.signal,
    });
  } catch (error) {
    clearTimeout(timeoutId);
    if (retries > 0 && (error instanceof TypeError || (error as Error).name === "AbortError")) {
      return request<T>(endpoint, options, retries - 1, timeoutMs);
    }
    if ((error as Error).name === "AbortError") {
      throw new ApiError(408, "İstek zaman aşımına uğradı");
    }
    throw new ApiError(0, "Ağ hatası veya sunucuya ulaşılamıyor");
  } finally {
    clearTimeout(timeoutId);
  }

  // 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  // Hata yanıtları
  if (!response.ok) {
    let detail = "Bir hata oluştu";
    try {
      const errorBody = await response.json();
      if (typeof errorBody.detail === "string") {
        detail = errorBody.detail;
      } else if (Array.isArray(errorBody.detail)) {
        // Pydantic 422 validation hatalıarı: [{loc, msg, type}, ...]
        detail = errorBody.detail
          .map((e: { msg?: string; loc?: (string | number)[] }) => {
            const field = e.loc?.filter((l) => typeof l === "string" && l !== "body").join(".") || "";
            return field ? `${field}: ${e.msg}` : (e.msg || "Doğrulama hatası");
          })
          .join("; ");
      } else if (errorBody.message) {
        detail = errorBody.message;
      }
    } catch {
      detail = response.statusText || "Sunucu yanıt vermedi";
    }

    // 401 → Token geçersiz, çıkış yap (login/register sayfasında değilse)
    if (response.status === 401) {
      const isAuthEndpoint = endpoint.includes("/auth/login") || endpoint.includes("/auth/register");
      if (!isAuthEndpoint) {
        removeToken();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    }
    
    // 5xx errors retry
    if (response.status >= 500 && retries > 0) {
      return request<T>(endpoint, options, retries - 1, timeoutMs);
    }

    throw new ApiError(response.status, detail);
  }

  return response.json();
}

/** Yetki gerektiren dosya/gorsel endpoint'lerini tarayici blob URL'sine cevirir. */
export async function fetchAuthenticatedBlobUrl(url: string): Promise<string> {
  const token = getToken();
  const headers: HeadersInit = {};

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    cache: "no-store",
    headers,
  });

  if (!response.ok) {
    let detail = response.statusText || "Gorsel yuklenemedi";
    try {
      const errorBody = await response.json();
      if (typeof errorBody.detail === "string") {
        detail = errorBody.detail;
      }
    } catch {
      // Binary olmayan hata yaniti yoksa statusText yeterli.
    }
    throw new ApiError(response.status, detail);
  }

  return URL.createObjectURL(await response.blob());
}

// ============== Auth API ==============

export interface UserResponse {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: string;
  status: string;
  created_at: string;
  last_login_at: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export const authApi = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: { email: string; password: string }) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getMe: () => request<UserResponse>("/auth/me"),

  logout: () =>
    request<{ message: string }>("/auth/logout", { method: "POST" }),

  updateProfile: (data: { full_name?: string; current_password?: string; new_password?: string }) =>
    request<UserResponse>("/auth/me", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  getMyStats: () =>
    request<{
      total_documents: number;
      favorite_documents: number;
      archived_documents: number;
      member_since: string | null;
      last_login: string | null;
    }>("/auth/me/stats"),
};

// ============== Documents API ==============

export interface DocumentResponse {
  id: number;
  user_id: number;
  title: string;
  description: string | null;
  source: string | null;
  period: string | null;
  original_filename: string;
  file_size: number;
  mime_type: string;
  page_count: number;
  status: string;
  is_favorite: boolean;
  access_level: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: DocumentResponse[];
  total: number;
  page: number;
  page_size: number;
}

export const documentsApi = {
  list: (params?: { page?: number; page_size?: number; search?: string; status_filter?: string; is_favorite?: boolean }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.page_size) searchParams.set("page_size", String(params.page_size));
    if (params?.search) searchParams.set("search", params.search);
    if (params?.status_filter) searchParams.set("status_filter", params.status_filter);
    if (params?.is_favorite !== undefined) searchParams.set("is_favorite", String(params.is_favorite));
    const qs = searchParams.toString();
    return request<DocumentListResponse>(`/documents${qs ? `?${qs}` : ""}`);
  },

  get: (id: number) => request<DocumentResponse>(`/documents/${id}`),

  upload: (file: File, metadata: { title: string; description?: string; source?: string; period?: string }) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", metadata.title);
    if (metadata.description) formData.append("description", metadata.description);
    if (metadata.source) formData.append("source", metadata.source);
    if (metadata.period) formData.append("period", metadata.period);

    return request<DocumentResponse>("/documents", {
      method: "POST",
      body: formData,
    });
  },

  update: (id: number, data: Partial<{ title: string; description: string; source: string; period: string }>) =>
    request<DocumentResponse>(`/documents/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    request<void>(`/documents/${id}`, { method: "DELETE" }),

  toggleFavorite: (id: number) =>
    request<DocumentResponse>(`/documents/${id}/favorite`, { method: "PATCH" }),

  toggleArchive: (id: number) =>
    request<DocumentResponse>(`/documents/${id}/archive`, { method: "PATCH" }),

  getResult: (id: number) =>
    request<FullDocumentAnalysisResponse>(`/documents/${id}/result`),
};

// ============== Full Document Analysis API ==============

export type AnalysisStage =
  | "IDLE"
  | "UPLOADING"
  | "PREPROCESSING"
  | "OCR"
  | "TRANSLITERATION"
  | "MODERNIZATION"
  | "ENTITY_ANALYSIS"
  | "HISTORICAL_RAG"
  | "COMPLETE"
  | "ERROR";

export interface FullAnalysisLine {
  line_id?: string;
  ocr_result_id?: number | null;
  page_id?: number | string | null;
  page_no?: number | null;
  line_no?: number | null;
  ocr_text?: string;
  latin_text?: string;
  modern_text?: string;
  text?: string;
  confidence?: number | null;
  bbox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  } | null;
  source?: string;
}

export interface EntityItem {
  value?: string;
  normalized_value?: string | null;
  text?: string;
  entity_type?: string;
  confidence_score?: number | null;
  start_offset?: number | null;
  end_offset?: number | null;
  metadata?: Record<string, unknown>;
}

export interface FullDocumentAnalysisResponse {
  document: {
    filename: string;
    document_type: string;
    language: string;
    document_id?: number | null;
    page_count: number;
  };
  image_processing: {
    applied: string[];
    ocr_safe_image: string;
    warnings: string[];
  };
  ocr: {
    ottoman_text: string;
    confidence: number;
    engine: string;
    fallback_used: boolean;
    lines: FullAnalysisLine[];
  };
  glossary?: unknown[];
  transliteration: {
    latin_text: string;
    confidence: number;
    method: string;
    lines: Array<Record<string, unknown>>;
    warnings: string[];
  };
  modern_turkish: {
    text: string;
    confidence: number;
    provider: string;
    lines: Array<Record<string, unknown>>;
    warnings: string[];
  };
  entities: {
    persons: EntityItem[];
    places: EntityItem[];
    institutions: EntityItem[];
    dates: EntityItem[];
    titles: EntityItem[];
    document_marks: EntityItem[];
  };
  historical_analysis: {
    possible_period: string;
    possible_sultan_period: string;
    possible_author: string;
    possible_institution: string;
    document_type: string;
    historical_context: string;
    confidence: number;
    provisional: boolean;
  };
  evidence: {
    document_evidence: Array<Record<string, unknown>>;
    historical_external_evidence: Array<Record<string, unknown>>;
    citations: Array<Record<string, unknown>>;
    model_inference: Array<Record<string, unknown>>;
    document_claims: Array<Record<string, unknown>>;
  };
  confidence: {
    ocr: number;
    transliteration: number;
    modern_turkish: number;
    entities: number;
    retrieval_strength: number;
    evidence_coverage: number;
    combined?: number | null;
    combined_provisional: boolean;
  };
  uncertainties: string[];
  warnings: string[];
}

export interface AnalysisJobResponse {
  job_id: number;
  document_id?: number | null;
  status: string;
  progress: number;
  current_stage?: string | null;
  created_at?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  result_url?: string | null;
}

function parseApiErrorPayload(body: unknown, fallback: string): string {
  if (!body || typeof body !== "object") return fallback;
  const payload = body as { detail?: unknown; message?: unknown };
  if (typeof payload.detail === "string") return payload.detail;
  if (Array.isArray(payload.detail)) {
    return payload.detail
      .map((item) => {
        if (!item || typeof item !== "object") return "Doğrulama hatası";
        const error = item as { msg?: string; loc?: (string | number)[] };
        const field = error.loc?.filter((part) => typeof part === "string" && part !== "body").join(".") || "";
        return field ? `${field}: ${error.msg}` : (error.msg || "Doğrulama hatası");
      })
      .join("; ");
  }
  if (typeof payload.message === "string") return payload.message;
  return fallback;
}

export const analysisApi = {
  analyze: (
    file: File,
    metadata: { title: string; description?: string },
    onUploadProgress?: (percent: number) => void
  ) =>
    new Promise<AnalysisJobResponse>((resolve, reject) => {
      const token = getToken();
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", metadata.title);
      if (metadata.description) formData.append("description", metadata.description);

      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_BASE_URL}/document/analyze`);
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);

      xhr.upload.onprogress = (event) => {
        if (!event.lengthComputable) return;
        onUploadProgress?.(Math.round((event.loaded / event.total) * 100));
      };

      xhr.onload = () => {
        let payload: unknown = null;
        try {
          payload = xhr.responseText ? JSON.parse(xhr.responseText) : null;
        } catch {
          payload = null;
        }

        if (xhr.status === 202 || (xhr.status >= 200 && xhr.status < 300)) {
          resolve(payload as AnalysisJobResponse);
          return;
        }

        const detail = parseApiErrorPayload(payload, xhr.statusText || "Analiz kuyruğa alınamadı");
        if (xhr.status === 401) removeToken();
        reject(new ApiError(xhr.status, detail));
      };

      xhr.onerror = () => reject(new ApiError(0, "Backend bağlantısı kurulamadı"));
      xhr.ontimeout = () => reject(new ApiError(0, "Analiz başlatma isteği zaman aşımına uğradı"));
      xhr.timeout = 30000;
      xhr.send(formData);
    }),

  getJob: (jobId: number) =>
    request<AnalysisJobResponse>(`/document/jobs/${jobId}`, {}, 0, 10000),

  getJobResult: (jobId: number) =>
    request<FullDocumentAnalysisResponse>(`/document/jobs/${jobId}/result`, {}, 0, 30000),

  analyzeFull: (
    file: File,
    metadata: { title: string; description?: string },
    onUploadProgress?: (percent: number) => void
  ) =>
    new Promise<FullDocumentAnalysisResponse>((resolve, reject) => {
      const token = getToken();
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", metadata.title);
      if (metadata.description) formData.append("description", metadata.description);

      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_BASE_URL}/document/analyze-full`);
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);

      xhr.upload.onprogress = (event) => {
        if (!event.lengthComputable) return;
        onUploadProgress?.(Math.round((event.loaded / event.total) * 100));
      };

      xhr.onload = () => {
        let payload: unknown = null;
        try {
          payload = xhr.responseText ? JSON.parse(xhr.responseText) : null;
        } catch {
          payload = null;
        }

        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(payload as FullDocumentAnalysisResponse);
          return;
        }

        const detail = parseApiErrorPayload(payload, xhr.statusText || "Analiz isteği başarısız oldu");
        if (xhr.status === 401) removeToken();
        reject(new ApiError(xhr.status, detail));
      };

      xhr.onerror = () => reject(new ApiError(0, "Backend bağlantısı kurulamadı"));
      xhr.ontimeout = () => reject(new ApiError(0, "Analiz isteği zaman aşımına uğradı"));
      xhr.timeout = 240000;
      xhr.send(formData);
    }),
};

// ============== OCR Review API ==============

export interface OCRCorrectionResponse {
  id: number;
  document_id: number;
  page_id?: number | null;
  ocr_result_id?: number | null;
  version_type: string;
  text: string;
  previous_text?: string | null;
  created_at: string;
}

export const ocrReviewApi = {
  createCorrection: (ocrResultId: number, text: string, expectedPreviousText?: string) =>
    request<OCRCorrectionResponse>(`/ocr-review/ocr-results/${ocrResultId}/corrections`, {
      method: "POST",
      body: JSON.stringify({
        corrected_text: text,
        expected_previous_text: expectedPreviousText,
      }),
    }),
};



// ============== Pages API ==============

export interface PageResponse {
  id: number;
  document_id: number;
  page_no: number;
  original_path: string;
  thumbnail_path: string | null;
  width: number | null;
  height: number | null;
  status: string;
  created_at: string;
}

export interface PageListResponse {
  pages: PageResponse[];
  total: number;
}

export const pagesApi = {
  list: (documentId: number) =>
    request<PageListResponse>(`/documents/${documentId}/pages`),

  getImageUrl: (documentId: number, pageNo: number) =>
    `${API_BASE_URL}/documents/${documentId}/pages/${pageNo}/image`,

  getThumbnailUrl: (documentId: number, pageNo: number) =>
    `${API_BASE_URL}/documents/${documentId}/pages/${pageNo}/thumbnail`,
};

// ============== Preprocessing API ==============

export interface ImageVariantResponse {
  id: number;
  page_id: number;
  profile: string;
  parameters: Record<string, JsonValue>;
  quality_score: number | null;
  created_at: string;
}

type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

export interface OCRPipelineLine {
  id?: string;
  page_id?: string | number | null;
  text: string;
  confidence?: number | null;
  bbox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  } | number[] | null;
}

export interface CitationResponse {
  id?: number;
  page_id?: number | null;
  locator: string;
  text?: string | null;
  score?: number | null;
}

export interface OCRJobStatusResponse {
  status: string;
  job_id: number;
  result?: {
    pipeline_results?: {
      original_ocr_text?: string;
      transliterated_text?: string;
      modernized_text?: string;
      summary_text?: string;
      lines?: OCRPipelineLine[];
      image_width?: number;
      image_height?: number;
      ner_results?: Array<{
        word: string;
        entity_group: string;
      }>;
    };
    confidence_scores?: {
      preprocessing?: number;
      ocr?: number;
      translation?: number;
      ner?: number;
      overall?: number;
    };
  };
}

export const preprocessingApi = {
  preprocess: (pageId: number, data: { profile: string; params?: JsonValue }) =>
    request<ImageVariantResponse>(`/pages/${pageId}/preprocessing`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listVariants: (pageId: number) =>
    request<ImageVariantResponse[]>(`/pages/${pageId}/preprocessing/variants`),

  getVariantImageUrl: (pageId: number, variantId: number) =>
    `${API_BASE_URL}/pages/${pageId}/preprocessing/variants/${variantId}/image`,
    
  getStages: (pageId: number) =>
    request<{ document_id: number; page_no: number; stages: Record<string, unknown>[] }>(`/pages/${pageId}/preprocessing/stages`),

  getStageImageUrl: (pageId: number, stageId: string) =>
    `${API_BASE_URL}/pages/${pageId}/preprocessing/stages/${stageId}/image`,
};

// ============== OCR & NLP & Chat API ==============

export const ocrApi = {
  triggerJob: (documentId: number) =>
    request<{ job_id: number; status: string }>(`/documents/${documentId}/ocr`, { method: "POST" }),
    
  getJobStatus: (documentId: number) =>
    request<OCRJobStatusResponse>(`/documents/${documentId}/ocr/status`),
};

export const chatApi = {
  createSession: (documentId: number, title: string = "Yeni Sohbet") =>
    request<{ id: number; document_id: number; title: string }>(`/chat/sessions`, {
      method: "POST",
      body: JSON.stringify({ document_id: documentId, title })
    }),
    
  sendMessage: (sessionId: number, content: string) =>
    request<{ role: string; content: string; citations: CitationResponse[] }>(`/chat/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content })
    })
};

// ============== Ground Truth API ==============

export interface GroundTruthDataset {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  status: string;
  version: string;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface GroundTruthPage {
  id: number;
  dataset_id: number;
  document_id: number | null;
  page_id: number | null;
  original_image_hash: string;
  image_width?: number | null;
  image_height?: number | null;
  metadata_json?: Record<string, unknown> | null;
  split_type: string;
  annotation_status: "DRAFT" | "IN_REVIEW" | "REVIEWED" | "REVIEWED_READY_TO_LOCK" | "LOCKED" | "REJECTED";
  created_at: string;
  updated_at: string;
}

export interface GroundTruthLine {
  id?: number;
  page_id?: number;
  bounding_box: number[];
  reading_order: number;
  text_content: string;
  draft_text?: string | null;
  text_reviewed?: boolean;
  bbox_reviewed?: boolean;
  text_changed?: boolean;
  bbox_changed?: boolean;
  status?: "DRAFT" | "IN_REVIEW" | "REVIEWED" | "REVIEWED_READY_TO_LOCK" | "LOCKED" | "REJECTED";
  version?: number;
  created_at?: string;
  updated_at?: string;
}

export interface GroundTruthProgress {
  dataset_id: number;
  dataset_status: string;
  annotation_status: string;
  total_lines: number;
  text_reviewed: number;
  bbox_reviewed: number;
  corrected: number;
  pending: number;
  percent: number;
  pages: Array<{
    page_id: number;
    source_page_id: string | null;
    total: number;
    text_reviewed: number;
    bbox_reviewed: number;
    status: string;
  }>;
}

export const groundTruthApi = {
  listDatasets: () => request<GroundTruthDataset[]>("/ground-truth/datasets"),

  importPilotDraft: () =>
    request<{ dataset: GroundTruthDataset; progress: GroundTruthProgress; created: boolean }>("/ground-truth/pilot-draft/import", {
      method: "POST",
    }),

  createDataset: (data: { name: string; description?: string }) => {
    const params = new URLSearchParams({ name: data.name });
    if (data.description) params.set("description", data.description);
    return request<GroundTruthDataset>(`/ground-truth/datasets?${params.toString()}`, { method: "POST" });
  },

  getDataset: (datasetId: number) =>
    request<GroundTruthDataset>(`/ground-truth/datasets/${datasetId}`),

  listPages: (datasetId: number) =>
    request<GroundTruthPage[]>(`/ground-truth/datasets/${datasetId}/pages`),

  addPage: (datasetId: number, data: { original_image_hash: string; document_id?: number; page_id?: number; split_type?: string }) => {
    const params = new URLSearchParams({
      original_image_hash: data.original_image_hash,
      split_type: data.split_type || "test",
    });
    if (data.document_id) params.set("document_id", String(data.document_id));
    if (data.page_id) params.set("page_id", String(data.page_id));
    return request<GroundTruthPage>(`/ground-truth/datasets/${datasetId}/pages?${params.toString()}`, { method: "POST" });
  },

  listLines: (pageId: number) =>
    request<GroundTruthLine[]>(`/ground-truth/pages/${pageId}/lines`),

  getProgress: (datasetId: number) =>
    request<GroundTruthProgress>(`/ground-truth/datasets/${datasetId}/progress`),

  saveLines: (pageId: number, lines: GroundTruthLine[]) =>
    request<{ message: string; lines: GroundTruthLine[] }>(`/ground-truth/pages/${pageId}/lines`, {
      method: "POST",
      body: JSON.stringify(lines),
    }),

  lockPage: (pageId: number) =>
    request<{ message: string }>(`/ground-truth/pages/${pageId}/lock`, { method: "POST" }),

  reviewLine: (lineId: number, data: { text_content: string; bounding_box: number[]; text_reviewed: boolean; bbox_reviewed: boolean }) =>
    request<{ line: GroundTruthLine; progress: GroundTruthProgress }>(`/ground-truth/lines/${lineId}/review`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  readyToLock: (datasetId: number) =>
    request<{ message: string; progress: GroundTruthProgress }>(`/ground-truth/datasets/${datasetId}/ready-to-lock`, {
      method: "POST",
      body: JSON.stringify({ rights_confirmed: true }),
    }),

  lockDataset: (datasetId: number) =>
    request<{ message: string; job_id: number; progress: GroundTruthProgress }>(`/ground-truth/datasets/${datasetId}/lock`, { method: "POST" }),

  exportDataset: (datasetId: number, format: "json" | "txt") =>
    request<{ format: string; content: unknown }>(`/ground-truth/datasets/${datasetId}/export?format=${format}`),

  getPageImageBlobUrl: (pageId: number) =>
    fetchAuthenticatedBlobUrl(`${API_BASE_URL}/ground-truth/pages/${pageId}/image`),
};

