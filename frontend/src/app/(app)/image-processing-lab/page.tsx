"use client";

import { type MouseEvent as ReactMouseEvent, type PointerEvent, type WheelEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ApiError,
  documentsApi,
  fetchAuthenticatedBlobUrl,
  getToken,
  pagesApi,
  preprocessingApi,
  type DocumentResponse,
  type ImageVariantResponse,
  type PageResponse,
} from "@/lib/api";
import { clearActiveDocumentContext, loadActiveDocumentContext } from "@/lib/documentContext";
import { AlertTriangle, FileText, Clock, Target, UploadCloud } from 'lucide-react';


const MAX_SIZE_MB = 50;
const ACCEPTED_EXTENSIONS = ["jpg", "jpeg", "png", "tiff", "tif", "pdf"];
const ACCEPTED_INPUT = ".jpg,.jpeg,.png,.tiff,.tif,.pdf";
const UNKNOWN = "N/A";

type StageKey =
  | "original"
  | "orientation"
  | "perspective"
  | "deskew"
  | "denoise"
  | "background"
  | "stain_detection"
  | "stain_removal"
  | "contrast_threshold"
  | "ocr_safe_final";

type LabStatus = "IDLE" | "LOADING_DOCUMENT" | "PROCESSING" | "COMPLETE" | "PARTIAL" | "ERROR";

type LabStage = {
  key: StageKey;
  order: string;
  title: string;
  status: "available" | "not_available";
  safeForOcr: boolean;
  imageUrl?: string | null;
  description: string;
  metadata: Record<string, string | number | null | undefined>;
  warnings: string[];
};

const MASK_LAYERS = [
  { key: "stain", label: "Leke Maskesi", className: "stain" },
  { key: "background", label: "Arka Plan Maskesi", className: "background" },
  { key: "uncertain", label: "Belirsiz Pikseller", className: "uncertain" },
  { key: "segmentation", label: "Segmentasyon Maskesi", className: "segmentation" },
  { key: "text", label: "Metin Bölgeleri", className: "text" },
] as const;

type MaskLayerKey = typeof MASK_LAYERS[number]["key"];

type ImageDimensions = { width: number; height: number };
type LoadedImageDimensions = ImageDimensions & { url: string };
type ViewerSize = { width: number; height: number };
type ViewerPan = { x: number; y: number };
type MaskBox = { x: number; y: number; width: number; height: number };
type MaskPolygon = { points: Array<[number, number]> };
type MaskLayerData = {
  boxes: MaskBox[];
  polygons: MaskPolygon[];
  rasterUrl?: string;
  rasterDimensions?: ImageDimensions;
};
type MaskLayerMap = Record<MaskLayerKey, MaskLayerData>;

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function numberFrom(value: unknown): number | null {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  return value;
}

function parseBox(value: unknown): MaskBox | null {
  if (Array.isArray(value) && value.length >= 4) {
    const [x, y, width, height] = value.map(numberFrom);
    if (x !== null && y !== null && width !== null && height !== null && width > 0 && height > 0) return { x, y, width, height };
    return null;
  }
  if (!isRecord(value)) return null;
  const x = numberFrom(value.x) ?? numberFrom(value.left) ?? numberFrom(value.x1);
  const y = numberFrom(value.y) ?? numberFrom(value.top) ?? numberFrom(value.y1);
  const width = numberFrom(value.width) ?? (numberFrom(value.x2) !== null && x !== null ? numberFrom(value.x2)! - x : null);
  const height = numberFrom(value.height) ?? (numberFrom(value.y2) !== null && y !== null ? numberFrom(value.y2)! - y : null);
  if (x === null || y === null || width === null || height === null || width <= 0 || height <= 0) return null;
  return { x, y, width, height };
}

function parseBoxList(value: unknown): MaskBox[] {
  if (!Array.isArray(value)) return [];
  return value.map(parseBox).filter((box): box is MaskBox => Boolean(box));
}

function parsePolygon(value: unknown): MaskPolygon | null {
  if (!Array.isArray(value)) return null;
  const points = value
    .map((point) => {
      if (!Array.isArray(point) || point.length < 2) return null;
      const x = numberFrom(point[0]);
      const y = numberFrom(point[1]);
      return x !== null && y !== null ? [x, y] as [number, number] : null;
    })
    .filter((point): point is [number, number] => Boolean(point));
  return points.length >= 3 ? { points } : null;
}

function parsePolygonList(value: unknown): MaskPolygon[] {
  if (!Array.isArray(value)) return [];
  return value.map(parsePolygon).filter((polygon): polygon is MaskPolygon => Boolean(polygon));
}

function firstArray(source: Record<string, unknown>, keys: string[]): unknown[] {
  for (const key of keys) {
    const value = source[key];
    if (Array.isArray(value)) return value;
  }
  return [];
}

function buildMaskLayers(parameters?: Record<string, unknown> | null): MaskLayerMap {
  const masks: MaskLayerMap = {
    stain: { boxes: [], polygons: [] },
    background: { boxes: [], polygons: [] },
    uncertain: { boxes: [], polygons: [] },
    segmentation: { boxes: [], polygons: [] },
    text: { boxes: [], polygons: [] },
  };
  if (!parameters) return masks;

  const nested = isRecord(parameters.masks) ? parameters.masks : {};
  const sources: Record<MaskLayerKey, Record<string, unknown>> = {
    stain: isRecord(nested.stain) ? nested.stain : parameters,
    background: isRecord(nested.background) ? nested.background : parameters,
    uncertain: isRecord(nested.uncertain) ? nested.uncertain : parameters,
    segmentation: isRecord(nested.segmentation) ? nested.segmentation : parameters,
    text: isRecord(nested.text) ? nested.text : parameters,
  };

  masks.stain.boxes = parseBoxList(firstArray(sources.stain, ["stain_boxes", "stain_regions", "boxes", "regions"]));
  masks.stain.polygons = parsePolygonList(firstArray(sources.stain, ["stain_polygons", "polygons"]));
  masks.background.boxes = parseBoxList(firstArray(sources.background, ["background_boxes", "background_regions", "boxes", "regions"]));
  masks.background.polygons = parsePolygonList(firstArray(sources.background, ["background_polygons", "polygons"]));
  masks.uncertain.boxes = parseBoxList(firstArray(sources.uncertain, ["uncertain_boxes", "uncertain_regions", "uncertain_pixels", "boxes", "regions"]));
  masks.uncertain.polygons = parsePolygonList(firstArray(sources.uncertain, ["uncertain_polygons", "polygons"]));
  masks.segmentation.boxes = parseBoxList(firstArray(sources.segmentation, ["segmentation_boxes", "layout_regions", "regions", "boxes"]));
  masks.segmentation.polygons = parsePolygonList(firstArray(sources.segmentation, ["segmentation_polygons", "polygons"]));
  masks.text.boxes = parseBoxList(firstArray(sources.text, ["text_regions", "line_boxes", "text_boxes", "regions", "boxes"]));
  masks.text.polygons = parsePolygonList(firstArray(sources.text, ["text_polygons", "polygons"]));

  return masks;
}

