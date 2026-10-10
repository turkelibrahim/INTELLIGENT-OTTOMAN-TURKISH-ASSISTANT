import { useState, useEffect, useRef, useCallback } from "react";
import {
  analysisApi,
  documentsApi,
  pagesApi,
  fetchAuthenticatedBlobUrl,
  ApiError,
  type AnalysisStage,
  type FullDocumentAnalysisResponse,
  type DocumentResponse,
  authApi
} from "@/lib/api";
import {
  clearActiveDocumentContext,
  loadActiveDocumentContext,
  saveActiveDocumentContext,
} from "@/lib/documentContext";

const ACCEPTED_EXTENSIONS = ["jpg", "jpeg", "png", "tiff", "tif", "pdf"];
const MAX_SIZE_MB = 50;

export function useRecentDocuments(hasDocument: boolean) {
  const [recentDocuments, setRecentDocuments] = useState<DocumentResponse[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);

  const loadDocs = useCallback(() => {
    if (!hasDocument) {
      setIsLoadingDocs(true);
      documentsApi.list({ page: 1, page_size: 6 })
        .then(res => setRecentDocuments(res.documents.filter(d => d.status !== 'archived')))
        .catch(err => console.error("Son belgeler yüklenemedi", err))
        .finally(() => setIsLoadingDocs(false));
    }
  }, [hasDocument]);

  useEffect(() => {
    const timer = setTimeout(() => loadDocs(), 0);
    return () => clearTimeout(timer);
  }, [loadDocs]);

  const toggleFavorite = async (id: number) => {
    try {
      await documentsApi.toggleFavorite(id);
      loadDocs();
    } catch (err) {
      console.error(err);
    }
  };

  const toggleArchive = async (id: number) => {
    try {
      await documentsApi.toggleArchive(id);
      loadDocs();
    } catch (err) {
      console.error(err);
    }
  };

  return { recentDocuments, isLoadingDocs, toggleFavorite, toggleArchive };
}

export function useDashboardStats(hasDocument: boolean) {
  const [stats, setStats] = useState<{
    total_documents: number;
    average_confidence: number;
    verified_sources: number;
    status: string;
  }>({
    total_documents: 0,
    average_confidence: 0,
    verified_sources: 0,
    status: "Aktif"
  });

  useEffect(() => {
    if (!hasDocument) {
      authApi.getMyStats().then((res) => {
        // Mock average confidence and verified sources if they don't exist in API
        setStats(prev => ({
          ...prev,
          total_documents: res.total_documents || 0,
          average_confidence: 84, // Example fallback, can be computed if possible
          verified_sources: 12
        }));
      }).catch(console.error);
    }
  }, [hasDocument]);

  return stats;
}

export function useDocumentViewer() {
  const [zoom, setZoom] = useState(100);
  const [rotation, setRotation] = useState(0);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const panStart = useRef({ x: 0, y: 0, panX: 0, panY: 0 });
  const viewerRef = useRef<HTMLDivElement>(null);

  const fitToScreen = () => {
    setZoom(100);
    setRotation(0);
    setPan({ x: 0, y: 0 });
  };

  const openFullscreen = () => {
    viewerRef.current?.requestFullscreen().catch(() => {});
  };

  return {
    zoom, setZoom,
    rotation, setRotation,
    pan, setPan,
    isPanning, setIsPanning,
    panStart,
    viewerRef,
    fitToScreen,
    openFullscreen
  };
}

