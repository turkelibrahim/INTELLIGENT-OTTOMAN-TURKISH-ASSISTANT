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
        title: "Orijinal",
        status: originalUrl ? "available" : "not_available",
        safeForOcr: false,
        imageUrl: originalUrl,
        description: "Değişmez orijinal belge.",
        metadata: {},
        warnings: [],
      },
      {
        key: "12_ocr_safe" as StageKey,
        order: "09",
        title: "OCR Güvenli Sonuç",
        status: variantUrl ? "available" : "not_available",
        safeForOcr: true,
        imageUrl: variantUrl,
        description: "OCR güvenli sonuç",
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

  return (
    <div className="ipl-page" ref={pageRef}>
      <header className="ipl-header">
        <div>
          <h1>Görüntü İşleme Laboratuvarı</h1>
          <span>{activeFilename ? activeFilename : "Belge seçin veya ana analizden aktif belgeyle gelin."}</span>
        </div>
        <div className="ipl-badges" aria-label="Sistem durumu">
          <span className="ipl-badge safe">OCR Motoru: Kraken</span>
          <span className="ipl-badge safe">OCR SAFE final</span>
        </div>
      </header>

      <section className="ipl-action-strip" aria-label="Laboratuvar aksiyonları">
        <button type="button" onClick={() => fileRef.current?.click()} aria-label="Belge seç">
          <strong>Belge Seç</strong>
          <span>Gerçek dosya yükle</span>
        </button>
        <button type="button" onClick={runLab} disabled={!file || labStatus === "LOADING_DOCUMENT" || labStatus === "PROCESSING"} aria-label="Otomatik işlem başlat">
          <strong>{labStatus === "PROCESSING" || labStatus === "LOADING_DOCUMENT" ? "Belge işleniyor..." : "Otomatik İşle"}</strong>
          <span>Upload ve OCR-safe üret</span>
        </button>
        <button type="button" onClick={() => downloadObjectUrl(variantUrl, "ocr-guvenli-sonuc.png")} disabled={!variantUrl} aria-label="OCR güvenli görüntüyü indir">
          <strong>OCR Güvenli İndir</strong>
          <span>Gerçek varyant dosyası</span>
        </button>
        <button type="button" onClick={() => router.push("/dashboard")} aria-label="Ana analize dön">
          <strong>Ana Analize Dön</strong>
          <span>Belge analiz ekranı</span>
        </button>
      </section>

      <section className="ipl-control-bar">
        <button className="ipl-file" type="button" onClick={() => fileRef.current?.click()}>
          <strong>{file?.name || "Belge seçilmedi"}</strong>
          <span>{file ? `${formatBytes(file.size)} · ${file.type || "Format tespit edilemedi"}` : "PNG, JPG, TIFF veya PDF"}</span>
        </button>
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
        <label>
          <span>Belge başlığı</span>
          <input className="input-field" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Başlık" />
        </label>
        <div className="ipl-control-actions">
          <button type="button" onClick={() => router.push("/dashboard")}>Ana Analize Dön</button>
          <button type="button" onClick={() => router.push("/historical-analysis")} disabled={!document || !hasAnalysisContext}>Tarihsel Analizi Aç</button>
          <button type="button" onClick={resetAnalysis}>Yeni Analiz</button>
          <button type="button" onClick={() => pageRef.current?.requestFullscreen()} title="Tarayıcı tam ekranı">Tam Ekran</button>
        </div>
      </section>

      {error && <div className="ipl-error">{error}</div>}
      {(labStatus === "LOADING_DOCUMENT" || labStatus === "PROCESSING") && <div className="ipl-progress">Belge işleniyor...</div>}

      <section className="ipl-workspace">
        <article className="ipl-pane">
          <header>
            <div>
              <p>1. Orijinal Belge</p>
              <h2>Değişmez Kaynak</h2>
            </div>
            <span className="ipl-badge muted">ORIGINAL</span>
          </header>
          <ImageViewer imageUrl={originalUrl} label="Orijinal belge" emptyText="İşlem aşamalarını görüntülemek için bir belge seçin." />
          <dl className="ipl-footer-meta">
            <div><dt>Dosya</dt><dd>{display(document?.original_filename || file?.name)}</dd></div>
            <div><dt>Boyut</dt><dd>{formatBytes(document?.file_size || file?.size)}</dd></div>
            <div><dt>Format</dt><dd>{display(document?.mime_type || file?.type)}</dd></div>
            <div><dt>Sayfa</dt><dd>{page ? `${page.page_no} / ${document?.page_count || 1}` : UNKNOWN}</dd></div>
          </dl>
        </article>

        <article className="ipl-pane ipl-center">
          <header>
            <div>
              <p>2. İşlem Aşaması</p>
              <h2>{selected.order} · {selected.title}</h2>
            </div>
            <div className="ipl-stage-selector">
              <select value={selected.key} onChange={(event) => setSelectedStage(event.target.value as StageKey)} aria-label="İşlem aşaması seç">
                {availableStages.map((stage) => <option key={stage.key} value={stage.key}>{stage.order} {stage.title}</option>)}
              </select>
              <span className={`ipl-badge ${selected.safeForOcr ? "safe" : "muted"}`}>{selected.safeForOcr ? "OCR SAFE ✓" : "OCR dışı"}</span>
            </div>
          </header>
          <ImageViewer imageUrl={selected.imageUrl || null} label={`${selected.title} önizleme`} emptyText={selected.description} />
        </article>
        
        {cleanDigitalCopyUrl && (
          <article className="ipl-pane">
            <header>
              <div>
                <p>Ekstra Çıktı</p>
                <h2>Temiz Dijital Belge</h2>
              </div>
              <span className="ipl-badge safe">GÖRSEL KOPYA</span>
            </header>
            <ImageViewer imageUrl={cleanDigitalCopyUrl} label="Temiz dijital belge" emptyText="İşlem aşamalarını görüntülemek için bir belge seçin." />
            <dl className="ipl-footer-meta">
              <div><dt>Amaç</dt><dd>İnsan okuması için iyileştirilmiş</dd></div>
              <div><dt>Not</dt><dd>OCR motoruna gönderilmez</dd></div>
            </dl>
          </article>
        )}

        <aside className="ipl-pane ipl-info">
          <header>
            <div>
              <p>3. Aşama Bilgileri</p>
              <h2>Detaylar ve Metrikler</h2>
            </div>
          </header>
          <dl className="ipl-meta">
            {Object.entries(selected.metadata).map(([key, value]) => (
              <div key={key}><dt>{key}</dt><dd>{display(value)}</dd></div>
            ))}
          </dl>
          <section className="ipl-card-section">
            <h3>Metin Koruma Analizi</h3>
            <p>Osmanlıca karakter noktaları ve ince işaretlerin korunması OCR doğruluğu için kritiktir.</p>
            <dl className="ipl-meta compact">
              <div><dt>Metin koruma skoru</dt><dd>Hesaplanmadı</dd></div>
              <div><dt>Bağlı bileşen değişimi</dt><dd>Hesaplanmadı</dd></div>
              <div><dt>Ön plan piksel değişimi</dt><dd>Hesaplanmadı</dd></div>
              <div><dt>Belirsiz kaldırma</dt><dd>Hesaplanmadı</dd></div>
            </dl>
          </section>
          {selected.warnings.length > 0 && (
            <div className="ipl-warning-list">
              {selected.warnings.map((warning) => <span key={warning}>{warning}</span>)}
            </div>
          )}
        </aside>
      </section>

      <section className="ipl-lower-grid">
        <BeforeAfterComparison
          originalUrl={originalUrl}
          variantUrl={variantUrl}
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

        <section className="ipl-panel">
          <h2>Maske Katmanları</h2>
          {MASK_LAYERS.map((mask) => {
            const layer = maskLayers[mask.key];
            const available = Boolean(layer.rasterUrl || layer.boxes.length || layer.polygons.length);
            return (
              <label
                className={`ipl-mask-row ${activeMasks[mask.key] ? "active" : ""} ${available ? "" : "disabled"}`}
                key={mask.key}
                title={available ? mask.label : "Bu belge için bu maske üretilmedi."}
              >
                <span>
                  <i className={`ipl-mask-swatch ${mask.className}`} aria-hidden="true" />
                  {mask.label}
                </span>
                <input
                  type="checkbox"
                  checked={available && activeMasks[mask.key]}
                  disabled={!available}
                  onChange={(event) => setActiveMasks((current) => ({ ...current, [mask.key]: event.target.checked }))}
                />
              </label>
            );
          })}
          <label className="ipl-opacity">
            <span>Overlay opaklığı</span>
            <input type="range" min="0" max="100" value={maskOpacity} onChange={(event) => setMaskOpacity(Number(event.target.value))} aria-label="Maske opaklığı" />
            <strong>%{maskOpacity}</strong>
          </label>
          <div className="ipl-mask-status">
            {!hasAnyMaskData
              ? "Bu belge için maske verisi üretilmedi."
              : Object.values(activeMasks).some(Boolean)
                ? "Seçili gerçek maske katmanları görüntü koordinatlarında açıldı."
                : "Maske seçilmedi."}
          </div>
        </section>
      </section>

      <details className="ipl-network">
        <summary>Teknik Tanılama</summary>
        <h2>Gerçek API Kanıtı</h2>
        {networkEvidence.length ? <ul>{networkEvidence.map((item, index) => <li key={index}>{item}</li>)}</ul> : <p>Gerçek upload, sayfa görüntüsü, preprocessing ve varyant görüntüsü çağrıları işlemden sonra burada görünür.</p>}
      </details>
    </div>
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
    <section className="ipl-panel ipl-comparison">
      <header>
        <div>
          <p>Önce / Sonra Karşılaştırma</p>
          <h2>Orijinal ↔ OCR Güvenli Sonuç</h2>
        </div>
        <div className="ipl-segments" role="group" aria-label="Karşılaştırma modu">
          <button
            type="button"
            className={mode === "slider" ? "active" : ""}
            onClick={() => setMode("slider")}
            disabled={Boolean(originalDimensions && variantDimensions && !sameGeometry)}
            title={originalDimensions && variantDimensions && !sameGeometry ? "Bu iki görüntünün geometrileri farklı olduğu için slider kullanılamıyor." : "Slider"}
          >
            Slider
          </button>
          <button type="button" className={mode === "side_by_side" ? "active" : ""} onClick={() => setMode("side_by_side")}>Yan Yana</button>
        </div>
      </header>
      <div
        ref={frameRef}
        className={`ipl-compare-frame ${mode} ${isPanning ? "panning" : ""}`}
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
      <div className="ipl-viewer-actions">
        <button type="button" onClick={() => setZoom(Math.max(50, zoom - 25))} disabled={!hasImages} aria-label="Karşılaştırmayı uzaklaştır">-</button>
        <button type="button" onClick={() => setZoom(Math.min(500, zoom + 25))} disabled={!hasImages} aria-label="Karşılaştırmayı yakınlaştır">+</button>
        <button type="button" onClick={resetViewer} disabled={!hasImages} aria-label="Senkron karşılaştırmayı sıfırla">Senkron Sıfırla</button>
        <span>%{zoom}</span>
      </div>
    </section>
  );
}