function display(value: unknown): string {
  if (value === null || value === undefined || value === "") return UNKNOWN;
  return String(value);
}

function formatBytes(value?: number | null): string {
  if (!value) return UNKNOWN;
  if (value < 1024 * 1024) return `${Math.round(value / 1024)} KB`;
  return `${(value / (1024 * 1024)).toFixed(2)} MB`;
}

function formatScore(value?: number | null): string {
  if (typeof value !== "number") return UNKNOWN;
  return `%${Math.round(value)}`;
}

function downloadObjectUrl(url: string | null, filename: string) {
  if (!url) return;
  const anchor = window.document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  anchor.click();
}

export default function ImageProcessingLabPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const pageRef = useRef<HTMLDivElement>(null);
  const [initialContext] = useState(() => loadActiveDocumentContext());

  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState(() => initialContext?.filename.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " ") || "");
  const [document, setDocument] = useState<DocumentResponse | null>(null);
  const [page, setPage] = useState<PageResponse | null>(null);
  const [variant, setVariant] = useState<ImageVariantResponse | null>(null);
  const [originalUrl, setOriginalUrl] = useState<string | null>(null);
  const [variantUrl, setVariantUrl] = useState<string | null>(null);
  const [backendStages, setBackendStages] = useState<LabStage[]>([]);
  const [cleanDigitalCopyUrl, setCleanDigitalCopyUrl] = useState<string | null>(null);
  const [selectedStage, setSelectedStage] = useState<StageKey>("00_original" as StageKey);
  const [labStatus, setLabStatus] = useState<LabStatus>("IDLE");
  const [error, setError] = useState("");
  const [networkEvidence, setNetworkEvidence] = useState<string[]>([]);
  const [contextLoaded, setContextLoaded] = useState(false);
  const [hasAnalysisContext, setHasAnalysisContext] = useState(() => Boolean(initialContext?.analysisResult));
  const [compareSplit, setCompareSplit] = useState(50);
  const [compareMode, setCompareMode] = useState<"slider" | "side_by_side">("slider");
  const [compareZoom, setCompareZoom] = useState(100);
  const [activeMasks, setActiveMasks] = useState<Record<MaskLayerKey, boolean>>({
    stain: false,
    background: false,
    uncertain: false,
    segmentation: false,
    text: false,
  });
  const [maskOpacity, setMaskOpacity] = useState(50);
  const maskLayers = useMemo(() => buildMaskLayers(variant?.parameters), [variant]);
  const hasAnyMaskData = useMemo(
    () => MASK_LAYERS.some((mask) => maskLayers[mask.key].boxes.length > 0 || maskLayers[mask.key].polygons.length > 0 || Boolean(maskLayers[mask.key].rasterUrl)),
    [maskLayers],
  );

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  useEffect(() => {
    const context = initialContext;
    if (!context?.documentId || contextLoaded || file || document) return;
    let cancelled = false;
    const loadExistingDocument = async () => {
      setContextLoaded(true);
      setLabStatus("LOADING_DOCUMENT");
      setError("");
      setTitle(context.filename.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " "));
      setNetworkEvidence(["Loaded active document context"]);
      try {
        const existingDocument = await documentsApi.get(context.documentId as number);
        const pageList = await pagesApi.list(existingDocument.id);
        const firstPage = pageList.pages[0];
        if (!firstPage) throw new Error("Aktif belge için sayfa bulunamadı.");
        const originalBlob = await fetchAuthenticatedBlobUrl(pagesApi.getImageUrl(existingDocument.id, firstPage.page_no));
        setNetworkEvidence((items) => [...items, `GET /api/v1/documents/${existingDocument.id}/pages/${firstPage.page_no}/image -> 200`]);

        setLabStatus("PROCESSING");
        const processed = await preprocessingApi.preprocess(firstPage.id, { profile: "temiz_baski" });
        const processedBlob = await fetchAuthenticatedBlobUrl(preprocessingApi.getVariantImageUrl(firstPage.id, processed.id));
        
        const manifest = await preprocessingApi.getStages(firstPage.id).catch(() => ({ stages: [] }));
        const fetchedStages: LabStage[] = [];
        let fetchedCleanCopyUrl: string | null = null;
        for (const s of manifest.stages || []) {
            let blobUrl = null;
            if (s.status === 'COMPLETED') {
                const url = preprocessingApi.getStageImageUrl(firstPage.id, String(s.id));
                blobUrl = await fetchAuthenticatedBlobUrl(url).catch(() => null);
                if (cancelled) return;
            }
            if (s.is_clean_copy) {
                fetchedCleanCopyUrl = blobUrl;
                continue;
            }
            fetchedStages.push({
                key: s.id as StageKey,
                order: String(s.order).padStart(2, '0'),
                title: String(s.label),
                status: s.status === 'COMPLETED' ? 'available' : 'not_available',
                safeForOcr: !!s.ocr_safe,
                imageUrl: blobUrl,
                description: s.status === 'COMPLETED' ? `Aşama: ${s.label}` : 'Bu aşama atlandı veya üretilmedi.',
                metadata: (s.metadata as Record<string, string | number | null | undefined>) || {},
                warnings: (s.warnings as string[]) || []
            });
        }
        
        if (cancelled) {
          URL.revokeObjectURL(originalBlob);
          URL.revokeObjectURL(processedBlob);
          return;
        }
        setDocument(existingDocument);
        setPage(firstPage);
        setVariant(processed);
        setOriginalUrl(originalBlob);
        setVariantUrl(processedBlob);
        setBackendStages(fetchedStages);
        setCleanDigitalCopyUrl(fetchedCleanCopyUrl);
        const targetSafeStage = fetchedStages.find(s => s.safeForOcr);
        setSelectedStage(targetSafeStage ? targetSafeStage.key : ("ocr_safe_final" as StageKey));
        setLabStatus("PARTIAL");
        setNetworkEvidence((items) => [...items, `POST /api/v1/pages/${firstPage.id}/preprocessing -> 200`, `GET /api/v1/pages/${firstPage.id}/preprocessing/variants/${processed.id}/image -> 200`, `GET /api/v1/pages/${firstPage.id}/preprocessing/stages -> 200`]);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError) setError(err.detail);
        else setError(err instanceof Error ? err.message : "Aktif belge laboratuvara yüklenemedi.");
        setLabStatus("ERROR");
      }
    };
    void loadExistingDocument();
    return () => {
      cancelled = true;
    };
  }, [document, file, initialContext, contextLoaded]);

  useEffect(() => {
    return () => {
      if (originalUrl) URL.revokeObjectURL(originalUrl);
      if (variantUrl) URL.revokeObjectURL(variantUrl);
    };
  }, [originalUrl, variantUrl]);

  const stages = useMemo<LabStage[]>(() => {
    if (backendStages.length > 0) return backendStages;
    
    // Fallback if no backend stages
    return [
      {
        key: "00_original" as StageKey,
        order: "00",
        title: "Original",
        status: originalUrl ? "available" : "not_available",
        safeForOcr: false,
        imageUrl: originalUrl,
        description: "Orijinal belge.",
        metadata: {},
        warnings: [],
      },
      {
        key: "01_grayscale" as StageKey,
        order: "01",
        title: "Grayscale",
        status: "not_available",
        safeForOcr: false,
        description: "Gri tonlamaya dönüştürme",
        metadata: {},
        warnings: [],
      },
      {
        key: "02_denoise" as StageKey,
        order: "02",
        title: "Denoise",
        status: "not_available",
        safeForOcr: false,
        description: "Gürültü azaltma",
        metadata: {},
        warnings: [],
      },
      {
        key: "03_deskew" as StageKey,
        order: "03",
        title: "Deskew",
        status: "not_available",
        safeForOcr: false,
        description: "Eğiklik düzeltme",
        metadata: {},
        warnings: [],
      },
      {
        key: "04_threshold" as StageKey,
        order: "04",
        title: "Threshold",
        status: "not_available",
        safeForOcr: false,
        description: "İkili (siyah/beyaz) dönüştürme",
        metadata: {},
        warnings: [],
      },
      {
        key: "05_segmentation" as StageKey,
        order: "05",
        title: "Segmentation",
        status: "not_available",
        safeForOcr: false,
        description: "Bölge tespiti",
        metadata: {},
        warnings: [],
      },
      {
        key: "06_final" as StageKey,
        order: "06",
        title: "Final",
        status: variantUrl ? "available" : "not_available",
        safeForOcr: true,
        imageUrl: variantUrl,
        description: "OCR güvenli final sonuç",
        metadata: {},
        warnings: [],
      },
    ];
  }, [backendStages, originalUrl, variantUrl]);

  const selectedIndex = stages.findIndex((stage) => stage.key === selectedStage);
  const availableStages = stages.filter((stage) => stage.status === "available");
  const selectedStageRecord = selectedIndex >= 0 ? stages[selectedIndex] : stages[0];
  const selected = selectedStageRecord?.status === "available"
    ? selectedStageRecord
    : availableStages.find((stage) => stage.key === "ocr_safe_final") || availableStages[0] || selectedStageRecord;
  const selectedAvailableIndex = availableStages.findIndex((stage) => stage.key === selected.key);
  const previousAvailableStage = availableStages[Math.max(0, selectedAvailableIndex - 1)] || availableStages[0];
  const nextAvailableStage = availableStages[Math.min(availableStages.length - 1, selectedAvailableIndex + 1)] || availableStages[availableStages.length - 1];
  const activeFilename = document?.original_filename || file?.name || initialContext?.filename || "";

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.tagName === "INPUT" || target?.tagName === "TEXTAREA" || target?.tagName === "SELECT") return;
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        if (previousAvailableStage) setSelectedStage(previousAvailableStage.key);
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        if (nextAvailableStage) setSelectedStage(nextAvailableStage.key);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [nextAvailableStage, previousAvailableStage]);

  const validateFile = (candidate: File): string => {
    const ext = candidate.name.split(".").pop()?.toLowerCase() || "";
    if (!ACCEPTED_EXTENSIONS.includes(ext)) return `Desteklenmeyen dosya türü: .${ext || "bilinmiyor"}`;
    if (candidate.size > MAX_SIZE_MB * 1024 * 1024) return `Dosya boyutu ${MAX_SIZE_MB} MB sınırını aşıyor`;
    return "";
  };

  const resetAnalysis = () => {
    clearActiveDocumentContext();
    setFile(null);
    setTitle("");
    setDocument(null);
    setPage(null);
    setVariant(null);
    setSelectedStage("original");
    setLabStatus("IDLE");
    setError("");
    setNetworkEvidence([]);
    if (originalUrl) URL.revokeObjectURL(originalUrl);
    if (variantUrl) URL.revokeObjectURL(variantUrl);
    setOriginalUrl(null);
    setVariantUrl(null);
    setBackendStages([]);
    setCleanDigitalCopyUrl(null);
    setContextLoaded(false);
    setHasAnalysisContext(false);
    if (fileRef.current) fileRef.current.value = "";
  };

  const handleFile = (candidate: File) => {
    const validation = validateFile(candidate);
    setError(validation);
    if (validation) {
      setLabStatus("ERROR");
      return;
    }
    setFile(candidate);
    clearActiveDocumentContext();
    setTitle(candidate.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " "));
    setDocument(null);
    setPage(null);
    setVariant(null);
    setSelectedStage("original");
    setLabStatus("IDLE");
    setNetworkEvidence([]);
    setContextLoaded(false);
    setHasAnalysisContext(false);
    if (originalUrl) URL.revokeObjectURL(originalUrl);
    if (variantUrl) URL.revokeObjectURL(variantUrl);
    setOriginalUrl(null);
    setVariantUrl(null);
    setBackendStages([]);
    setCleanDigitalCopyUrl(null);
  };

  const runLab = async () => {
    if (!file) {
      setError("İşlem aşamalarını görüntülemek için bir belge seçin.");
      return;
    }
    if (!title.trim()) {
      setError("Lütfen belge başlığı girin.");
      return;
    }
    setLabStatus("LOADING_DOCUMENT");
    setError("");
    setNetworkEvidence([]);
    try {
      const uploaded = await documentsApi.upload(file, { title: title.trim(), description: "Görüntü İşleme Laboratuvarı çalışması" });
      setNetworkEvidence((items) => [...items, "POST /api/v1/documents -> 201"]);

      const pageList = await pagesApi.list(uploaded.id);
      setNetworkEvidence((items) => [...items, `GET /api/v1/documents/${uploaded.id}/pages -> 200`]);
      const firstPage = pageList.pages[0];
      if (!firstPage) throw new Error("Yüklenen belge için sayfa bulunamadı.");

      const originalBlob = await fetchAuthenticatedBlobUrl(pagesApi.getImageUrl(uploaded.id, firstPage.page_no));
      setNetworkEvidence((items) => [...items, `GET /api/v1/documents/${uploaded.id}/pages/${firstPage.page_no}/image -> 200`]);

      setLabStatus("PROCESSING");
      const processed = await preprocessingApi.preprocess(firstPage.id, { profile: "temiz_baski" });
      setNetworkEvidence((items) => [...items, `POST /api/v1/pages/${firstPage.id}/preprocessing -> 200`]);
      const processedBlob = await fetchAuthenticatedBlobUrl(preprocessingApi.getVariantImageUrl(firstPage.id, processed.id));
      setNetworkEvidence((items) => [...items, `GET /api/v1/pages/${firstPage.id}/preprocessing/variants/${processed.id}/image -> 200`]);

      const manifest = await preprocessingApi.getStages(firstPage.id).catch(() => ({ stages: [] }));
      const fetchedStages: LabStage[] = [];
      let fetchedCleanCopyUrl: string | null = null;
      for (const s of manifest.stages || []) {
          let blobUrl = null;
          if (s.status === 'COMPLETED') {
              const url = preprocessingApi.getStageImageUrl(firstPage.id, String(s.id));
              blobUrl = await fetchAuthenticatedBlobUrl(url).catch(() => null);
          }
          if (s.is_clean_copy) {
              fetchedCleanCopyUrl = blobUrl;
              continue;
          }
          fetchedStages.push({
              key: s.id as StageKey,
              order: String(s.order).padStart(2, '0'),
              title: String(s.label),
              status: s.status === 'COMPLETED' ? 'available' : 'not_available',
              safeForOcr: !!s.ocr_safe,
              imageUrl: blobUrl,
              description: s.status === 'COMPLETED' ? `Aşama: ${s.label}` : 'Bu aşama atlandı veya üretilmedi.',
              metadata: (s.metadata as Record<string, string | number | null | undefined>) || {},
              warnings: (s.warnings as string[]) || []
          });
      }

      if (originalUrl) URL.revokeObjectURL(originalUrl);
      if (variantUrl) URL.revokeObjectURL(variantUrl);
      setDocument(uploaded);
      setPage(firstPage);
      setVariant(processed);
      setOriginalUrl(originalBlob);
      setVariantUrl(processedBlob);
      setBackendStages(fetchedStages);
      setCleanDigitalCopyUrl(fetchedCleanCopyUrl);
      const targetSafeStage = fetchedStages.find(s => s.safeForOcr);
      setSelectedStage(targetSafeStage ? targetSafeStage.key : ("ocr_safe_final" as StageKey));
      setLabStatus("PARTIAL");
    } catch (err) {
      if (err instanceof ApiError) setError(err.detail);
      else setError(err instanceof Error ? err.message : "Görüntü İşleme Laboratuvarı çalıştırılamadı.");
      setLabStatus("ERROR");
    }
  };

  const hasDocument = Boolean(file || document || (initialContext?.documentId && !error && labStatus !== "ERROR"));

  return (
    <main className="w-full min-h-[calc(100vh-64px)] p-4 lg:p-8 animate-in fade-in duration-700 flex flex-col" ref={pageRef}>
      
      {/* Hidden file input used by both states */}
      <input
        ref={fileRef}
        type="file"
        accept={ACCEPTED_INPUT}
        hidden
        onChange={(event) => {
          const selectedFile = event.target.files?.[0];
          if (selectedFile) handleFile(selectedFile);
        }}
      />

      {/* Header */}
      <header className="ota-page-header">
        <div>
          <h1 className="text-3xl font-serif font-bold text-[var(--ota-text)] flex items-center gap-3">
            Görüntü İşleme Laboratuvarı
            {labStatus === "PROCESSING" || labStatus === "LOADING_DOCUMENT" ? (
              <span className="text-xs px-2 py-1 bg-[var(--ota-gold)]/20 text-[var(--ota-gold)] rounded-full animate-pulse border border-[var(--ota-gold)]/30">İşleniyor...</span>
            ) : null}
          </h1>
          <p className="text-[var(--ota-text-muted)] text-sm mt-1">
            {activeFilename ? activeFilename : "Belge ön işleme ve OCR optimizasyonu"}
          </p>
        </div>
        {hasDocument && (
          <div className="flex flex-wrap gap-2">
             <button type="button" onClick={() => fileRef.current?.click()} className="px-4 py-2 bg-[var(--ota-bg-2)] border border-[var(--ota-border)] hover:border-[var(--ota-gold)]/50 hover:bg-[var(--ota-gold-dim)] text-[var(--ota-text)] rounded-lg text-sm transition-all font-medium">Başka Belge Seç</button>
             <button type="button" onClick={runLab} disabled={!file || labStatus === "LOADING_DOCUMENT" || labStatus === "PROCESSING"} className="px-4 py-2 bg-[var(--ota-gold)] text-[#0A202A] border border-[var(--ota-gold)] hover:bg-[var(--ota-gold)]/90 rounded-lg text-sm transition-all font-bold disabled:opacity-50">
               {labStatus === "PROCESSING" || labStatus === "LOADING_DOCUMENT" ? "İşleniyor..." : "Yeniden İşle"}
             </button>
             <button type="button" onClick={() => router.push("/dashboard")} className="px-4 py-2 bg-[var(--ota-bg-2)] border border-[var(--ota-border)] hover:bg-[var(--ota-bg)] text-[var(--ota-text)] rounded-lg text-sm transition-all font-medium">Ana Analize Dön</button>
          </div>
        )}
      </header>

      {error && (
        <div className="mb-6 p-4 bg-[var(--ota-ruby)]/10 border border-[var(--ota-ruby)]/30 text-[var(--ota-ruby)] rounded-xl text-sm flex items-center gap-2">
          <span><AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> {error}
        </div>
      )}

      {!hasDocument ? (
        // STATE 1: PREMIUM EMPTY STATE
        <section className="flex-1 glass-panel rounded-3xl border border-[var(--ota-border)] shadow-[var(--glass-shadow)] flex flex-col items-center justify-center p-12 text-center relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-[var(--ota-iznik-turquoise)]/5 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/3 pointer-events-none" />
          <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-[var(--ota-gold)]/5 rounded-full blur-[100px] translate-y-1/3 -translate-x-1/3 pointer-events-none" />
          
          <div 
            className="w-28 h-28 mb-8 rounded-full bg-[var(--ota-bg-2)] border border-[var(--ota-border)] flex items-center justify-center shadow-2xl group-hover:border-[var(--ota-gold)]/40 group-hover:scale-105 transition-all duration-500 cursor-pointer relative"
            onClick={() => fileRef.current?.click()}
          >
            <div className="absolute inset-0 rounded-full bg-[var(--ota-gold)]/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <span className="text-5xl relative z-10 drop-shadow-md"><FileText className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>
          </div>
          
          <h2 className="text-3xl font-bold text-[var(--ota-text)] mb-4">Yeni Belge Seç</h2>
          <p className="text-[var(--ota-text-muted)] mb-8 max-w-md text-base leading-relaxed">
            Yapay zeka tabanlı Osmanlıca belge analizine başlamak için görüntü veya PDF dosyanızı laboratuvara yükleyin.<br/><br/>
            <span className="inline-block px-3 py-1 bg-[var(--ota-bg-2)] rounded-lg text-xs font-mono border border-[var(--ota-border)] mt-2">PNG, JPG, TIFF veya PDF</span>
          </p>
          
          <button 
            onClick={() => fileRef.current?.click()} 
            className="px-8 py-4 bg-[var(--ota-gold)] text-[#0A202A] font-bold rounded-xl hover:bg-[var(--ota-gold)]/90 hover:-translate-y-1 transition-all duration-300 shadow-[0_8px_30px_rgba(198,163,74,0.3)] flex items-center gap-3"
          >
            <UploadCloud className="w-5 h-5" /> Bilgisayardan Yükle
          </button>
        </section>
      ) : (
        // STATE 2: ACTIVE STATE
        <div className="flex-1 flex flex-col lg:flex-row gap-6 min-h-0">
          
          {/* Main Viewer Area */}
          <section className="flex-1 glass-panel rounded-2xl border border-[var(--ota-border)] shadow-[var(--glass-shadow)] flex flex-col overflow-hidden bg-[var(--ota-surface-dark)]/90 min-h-[600px] lg:min-h-0">
            <BeforeAfterComparison
              originalUrl={originalUrl}
              variantUrl={selected.imageUrl || variantUrl}
              split={compareSplit}
              setSplit={setCompareSplit}
              mode={compareMode}
              setMode={setCompareMode}
              zoom={compareZoom}
              setZoom={setCompareZoom}
              activeMasks={activeMasks}
              maskOpacity={maskOpacity}
              maskLayers={maskLayers}
            />
          </section>

          {/* Right Control Panel */}
          <aside className="w-full lg:w-[380px] xl:w-[420px] flex-shrink-0 flex flex-col gap-6 lg:overflow-y-auto lg:pr-2 custom-scrollbar max-h-full">
            
            {/* Processing Steps (Stages) */}
            <article className="glass-panel p-5 rounded-2xl border border-[var(--ota-border)] shadow-[var(--glass-shadow)] bg-[var(--ota-surface)]">
              <header className="mb-4">
                <h2 className="text-sm font-bold text-[var(--ota-text)] uppercase tracking-wider flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--ota-gold)]"></span> İşlem Adımları
                </h2>
                {backendStages.length === 0 && (
                  <p className="text-xs text-[var(--ota-text-muted)] mt-2 italic bg-[var(--ota-bg-2)] p-2 rounded-lg border border-[var(--ota-border)]/50">
                    Bu belge için detaylı preprocessing verisi mevcut değil.
                  </p>
                )}
              </header>
              <div className="relative flex flex-col gap-0 py-2 pl-2">
                {/* Dikey çizgi (Pipeline connector) */}
                <div className="absolute left-[17px] top-6 bottom-6 w-px bg-[var(--ota-border)]/70"></div>
                
                {stages.map((stage) => {
                  const isActive = selectedStage === stage.key;
                  const isAvailable = stage.status === "available";
                  
                  // Extract time/metric if available from metadata
                  const time = stage.metadata?.processing_time_ms ? `${stage.metadata.processing_time_ms}ms` : null;
                  const metricConfidence = stage.metadata?.confidence ? `%${Math.round(Number(stage.metadata.confidence) * 100)}` : null;
                  const metric = stage.metadata?.metric ? String(stage.metadata.metric) : metricConfidence;

                  return (
                    <div key={stage.key} className="relative flex gap-3 items-stretch py-2 group">
                      {/* Durum noktası */}
                      <div className="relative z-10 flex-shrink-0 mt-3 flex justify-center w-5">
                        <div className={`w-4 h-4 rounded-full flex items-center justify-center border-2 transition-colors ${
                          isActive ? "border-[var(--ota-gold)] bg-[var(--ota-gold)] scale-110" :
                          isAvailable ? "border-[var(--ota-success)] bg-[var(--ota-surface)]" :
                          "border-[var(--ota-border)] bg-[var(--ota-bg-2)]"
                        }`}>
                          {isActive && <div className="w-1.5 h-1.5 rounded-full bg-[#0A202A]" />}
                        </div>
                      </div>
                      
                      {/* İçerik Kutusu */}
                      <button
                        onClick={() => isAvailable && setSelectedStage(stage.key)}
                        disabled={!isAvailable}
                        className={`flex-1 text-left rounded-xl border transition-all flex flex-col overflow-hidden ${
                          isActive 
                            ? "bg-[var(--ota-gold)]/10 border-[var(--ota-gold)]/50 shadow-sm ring-1 ring-[var(--ota-gold)]/30" 
                            : isAvailable
                              ? "bg-[var(--ota-bg-2)]/50 border-[var(--ota-border)] hover:border-[var(--ota-border-hover)] hover:bg-[var(--ota-bg-2)]"
                              : "bg-[var(--ota-bg)]/20 border-[var(--ota-border)]/30 opacity-60 cursor-not-allowed"
                        }`}
                      >
                        <div className="p-2.5 flex items-center gap-3">
                          {/* Thumbnail */}
                          {stage.imageUrl ? (
                            <div className="w-10 h-10 rounded-lg border border-[var(--ota-border)]/50 overflow-hidden bg-[var(--ota-bg)] flex-shrink-0 shadow-inner">
                               {/* eslint-disable-next-line @next/next/no-img-element */}
                               <img src={stage.imageUrl} alt={stage.title} className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity" />
                            </div>
                          ) : (
                            <div className="w-10 h-10 rounded-lg border border-[var(--ota-border)]/30 border-dashed bg-[var(--ota-bg-2)] flex items-center justify-center flex-shrink-0">
                               <span className="text-[10px] text-[var(--ota-text-muted)] font-mono">Yok</span>
                            </div>
                          )}

                          {/* Bilgi */}
                          <div className="flex-1 min-w-0 flex flex-col justify-center">
                            <div className="flex items-center justify-between gap-2">
                               <span className={`font-semibold text-xs truncate tracking-wide ${isActive ? "text-[var(--ota-gold)]" : isAvailable ? "text-[var(--ota-text)]" : "text-[var(--ota-text-muted)]"}`}>
                                 {stage.title}
                               </span>
                               {stage.safeForOcr && <span className="text-[8px] font-bold uppercase px-1.5 py-0.5 rounded-md bg-[var(--ota-success)]/10 text-[var(--ota-success)] border border-[var(--ota-success)]/20 shrink-0">OCR</span>}
                            </div>
                            
                            <div className="flex items-center gap-2 mt-1.5 text-[9px] text-[var(--ota-text-muted)] uppercase tracking-wider font-medium">
                               {!isAvailable ? (
                                 <span className="text-[var(--ota-text-muted)]/70 line-through decoration-[var(--ota-border)]">Atlandı / Yok</span>
                               ) : (
                                 <>
                                   <span className="text-[var(--ota-success)]">Kullanılabilir</span>
                                   {time && <span className="flex items-center gap-0.5 before:content-['•'] before:mr-2 before:text-[var(--ota-border)]"><span><Clock className="w-3 h-3" /></span> {time}</span>}
                                   {metric && <span className="flex items-center gap-0.5 before:content-['•'] before:mr-2 before:text-[var(--ota-border)]"><span><Target className="w-3 h-3" /></span> {metric}</span>}
                                 </>
                               )}
                            </div>
                          </div>
                        </div>
                      </button>
                    </div>
                  );
                })}
              </div>
            </article>

            {/* Metrics & Details for Selected Stage */}
            <article className="glass-panel p-5 rounded-2xl border border-[var(--ota-border)] shadow-[var(--glass-shadow)] bg-[var(--ota-surface)]">
              <header className="mb-4">
                <h2 className="text-sm font-bold text-[var(--ota-text)] uppercase tracking-wider flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--ota-iznik-turquoise)]"></span> Metrikler
                </h2>
              </header>
              {Object.keys(selected.metadata).length > 0 ? (
                <dl className="flex flex-col gap-3">
                  {Object.entries(selected.metadata).map(([key, value]) => (
                    <div key={key} className="flex justify-between items-center py-2 border-b border-[var(--ota-border)]/50 last:border-0">
                      <dt className="text-xs font-semibold text-[var(--ota-text-muted)]">{key}</dt>
                      <dd className="text-sm text-[var(--ota-text)] font-medium text-right max-w-[60%] truncate" title={display(value)}>{display(value)}</dd>
                    </div>
                  ))}
                </dl>
              ) : (
                <p className="text-xs text-[var(--ota-text-muted)] italic p-3 bg-[var(--ota-bg-2)]/50 rounded-lg text-center">Bu adım için ek metrik bulunmuyor.</p>
              )}
              {selected.warnings.length > 0 && (
                <div className="mt-4 flex flex-col gap-2">
                  {selected.warnings.map((warning, i) => (
                    <span key={i} className="text-xs p-2 bg-[var(--ota-ruby)]/10 text-[var(--ota-ruby)] border border-[var(--ota-ruby)]/20 rounded flex items-start gap-2">
                      <span><AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> {warning}
                    </span>
                  ))}
                </div>
              )}
            </article>

            {/* Mask Layers */}
            <article className="glass-panel p-5 rounded-2xl border border-[var(--ota-border)] shadow-[var(--glass-shadow)] bg-[var(--ota-surface)]">
              <header className="mb-4">
                <h2 className="text-sm font-bold text-[var(--ota-text)] uppercase tracking-wider flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--ota-sage)]"></span> Maske Katmanları
                </h2>
              </header>
              <div className="flex flex-col gap-2 mb-5">
                {MASK_LAYERS.map((mask) => {
                  const layer = maskLayers[mask.key];
                  const available = Boolean(layer.rasterUrl || layer.boxes.length || layer.polygons.length);
                  return (
                    <label
                      key={mask.key}
                      className={`flex items-center justify-between p-3 rounded-xl border transition-colors cursor-pointer ${
                        available 
                          ? (activeMasks[mask.key] ? "bg-[var(--ota-bg-2)] border-[var(--ota-sage)]/40" : "bg-[var(--ota-bg-2)]/50 border-[var(--ota-border)] hover:border-[var(--ota-border-hover)]") 
                          : "opacity-40 cursor-not-allowed bg-[var(--ota-bg)] border-transparent"
                      }`}
                      title={available ? mask.label : "Bu belge için üretilmedi."}
                    >
                      <div className="flex items-center gap-3">
                        <i className={`w-3 h-3 rounded-full shadow-sm ipl-mask-swatch ${mask.className}`} aria-hidden="true" />
                        <span className="text-sm font-medium text-[var(--ota-text)]">{mask.label}</span>
                      </div>
                      <input
                        type="checkbox"
                        className="w-4 h-4 rounded border-[var(--ota-border)] text-[var(--ota-sage)] focus:ring-[var(--ota-sage)] bg-[var(--ota-bg)]"
                        checked={available && activeMasks[mask.key]}
                        disabled={!available}
                        onChange={(event) => setActiveMasks((current) => ({ ...current, [mask.key]: event.target.checked }))}
                      />
                    </label>
                  );
                })}
              </div>
              
              <label className="flex flex-col gap-2">
                <div className="flex justify-between items-center text-xs font-semibold text-[var(--ota-text-muted)] uppercase">
                  <span>Opaklık</span>
                  <span className="text-[var(--ota-gold)]">%{maskOpacity}</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="100" 
                  value={maskOpacity} 
                  onChange={(event) => setMaskOpacity(Number(event.target.value))} 
                  className="w-full accent-[var(--ota-gold)] h-1.5 bg-[var(--ota-border)] rounded-full appearance-none outline-none"
                />
              </label>
            </article>

            {/* Diagnostics (Collapsible) */}
            <details className="glass-panel p-5 rounded-2xl border border-[var(--ota-border)] shadow-[var(--glass-shadow)] bg-[var(--ota-surface)] group">
              <summary className="text-sm font-bold text-[var(--ota-text-muted)] uppercase tracking-wider flex items-center justify-between cursor-pointer list-none select-none">
                <span className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[var(--ota-text-muted)] group-open:bg-[var(--ota-text)] transition-colors"></span> Teknik Tanılama</span>
                <span className="group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="pt-4 mt-2 border-t border-[var(--ota-border)]/50">
                {networkEvidence.length ? (
                  <ul className="flex flex-col gap-1.5">
                    {networkEvidence.map((item, index) => (
                      <li key={index} className="text-[10px] font-mono text-[var(--ota-text-2)] p-1.5 bg-[var(--ota-bg-2)] rounded border border-[var(--ota-border)] break-all">{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-[var(--ota-text-muted)] italic">Ağ istek logları burada görünür.</p>
                )}
              </div>
            </details>

          </aside>
        </div>
      )}
    </main>
  );
}

function ImageViewer({ imageUrl, label, emptyText }: { imageUrl: string | null; label: string; emptyText: string }) {
  const frameRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(100);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const isPanningRef = useRef(false);
  const start = useRef({ x: 0, y: 0, panX: 0, panY: 0 });

  const reset = () => {
    setZoom(100);
    setPan({ x: 0, y: 0 });
  };

  const beginPan = (clientX: number, clientY: number) => {
    if (!imageUrl) return;
    setIsPanning(true);
    isPanningRef.current = true;
    start.current = { x: clientX, y: clientY, panX: pan.x, panY: pan.y };
  };

  const movePan = (clientX: number, clientY: number) => {
    if (!isPanningRef.current) return;
    setPan({
      x: start.current.panX + clientX - start.current.x,
      y: start.current.panY + clientY - start.current.y,
    });
  };

  const endPan = () => {
    isPanningRef.current = false;
    setIsPanning(false);
  };

  const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    beginPan(event.clientX, event.clientY);
    if (imageUrl) event.currentTarget.setPointerCapture(event.pointerId);
  };

  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    movePan(event.clientX, event.clientY);
  };

  const onMouseDown = (event: ReactMouseEvent<HTMLDivElement>) => {
    beginPan(event.clientX, event.clientY);
  };

  const onMouseMove = (event: ReactMouseEvent<HTMLDivElement>) => {
    movePan(event.clientX, event.clientY);
  };

  const onWheel = (event: WheelEvent<HTMLDivElement>) => {
    if (!imageUrl) return;
    event.preventDefault();
    setZoom((value) => Math.max(50, Math.min(300, value + (event.deltaY < 0 ? 10 : -10))));
  };

  return (
    <div className="ipl-viewer-shell">
      <div
        ref={frameRef}
        className={`ipl-stage-view ${isPanning ? "panning" : ""}`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endPan}
        onPointerCancel={endPan}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={endPan}
        onMouseLeave={endPan}
        onWheel={onWheel}
      >
        {imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={imageUrl} alt={label} style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom / 100})` }} draggable={false} />
        ) : (
          <div className="ipl-empty">{emptyText}</div>
        )}
      </div>
      <div className="ipl-viewer-actions">
        <button type="button" onClick={() => setZoom((value) => Math.max(50, value - 25))} disabled={!imageUrl} aria-label="Uzaklaştır">-</button>
        <button type="button" onClick={() => setZoom((value) => Math.min(300, value + 25))} disabled={!imageUrl} aria-label="Yakınlaştır">+</button>
        <button type="button" onClick={() => { setZoom(100); setPan({ x: 0, y: 0 }); }} disabled={!imageUrl} aria-label="Yüzde yüz">100%</button>
        <button type="button" onClick={reset} disabled={!imageUrl} aria-label="Sığdır">Sığdır</button>
        <button type="button" onClick={reset} disabled={!imageUrl} aria-label="Sıfırla">Sıfırla</button>
        <button type="button" onClick={() => setPan((value) => ({ x: value.x + 40, y: value.y }))} disabled={!imageUrl} aria-label="Sağa kaydır">Kaydır</button>
        <button type="button" onClick={() => frameRef.current?.requestFullscreen()} disabled={!imageUrl} aria-label="Tam ekran">Tam</button>
        <span>%{zoom}</span>
      </div>
    </div>
  );
}

function BeforeAfterComparison({
  originalUrl,
  variantUrl,
  split,
  setSplit,
  mode,
  setMode,
  zoom,
  setZoom,
  activeMasks,
  maskOpacity,
  maskLayers,
}: {
  originalUrl: string | null;
  variantUrl: string | null;
  split: number;
  setSplit: (value: number) => void;
  mode: "slider" | "side_by_side";
  setMode: (value: "slider" | "side_by_side") => void;
  zoom: number;
  setZoom: (value: number) => void;
  activeMasks: Record<MaskLayerKey, boolean>;
  maskOpacity: number;
  maskLayers: MaskLayerMap;
}) {
  const frameRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<"pan" | "slider" | null>(null);
  const panStartRef = useRef({ x: 0, y: 0, panX: 0, panY: 0 });
  const hasImages = Boolean(originalUrl && variantUrl);
  const [viewport, setViewport] = useState<ViewerSize>({ width: 0, height: 0 });
  const [loadedOriginalDimensions, setLoadedOriginalDimensions] = useState<LoadedImageDimensions | null>(null);
  const [loadedVariantDimensions, setLoadedVariantDimensions] = useState<LoadedImageDimensions | null>(null);
  const [pan, setPan] = useState<ViewerPan>({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);

  useEffect(() => {
    const node = frameRef.current;
    if (!node) return;
    const updateViewport = () => {
      const rect = node.getBoundingClientRect();
      setViewport({ width: rect.width, height: rect.height });
    };
    updateViewport();
    const observer = new ResizeObserver(updateViewport);
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const originalDimensions = loadedOriginalDimensions?.url === originalUrl ? loadedOriginalDimensions : null;
  const variantDimensions = loadedVariantDimensions?.url === variantUrl ? loadedVariantDimensions : null;

  const sameGeometry = Boolean(
    originalDimensions
    && variantDimensions
    && originalDimensions.width === variantDimensions.width
    && originalDimensions.height === variantDimensions.height,
  );

  useEffect(() => {
    if (mode === "slider" && originalDimensions && variantDimensions && !sameGeometry) setMode("side_by_side");
  }, [mode, originalDimensions, variantDimensions, sameGeometry, setMode]);

  const fitScale = useMemo(() => {
    if (!originalDimensions || viewport.width <= 0 || viewport.height <= 0) return 1;
    return Math.min(viewport.width / originalDimensions.width, viewport.height / originalDimensions.height);
  }, [originalDimensions, viewport.height, viewport.width]);

  const renderScale = fitScale * (zoom / 100);
  const renderedWidth = (originalDimensions?.width || 0) * renderScale;
  const renderedHeight = (originalDimensions?.height || 0) * renderScale;
  const offsetX = Math.round((viewport.width - renderedWidth) / 2 + pan.x);
  const offsetY = Math.round((viewport.height - renderedHeight) / 2 + pan.y);
  const selectedMasks = MASK_LAYERS.filter((mask) => activeMasks[mask.key] && (maskLayers[mask.key].boxes.length || maskLayers[mask.key].polygons.length || maskLayers[mask.key].rasterUrl));

  const clampPan = useCallback((next: ViewerPan): ViewerPan => {
    if (!originalDimensions || viewport.width <= 0 || viewport.height <= 0) return next;
    const imageWidth = originalDimensions.width * renderScale;
    const imageHeight = originalDimensions.height * renderScale;
    const maxX = Math.max(0, (imageWidth - viewport.width) / 2 + viewport.width * 0.15);
    const maxY = Math.max(0, (imageHeight - viewport.height) / 2 + viewport.height * 0.15);
    return {
      x: Math.max(-maxX, Math.min(maxX, next.x)),
      y: Math.max(-maxY, Math.min(maxY, next.y)),
    };
  }, [originalDimensions, renderScale, viewport.height, viewport.width]);

  const resetViewer = () => {
    setZoom(100);
    setPan({ x: 0, y: 0 });
    setSplit(50);
  };

  const updateSplitFromPointer = (clientX: number) => {
    const rect = frameRef.current?.getBoundingClientRect();
    if (!rect) return;
    const next = ((clientX - rect.left) / rect.width) * 100;
    setSplit(Math.max(0, Math.min(100, Math.round(next))));
  };

  const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    if (!hasImages || event.button !== 0) return;
    const target = event.target as HTMLElement;
    if (target.closest("[data-compare-slider]")) {
      dragRef.current = "slider";
      updateSplitFromPointer(event.clientX);
    } else {
      dragRef.current = "pan";
      setIsPanning(true);
      panStartRef.current = { x: event.clientX, y: event.clientY, panX: pan.x, panY: pan.y };
    }
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (!dragRef.current) return;
    if (dragRef.current === "slider") {
      updateSplitFromPointer(event.clientX);
      return;
    }
    setPan(clampPan({
      x: panStartRef.current.panX + event.clientX - panStartRef.current.x,
      y: panStartRef.current.panY + event.clientY - panStartRef.current.y,
    }));
  };

  const endPointer = () => {
    dragRef.current = null;
    setIsPanning(false);
  };

  const onWheel = (event: WheelEvent<HTMLDivElement>) => {
    if (!hasImages) return;
    event.preventDefault();
    setZoom(Math.max(50, Math.min(500, zoom + (event.deltaY < 0 ? 10 : -10))));
  };

  const renderMaskOverlay = () => {
    if (!originalDimensions || selectedMasks.length === 0) return null;
    return (
      <svg
        className="ipl-mask-overlay"
        viewBox={`0 0 ${originalDimensions.width} ${originalDimensions.height}`}
        width={originalDimensions.width}
        height={originalDimensions.height}
        style={{ opacity: maskOpacity / 100 }}
        aria-hidden="true"
      >
        {selectedMasks.map((mask) => {
          const layer = maskLayers[mask.key];
          return (
            <g className={mask.className} key={mask.key}>
              {layer.boxes.map((box, index) => <rect key={`box-${index}`} x={box.x} y={box.y} width={box.width} height={box.height} rx="2" />)}
              {layer.polygons.map((polygon, index) => <polygon key={`polygon-${index}`} points={polygon.points.map(([x, y]) => `${x},${y}`).join(" ")} />)}
            </g>
          );
        })}
      </svg>
    );
  };

  const transformStyle = originalDimensions ? {
    left: `${offsetX}px`,
    top: `${offsetY}px`,
    width: `${originalDimensions.width}px`,
    height: `${originalDimensions.height}px`,
    transform: `scale(${renderScale})`,
  } : undefined;

  return (
    <div className="flex flex-col h-full bg-[var(--ota-surface-dark)]/50">
      <header className="px-6 py-4 border-b border-[var(--ota-border)]/50 bg-[var(--ota-bg-2)]/30 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-[var(--ota-text)] uppercase tracking-wider flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--ota-gold)]"></span> Önizleme
          </h2>
          <p className="text-xs text-[var(--ota-text-muted)] mt-1">Orijinal ↔ İşlenmiş Görüntü (Değiştirmek için sağ panelden adım seçin)</p>
        </div>
        <div className="flex bg-[var(--ota-bg-2)] p-1 rounded-lg border border-[var(--ota-border)]" role="group" aria-label="Karşılaştırma modu">
          <button
            type="button"
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${mode === "slider" ? "bg-[var(--ota-gold)] text-[#0A202A]" : "text-[var(--ota-text-2)] hover:text-[var(--ota-text)]"}`}
            onClick={() => setMode("slider")}
            disabled={Boolean(originalDimensions && variantDimensions && !sameGeometry)}
            title={originalDimensions && variantDimensions && !sameGeometry ? "Geometri farkından dolayı kullanılamıyor." : "Slider (Kaydırıcı)"}
          >
            Slider
          </button>
          <button 
            type="button" 
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${mode === "side_by_side" ? "bg-[var(--ota-gold)] text-[#0A202A]" : "text-[var(--ota-text-2)] hover:text-[var(--ota-text)]"}`}
            onClick={() => setMode("side_by_side")}
          >
            Yan Yana
          </button>
        </div>
      </header>
      <div
        ref={frameRef}
        className={`relative flex-1 overflow-hidden ${mode} ${isPanning ? "cursor-grabbing" : "cursor-grab"}`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endPointer}
        onPointerCancel={endPointer}
        onWheel={onWheel}
      >
        {hasImages ? (
          <>
            {mode === "slider" && sameGeometry && transformStyle ? (
              <>
                <div className="ipl-transform-layer" style={transformStyle}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={originalUrl || ""} alt="Orijinal karşılaştırma" draggable={false} onLoad={(event) => setLoadedOriginalDimensions({ url: originalUrl || "", width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })} />
                  <div className="ipl-after-wrap" style={{ clipPath: `inset(0 ${100 - split}% 0 0)` }}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={variantUrl || ""} alt="OCR güvenli karşılaştırma" draggable={false} onLoad={(event) => setLoadedVariantDimensions({ url: variantUrl || "", width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })} />
                  </div>
                  {renderMaskOverlay()}
                </div>
                <div className="ipl-compare-divider" style={{ left: `${split}%` }} data-compare-slider aria-hidden="true"><span /></div>
                <input className="ipl-compare-slider" data-compare-slider type="range" min="0" max="100" value={split} onChange={(event) => setSplit(Number(event.target.value))} aria-label="Önce sonra sürgüsü" />
              </>
            ) : (
              <div className="ipl-side-by-side">
                <div className="ipl-side-pane">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={originalUrl || ""} alt="Orijinal yan yana" draggable={false} style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom / 100})` }} onLoad={(event) => setLoadedOriginalDimensions({ url: originalUrl || "", width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })} />
                </div>
                <div className="ipl-side-pane">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={variantUrl || ""} alt="OCR güvenli yan yana" draggable={false} style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom / 100})` }} onLoad={(event) => setLoadedVariantDimensions({ url: variantUrl || "", width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })} />
                </div>
              </div>
            )}
            {originalDimensions && variantDimensions && !sameGeometry && (
              <div className="ipl-geometry-warning">Bu iki görüntünün geometrileri farklı olduğu için slider karşılaştırması kullanılamıyor.</div>
            )}
          </>
        ) : (
          <div className="ipl-empty">Orijinal ve OCR güvenli sonuç üretildiğinde karşılaştırma burada görünür.</div>
        )}
      </div>
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-[var(--ota-bg-2)]/90 backdrop-blur-md p-1.5 rounded-xl border border-[var(--ota-border)] shadow-lg z-50">
        <button type="button" className="w-8 h-8 flex items-center justify-center rounded-lg bg-[var(--ota-bg)] border border-[var(--ota-border)] hover:border-[var(--ota-gold)]/50 hover:text-[var(--ota-gold)] transition-colors text-lg disabled:opacity-50" onClick={() => setZoom(Math.max(50, zoom - 25))} disabled={!hasImages} aria-label="Uzaklaştır">-</button>
        <span className="text-xs font-mono w-12 text-center text-[var(--ota-text)] font-semibold">%{zoom}</span>
        <button type="button" className="w-8 h-8 flex items-center justify-center rounded-lg bg-[var(--ota-bg)] border border-[var(--ota-border)] hover:border-[var(--ota-gold)]/50 hover:text-[var(--ota-gold)] transition-colors text-lg disabled:opacity-50" onClick={() => setZoom(Math.min(500, zoom + 25))} disabled={!hasImages} aria-label="Yakınlaştır">+</button>
        <div className="w-px h-5 bg-[var(--ota-border)] mx-1" />
        <button type="button" className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--ota-bg)] border border-[var(--ota-border)] hover:border-[var(--ota-gold)]/50 hover:text-[var(--ota-gold)] transition-colors disabled:opacity-50" onClick={resetViewer} disabled={!hasImages}>Senkron Sıfırla</button>
      </div>
    </div>
  );
}