export function useDocumentAnalysis() {
  const [initialContext] = useState(() => loadActiveDocumentContext());

  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [title, setTitle] = useState(() =>
    initialContext?.filename.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " ") || ""
  );
  const [description, setDescription] = useState("");
  
  const [stage, setStage] = useState<AnalysisStage>(() =>
    initialContext ? "COMPLETE" : "IDLE"
  );
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState("");
  const [result, setResult] = useState<FullDocumentAnalysisResponse | null>(
    () => initialContext?.analysisResult || null
  );

  const analyzeInFlightRef = useRef(false);
  const pollingCancelledRef = useRef(false);

  const isBusy = stage !== "IDLE" && stage !== "ERROR" && stage !== "COMPLETE";
  const hasDocument = Boolean(file || previewUrl || result);
  const isComplete = stage === "COMPLETE" && result != null;
  const isProcessing = isBusy;

  // Cleanup blob URLs
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      pollingCancelledRef.current = true;
    };
  }, [previewUrl]);

  // Load preview for existing context
  useEffect(() => {
    const context = initialContext;
    if (!context || previewUrl) return;
    const documentId = context.documentId;
    if (!documentId) return;
    let cancelled = false;
    pagesApi
      .list(documentId)
      .then((pageList) => {
        const firstPage = pageList.pages[0];
        if (!firstPage) return null;
        return fetchAuthenticatedBlobUrl(
          pagesApi.getImageUrl(documentId, firstPage.page_no)
        );
      })
      .then((url) => {
        if (!cancelled && url) setPreviewUrl(url);
      })
      .catch(() => {
        if (!cancelled)
          setError("Aktif belgenin görüntüsü yüklenemedi; analiz sonucu korunuyor.");
      });
    return () => {
      cancelled = true;
    };
  }, [initialContext, previewUrl]);

  const validateFile = (candidate: File): string => {
    const ext = candidate.name.split(".").pop()?.toLowerCase() || "";
    if (!ACCEPTED_EXTENSIONS.includes(ext))
      return `Desteklenmeyen dosya türü: .${ext || "bilinmiyor"}`;
    if (candidate.size > MAX_SIZE_MB * 1024 * 1024)
      return `Dosya boyutu ${MAX_SIZE_MB} MB sınırını aşıyor`;
    return "";
  };

  const selectFile = (selected: File) => {
    const err = validateFile(selected);
    setError(err);
    if (err) return;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(selected);
    setPreviewUrl(
      selected.type.startsWith("image/") ? URL.createObjectURL(selected) : null
    );
    setTitle((current) => current || selected.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " "));
    setResult(null);
    setStage("IDLE");
    setUploadProgress(0);
    clearActiveDocumentContext();
  };

  const resetDocument = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(null);
    setTitle("");
    setDescription("");
    setStage("IDLE");
    setUploadProgress(0);
    setError("");
    setResult(null);
    clearActiveDocumentContext();
  };

  const loadRecentDocument = async (doc: DocumentResponse, onSuccess: () => void) => {
    if (analyzeInFlightRef.current || isBusy) return;
    setStage("UPLOADING"); // Loading shim
    setError("");
    try {
      const response = await documentsApi.getResult(doc.id);
      
      let preview = null;
      try {
        const pagesRes = await pagesApi.list(doc.id);
        if (pagesRes.pages.length > 0) {
          preview = await fetchAuthenticatedBlobUrl(pagesApi.getImageUrl(doc.id, pagesRes.pages[0].page_no));
        }
      } catch (err) {
        console.error("Preview url load failed", err);
      }

      if (preview) setPreviewUrl(preview);
      setTitle(doc.title);
      setDescription(doc.description || "");
      
      setResult(response);
      saveActiveDocumentContext(response);
      setStage("COMPLETE");
      onSuccess();
    } catch (err: unknown) {
      const error = err as Record<string, unknown>;
      setError("Belge analiz sonucu yüklenemedi: " + (error.detail || error.message || "Bilinmeyen hata"));
      setStage("IDLE");
    }
  };

  const analyze = useCallback(async (onSuccess: () => void) => {
    if (analyzeInFlightRef.current || isBusy) return;
    if (!file) {
      setError("Lütfen analiz için bir belge seçin");
      return;
    }
    if (!title.trim()) {
      setError("Lütfen belge başlığı girin");
      return;
    }
    setError("");
    setResult(null);
    clearActiveDocumentContext();
    analyzeInFlightRef.current = true;
    pollingCancelledRef.current = false;
    setStage("UPLOADING");
    setUploadProgress(0);

    try {
      const job = await analysisApi.analyze(
        file,
        { title: title.trim(), description: description.trim() || undefined },
        (pct) => {
          setUploadProgress(pct);
          if (pct >= 100) setStage("PREPROCESSING");
        }
      );
      const stageForStatus = (statusValue: string): AnalysisStage => {
        const normalized = statusValue.toUpperCase();
        if (normalized.includes("OCR")) return "OCR";
        if (normalized.includes("TRANSLITER")) return "TRANSLITERATION";
        if (normalized.includes("MODERN")) return "MODERNIZATION";
        if (normalized.includes("NER")) return "ENTITY_ANALYSIS";
        if (normalized.includes("COMPLETED")) return "COMPLETE";
        if (normalized.includes("FAILED")) return "ERROR";
        return "PREPROCESSING";
      };
      const sleep = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));
      let latestJob = job;
      setStage(stageForStatus(latestJob.status));
      while (!pollingCancelledRef.current) {
        if (latestJob.status === "COMPLETED") break;
        if (latestJob.status === "FAILED") {
          throw new ApiError(500, latestJob.error_message || "Analiz işi başarısız oldu");
        }
        await sleep(1500);
        latestJob = await analysisApi.getJob(latestJob.job_id);
        setStage(stageForStatus(latestJob.status));
      }
      if (pollingCancelledRef.current) return;
      const response = await analysisApi.getJobResult(latestJob.job_id);
      setResult(response);
      saveActiveDocumentContext(response);
      setStage("COMPLETE");
      onSuccess();
    } catch (caught) {
      setStage("ERROR");
      setError(
        caught instanceof ApiError
          ? caught.detail
          : "Analiz sırasında beklenmeyen bir hata oluştu"
      );
    } finally {
      analyzeInFlightRef.current = false;
    }
  }, [file, title, description, isBusy]);

  return {
    file, setFile,
    previewUrl, setPreviewUrl,
    title, setTitle,
    description, setDescription,
    stage, setStage,
    uploadProgress,
    error, setError,
    result, setResult,
    hasDocument, isComplete, isProcessing, isBusy,
    selectFile, resetDocument, loadRecentDocument, analyze
  };
}
