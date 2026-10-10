"use client";



import {

  useEffect,

  useMemo,

  useRef,

  useState,

  useCallback,

} from "react";

import { useRouter } from "next/navigation";

import { useRecentDocuments, useDocumentViewer, useDocumentAnalysis } from "./hooks";
import { useFocusMode } from "@/components/dashboard/AppShell";



import {

  analysisApi,

  documentsApi,

  ApiError,

  fetchAuthenticatedBlobUrl,

  getToken,

  ocrReviewApi,

  pagesApi,

  type AnalysisStage,

  type FullAnalysisLine,

  type FullDocumentAnalysisResponse,

  type DocumentResponse,

} from "@/lib/api";

import {

  clearActiveDocumentContext,

  loadActiveDocumentContext,

  saveActiveDocumentContext,

} from "@/lib/documentContext";

import { normalizeLine, modernConfidenceBadge } from "@/lib/viewModel";

import AnalysisProgress from "@/components/ui/AnalysisProgress";

import EmptyState from "@/components/ui/EmptyState";

import ConfidenceBadge from "@/components/ui/ConfidenceBadge";

import StatusBadge from "@/components/ui/StatusBadge";

import DocumentInfoTab from "@/components/workspace/tabs/DocumentInfoTab";

import EntitiesTab from "@/components/workspace/tabs/EntitiesTab";

import HistoricalSidebar from "@/components/workspace/HistoricalSidebar";
import HistoricalContextTab from "@/components/workspace/tabs/HistoricalContextTab";

import SourcesTab from "@/components/workspace/tabs/SourcesTab";

import TechnicalDetailsTab from "@/components/workspace/tabs/TechnicalDetailsTab";

import ChatWidget from "@/components/workspace/ChatWidget";
import { AlertTriangle, FileText, UploadCloud, Star, Archive } from 'lucide-react';




// ── Constants ────────────────────────────────────────────────────────────────

const ACCEPTED_EXTENSIONS = ["jpg", "jpeg", "png", "tiff", "tif", "pdf"];

const ACCEPTED_INPUT = ".jpg,.jpeg,.png,.tiff,.tif,.pdf";

const MAX_SIZE_MB = 50;



type TabKey = "info" | "entities" | "historical" | "sources" | "technical" | "preprocessing" | "model_comparison" | "ai_notes";

const PRIMARY_TABS: Array<{ key: TabKey; label: string }> = [
  { key: "info",       label: "Belge Bilgileri" },
  { key: "entities",   label: "Kişiler ve Yerler" },
  { key: "historical", label: "Tarihsel Bağlam" },
  { key: "sources",    label: "Kaynaklar" },
];

const ADVANCED_TABS: Array<{ key: TabKey; label: string }> = [
  { key: "technical",  label: "Teknik" },
  { key: "preprocessing", label: "Preprocessing" },
  { key: "model_comparison", label: "Model Comparison" },
  { key: "ai_notes",  label: "AI Notes" },
];

const ALL_TABS = [...PRIMARY_TABS, ...ADVANCED_TABS];



function HighlightedText({ text, entities }: { text: string; entities?: Record<string, unknown>[] }) {

  if (!text || !entities || entities.length === 0) return <>{text}</>;

  

  const validEntities = entities.filter(e => 

    ["GLOSSARY", "PER", "LOC", "ORG", "DATE"].includes((e.entity_type || e.type || e.label) as string)

  );

  if (validEntities.length === 0) return <>{text}</>;



  let resultArr: React.ReactNode[] = [text];

  

  validEntities.forEach(ent => {

    const word = (ent.value || ent.text) as string;

    const type = ent.entity_type || ent.type || ent.label;

    const meaning = ent.normalized_value || ent.meaning || type;

    if (!word) return;

    

    let color = "#d4af37"; // GLOSSARY

    if (type === "PER") color = "#3b82f6";

    if (type === "LOC") color = "#10b981";

    if (type === "ORG") color = "#8b5cf6";

    if (type === "DATE") color = "#f59e0b";

    

    const tooltip = type === "GLOSSARY" ? meaning : `${type}: ${meaning}`;



    const newArr: React.ReactNode[] = [];

    resultArr.forEach(item => {

      if (typeof item === "string") {

        const parts = item.split(new RegExp(`(${word})`, 'gi'));

        parts.forEach((p, idx) => {

          if (p.toLowerCase() === word.toLowerCase()) {

            newArr.push(

              <span key={`${word}-${idx}`} title={tooltip as string} style={{ borderBottom: `1px dashed ${color}`, cursor: 'help', color: color, fontWeight: 500 }}>

                {p}

              </span>

            );

          } else {

            newArr.push(p);

          }

        });

      } else {

        newArr.push(item);

      }

    });

    resultArr = newArr;

  });

  

  return <>{resultArr.map((el, i) => <span key={i}>{el}</span>)}</>;

}



// ── Dashboard Page ──────────────────────────────────────────────────────────

export default function DashboardPage() {

  const router = useRouter();

  const inputRef = useRef<HTMLInputElement>(null);

  

  const {

    file, previewUrl, title, setTitle, description, setDescription,

    stage, setStage, uploadProgress, error, setError, result, setResult,

    hasDocument, isComplete, isProcessing, isBusy,

    selectFile, resetDocument, loadRecentDocument, analyze

  } = useDocumentAnalysis();



  const {

    zoom, setZoom, rotation, setRotation, pan, setPan,

    isPanning, setIsPanning, panStart: panStartRef, viewerRef, fitToScreen, openFullscreen

  } = useDocumentViewer();



  const { recentDocuments, isLoadingDocs, toggleFavorite, toggleArchive } = useRecentDocuments(hasDocument);


// Panel state

  const [activeTab, setActiveTab] = useState<TabKey>("info");

  const [showLatin, setShowLatin] = useState(false);
  const [showHistorical, setShowHistorical] = useState(true);

  const [activeLineId, setActiveLineId] = useState<string | null>(null);

  const [isDragging, setIsDragging] = useState(false);

  const { isFocusMode, setIsFocusMode } = useFocusMode();
  const [isChatOpen, setIsChatOpen] = useState(false);


  // OCR edit state

  const [ocrEditMode, setOcrEditMode] = useState(false);

  const [ocrDraft, setOcrDraft] = useState("");

  const [ocrSaveStatus, setOcrSaveStatus] = useState("");

  const [modernEditMode, setModernEditMode] = useState(false);

  const [modernDraft, setModernDraft] = useState("");



  const handleAnalyze = () => analyze(() => { setShowLatin(false); setActiveTab("info"); });

  const handleLoadRecent = (doc: DocumentResponse) => loadRecentDocument(doc, () => { setShowLatin(false); setActiveTab("info"); });





  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    let mounted = true;
    setTimeout(() => {
      if (mounted) setIsMounted(true);
    }, 0);
    return () => { mounted = false; };
  }, []);



  // Auth guard

  useEffect(() => {

    // if (!getToken()) router.replace("/login");

  }, [router]);



  // Export handling

  const handleExport = useCallback(async (format: string) => {

    if (!result || !result.document.document_id) return;

    try {

      const token = getToken();

      let url = "";

      if (format === "json") url = `/api/v1/export/json/${result.document.document_id}`;

      else if (format === "csv") url = `/api/v1/export/csv/entities/${result.document.document_id}`;

      else if (format === "pdf") url = `/api/v1/export/pdf/${result.document.document_id}`;

      else url = `/api/v1/export/txt/${result.document.document_id}?version_type=${format}`;



      const API_BASE = process.env.NEXT_PUBLIC_API_URL?.replace("/api/v1", "") || "http://localhost:8000";

      const res = await fetch(`${API_BASE}${url}`, {

        headers: { Authorization: `Bearer ${token}` }

      });

      if (!res.ok) throw new Error("Export failed");

      

      const blob = await res.blob();

      const downloadUrl = window.URL.createObjectURL(blob);

      const a = document.createElement("a");

      a.href = downloadUrl;

      a.download = `document_${result.document.document_id}_export.${format === "json" ? "json" : format === "csv" ? "csv" : format === "pdf" ? "pdf" : "txt"}`;

      document.body.appendChild(a);

      a.click();

      window.URL.revokeObjectURL(downloadUrl);

      a.remove();

    } catch (err) {

      console.error(err);

      alert("Dışa aktarma başarısız oldu.");

    }

  }, [result]);



  // Computed

  const ocrLines = useMemo(() => (result?.ocr.lines || []).map(normalizeLine), [result]);

  const transliterationLines = useMemo(() => (result?.transliteration.lines || []).map((l, i) => normalizeLine(l as FullAnalysisLine, i)), [result]);

  const modernLines = useMemo(() => (result?.modern_turkish.lines || []).map((l, i) => normalizeLine(l as FullAnalysisLine, i)), [result]);



  const activeOcrLine = useMemo(() => ocrLines.find((l) => l.line_id === activeLineId) || ocrLines[0] || null, [activeLineId, ocrLines]);

  const modernBadge = useMemo(() => (result ? modernConfidenceBadge(result) : null), [result]);



  const copyText = (text: string) => {

    if (!text.trim()) return;

    void navigator.clipboard.writeText(text);

  };



  const addManualLine = useCallback(() => {

    if (!result) return;

    const newLineNo = (result.ocr?.lines?.length || 0) + 1;

    const newLineId = `manual-${Date.now()}`;

    const newOcrLine = { line_no: newLineNo, line_id: newLineId, text: "", confidence: 1.0, bbox: [0, 0, 100, 30] as [number, number, number, number] };

    const newResult = JSON.parse(JSON.stringify(result));

    if (!newResult.ocr) newResult.ocr = { lines: [], ottoman_text: "", engine: "manual", fallback_used: true, confidence: 1.0 };

    if (!newResult.ocr.lines) newResult.ocr.lines = [];

    newResult.ocr.lines.push(newOcrLine);

    if (!newResult.transliteration) newResult.transliteration = { lines: [], latin_text: "", method: "manual", confidence: 1.0, warnings: [] };

    if (!newResult.transliteration.lines) newResult.transliteration.lines = [];

    newResult.transliteration.lines.push({ line_no: newLineNo, line_id: newLineId, text: "", confidence: 1.0 });

    if (!newResult.modern_turkish) newResult.modern_turkish = { lines: [], text: "", provider: "manual", confidence: 1.0, warnings: [] };

    if (!newResult.modern_turkish.lines) newResult.modern_turkish.lines = [];

    newResult.modern_turkish.lines.push({ line_no: newLineNo, line_id: newLineId, text: "", confidence: 1.0 });

    setResult(newResult);

    setActiveLineId(newLineId);

    setOcrDraft("");

    setOcrEditMode(true);

  }, [result, setResult]);



  const downloadAnalysis = () => {

    if (!result) return;

    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });

    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");

    a.href = url;

    a.download = `${result.document.filename.replace(/\.[^/.]+$/, "") || "belge"}-analiz.json`;

    document.body.appendChild(a);

    a.click();

    a.remove();

    URL.revokeObjectURL(url);

  };



  const startOcrEdit = () => {

    if (!activeOcrLine) return;

    setOcrDraft(activeOcrLine.text || activeOcrLine.ocr_text || "");

    setOcrEditMode(true);

    setOcrSaveStatus("");

  };



  const saveOcrCorrection = async () => {

    if (!activeOcrLine?.ocr_result_id || !ocrDraft.trim() || !result) return;

    const previousText = activeOcrLine.text || activeOcrLine.ocr_text || "";

    setOcrSaveStatus("Kaydediliyor…");

    try {

      await ocrReviewApi.createCorrection(activeOcrLine.ocr_result_id, ocrDraft.trim(), previousText);

      const updatedLines = result.ocr.lines.map((l) => l.ocr_result_id === activeOcrLine.ocr_result_id ? { ...l, text: ocrDraft.trim(), ocr_text: ocrDraft.trim(), is_edited: true } : l);

      const updatedText = updatedLines.map((l) => l.text || l.ocr_text || "").join("\n");

      const updated = { ...result, ocr: { ...result.ocr, lines: updatedLines, ottoman_text: updatedText } };

      setResult(updated);

      saveActiveDocumentContext(updated);

      setOcrSaveStatus("Kaydedildi");

      setOcrEditMode(false);

    } catch (caught) {

      setOcrSaveStatus(caught instanceof ApiError ? caught.detail : "Kayıt hatası");

    }

  };



  const cancelOcrEdit = () => {

    setOcrEditMode(false);

    setOcrDraft("");

    setOcrSaveStatus("");

  };



  const activeModernLine = useMemo(() => modernLines.find((l) => l.line_id === activeLineId) || modernLines[0] || null, [activeLineId, modernLines]);



  const startModernEdit = () => {

    if (!activeModernLine) return;

    setModernDraft((activeModernLine as unknown as Record<string, unknown>).modern_text as string || activeModernLine.text || "");

    setModernEditMode(true);

  };



  const saveModernDraft = () => {

    if (!activeModernLine || !result) return;

    const updatedLines = result.modern_turkish.lines.map((rawLine) => {

      const l = rawLine as FullAnalysisLine;

      return l.line_id === activeModernLine.line_id ? { ...rawLine, modern_text: modernDraft, text: modernDraft, is_edited: true } : rawLine;

    });

    const updatedText = updatedLines.map((l) => {

      const line = l as FullAnalysisLine;

      return (line as unknown as Record<string, unknown>).modern_text as string || line.text || "";

    }).join("\n");

    const updated: FullDocumentAnalysisResponse = { ...result, modern_turkish: { ...result.modern_turkish, lines: updatedLines, text: updatedText } };

    setResult(updated);

    saveActiveDocumentContext(updated);

    setModernEditMode(false);

  };



  const handleLineClick = (lineId: string | null) => setActiveLineId((prev) => (prev === lineId ? null : lineId));



  const flatEntities = useMemo(() => {

    if (!result) return [];

    const arr: Record<string, unknown>[] = [];

    if (result.entities) {

      if (result.entities.persons) arr.push(...result.entities.persons.map((e) => ({ ...e, type: "PER" })));

      if (result.entities.places) arr.push(...result.entities.places.map((e) => ({ ...e, type: "LOC" })));

      if (result.entities.institutions) arr.push(...result.entities.institutions.map((e) => ({ ...e, type: "ORG" })));

      if (result.entities.dates) arr.push(...result.entities.dates.map((e) => ({ ...e, type: "DATE" })));

    }

    if (result.glossary) {

      arr.push(...(result.glossary as Record<string, string>[]).map((g) => ({ value: g.term || g.word, type: "GLOSSARY", meaning: g.meaning || g.modern_turkish })));

    }

    return arr;

  }, [result]);



  if (!isMounted) return null;



  return (

    <div className="ota-dashboard">

      {/* ── Empty Welcome State (no document) ── */}

      {!hasDocument && stage === "IDLE" && (

        <div className="ota-welcome">

          <div className="ota-welcome-inner">

            <div className="ota-welcome-icon" aria-hidden="true">

              <svg width="64" height="64" viewBox="0 0 64 64" fill="none">

                <rect x="8" y="4" width="36" height="48" rx="4" stroke="#D7A548" strokeWidth="2" fill="none" opacity=".3"/>

                <rect x="12" y="8" width="28" height="2" rx="1" fill="#D7A548" opacity=".5"/>

                <rect x="12" y="14" width="20" height="2" rx="1" fill="#D7A548" opacity=".4"/>

                <rect x="12" y="20" width="24" height="2" rx="1" fill="#D7A548" opacity=".3"/>

                <circle cx="46" cy="46" r="12" fill="#0A202A" stroke="#D7A548" strokeWidth="1.5"/>

                <path d="M46 40v12M40 46h12" stroke="#D7A548" strokeWidth="2" strokeLinecap="round"/>

              </svg>

            </div>

            <h2 className="ota-welcome-title">Yeni bir Osmanlıca belge analiz edin</h2>

            <p className="ota-welcome-desc">

              Belgenizi yükleyin; OCR, Latin harfli okunuş, Günümüz Türkçesi ve belge

              bilgileri tek çalışma alanında hazırlansın.

            </p>



            {/* Upload zone */}

            <div

              className={`ota-dropzone${isDragging ? " dragging" : ""}`}

              role="button"

              tabIndex={0}

              aria-label="Belge yüklemek için tıklayın veya sürükleyin"

              onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}

              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}

              onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}

              onDrop={(e) => {

                e.preventDefault();

                setIsDragging(false);

                const dropped = e.dataTransfer.files[0];

                if (dropped) selectFile(dropped);

              }}

              onClick={() => inputRef.current?.click()}

            >

              <input

                ref={inputRef}

                type="file"

                accept={ACCEPTED_INPUT}

                onChange={(e) => {

                  const sel = e.target.files?.[0];

                  if (sel) selectFile(sel);

                }}

                hidden

                aria-label="Belge dosyası seç"

              />

              <div className="ota-dropzone-icon" aria-hidden="true"><UploadCloud className="w-12 h-12 mx-auto text-[var(--ota-gold)] opacity-80" /></div>

              <strong className="ota-dropzone-label">Belge Yükle</strong>

              <span className="ota-dropzone-hint">PDF · JPG · PNG · TIFF · Maksimum 50 MB</span>

            </div>



            {error && (

              <div className="ota-alert error" role="alert">

                <strong>Hata:</strong> {error}

              </div>

            )}

          </div>



          {/* Son Eklenen Belgeler (Recent Documents) */}
          {recentDocuments.length > 0 && (
            <div className="mt-16 w-full max-w-4xl animate-in slide-in-from-bottom-4 fade-in duration-700">
              <h3 className="text-lg font-medium text-[var(--ota-text)] mb-6 flex items-center gap-2">
                <span className="text-[var(--ota-gold)]"><FileText className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> Son Analiz Edilen Belgeleriniz
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {recentDocuments.map((doc) => (
                  <div 
                    key={doc.id}
                    className="glass-panel p-5 rounded-xl cursor-pointer hover:border-[var(--ota-border-hover)] transition-all hover:bg-[var(--ota-bg-2)] flex flex-col gap-2 group"
                    onClick={() => handleLoadRecent(doc)}
                  >
                    <div className="flex items-start justify-between">
                      <span className="text-xl group-hover:scale-110 transition-transform origin-bottom-left text-[var(--ota-text)]"><FileText className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>
                      <div className="flex items-center gap-2">
                        <button 
                          onClick={(e) => { e.stopPropagation(); toggleFavorite(doc.id); }}
                          title="Favorilere Ekle"
                          className={`p-1.5 rounded-md transition-colors ${doc.is_favorite ? 'text-[var(--ota-gold)] bg-[var(--ota-gold-dim)]' : 'text-[var(--ota-text-muted)] hover:text-[var(--ota-gold)] hover:bg-[var(--ota-gold-dim)]'}`}
                        >
                          <Star className={`w-4 h-4 ${doc.is_favorite ? 'fill-current' : ''}`} />
                        </button>
                        <button 
                          onClick={(e) => { e.stopPropagation(); toggleArchive(doc.id); }}
                          title="Arşive Kaldır"
                          className="p-1.5 rounded-md text-[var(--ota-text-muted)] hover:text-[var(--ota-ruby)] hover:bg-[var(--ota-ruby)]/10 transition-colors"
                        >
                          <Archive className="w-4 h-4" />
                        </button>
                        <span className="text-xs px-2 py-1 bg-[var(--ota-gold-dim)] text-[var(--ota-gold)] rounded-md ml-2 border border-[var(--ota-border)]">
                          {new Date(doc.created_at).toLocaleDateString("tr-TR")}
                        </span>
                      </div>
                    </div>
                    <h4 className="font-semibold text-[var(--ota-text)] truncate mt-2 group-hover:text-[var(--ota-gold)] transition-colors">
                      {doc.title}
                    </h4>
                    <p className="text-xs text-[var(--ota-text-muted)] truncate">
                      {doc.original_filename}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}



        </div>

      )}



      {/* ── Upload form (file selected, not yet analyzed) ── */}

      {hasDocument && !isComplete && !isProcessing && stage !== "ERROR" && (

        <div className="ota-upload-form-bar">

          <div className="ota-upload-file-info">

            <span className="ota-file-icon" aria-hidden="true"><FileText className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>

            <span className="ota-file-name">{file?.name || "Belge yüklendi"}</span>

            {file && (

              <span className="ota-file-size">

                {(file.size / 1024 / 1024).toFixed(2)} MB

              </span>

            )}

          </div>

          <div className="ota-upload-fields">

            <input

              className="ota-input"

              value={title}

              onChange={(e) => setTitle(e.target.value)}

              placeholder="Belge başlığı (zorunlu)"

              aria-label="Belge başlığı"

              required

            />

            <input

              className="ota-input"

              value={description}

              onChange={(e) => setDescription(e.target.value)}

              placeholder="Kısa açıklama (isteğe bağlı)"

              aria-label="Belge açıklaması"

            />

          </div>

          <div className="ota-upload-actions">

            <button

              type="button"

              className="ota-btn-ghost"

              onClick={resetDocument}

            >

              İptal

            </button>

            <button

              type="button"

              className="ota-btn-primary"

              onClick={handleAnalyze}

              disabled={isBusy || !file || !title.trim()}

            >

              Analiz Et

            </button>

          </div>

          {error && (

            <div className="ota-alert error" role="alert">

              <strong>Hata:</strong> {error}

            </div>

          )}

        </div>

      )}



      {/* ── Processing ── */}

      {isProcessing && (

        <div className="ota-processing-banner" style={{ display: 'flex', gap: '40px', alignItems: 'center', justifyContent: 'center', padding: '48px', maxWidth: '1000px', margin: '0 auto' }}>

          {previewUrl && (

             <div className="processing-image-preview animate-in zoom-in-95 duration-500" style={{ flex: '0 0 45%' }}>

               <img src={previewUrl} alt="İşleniyor..." style={{ width: '100%', borderRadius: '16px', boxShadow: '0 12px 40px rgba(0,0,0,0.6)', border: '1px solid rgba(215, 165, 72, 0.2)', opacity: 0.85 }} />

             </div>

          )}

          <div className="processing-status" style={{ flex: '1', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>

            <AnalysisProgress stage={stage} uploadProgress={uploadProgress} />

            <p className="ota-processing-note" style={{ marginTop: '32px', fontSize: '15px' }}>

              Belgeniz yapay zeka tarafından işleniyor, lütfen bekleyin…

            </p>

          </div>

        </div>

      )}



      {/* ── Error state ── */}

      {stage === "ERROR" && (

        <div className="ota-error-banner" role="alert">

          <div className="ota-error-content">

            <span className="ota-error-icon"><AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>

            <div>

              <strong>Analiz tamamlanamadıı</strong>

              <p>{error || "Bu aşama işlenirken bir sorun oluştu."}</p>

            </div>

          </div>

          <button type="button" className="ota-btn-ghost" onClick={resetDocument}>

            Yeni Belge

          </button>

          <button

            type="button"

            className="ota-btn-secondary"

            onClick={handleAnalyze}

            disabled={!file}

          >

            Tekrar Dene

          </button>

        </div>

      )}



      {/* ── Main Workspace (3 panels + Latin + Tabs) ── */}

      {isComplete && result && (

        <div className={`ota-workspace ${isFocusMode ? 'focus-mode-active' : ''}`}>

          {/* Document title + actions row */}

          <div className="ota-workspace-topbar">

            <div className="ota-workspace-doc-info">

              <span className="ota-workspace-filename">

                {result.document.filename}

              </span>

              {result.document.document_type && (

                <span className="ota-workspace-doctype">

                  {result.document.document_type}

                </span>

              )}

            </div>

            <div className="ota-workspace-actions">

              <button

                type="button"

                className="ota-btn-ghost small"

                onClick={() => handleExport("json")}

              >

                JSON İndir

              </button>

              <button

                type="button"

                className="ota-btn-ghost small"

                onClick={() => handleExport("pdf")}

              >

                PDF İndir

              </button>

              <button

                type="button"

                className="ota-btn-ghost small"

                onClick={() => handleExport("csv")}

              >

                CSV İndir

              </button>

              <button

                type="button"

                className="ota-btn-ghost small"

                onClick={() => handleExport("modern")}

              >

                TXT İndir

              </button>

              <button

                type="button"

                className="ota-btn-ghost small"

                onClick={() => router.push("/image-processing-lab")}

              >

                Görüntü İşleme

              </button>

              <button

                type="button"

                className="ota-btn-ghost small"

                onClick={resetDocument}

              >
Yeni Belge

              </button>

              <button type="button" className={`ota-btn-ghost small ${isFocusMode ? 'bg-[var(--ota-gold)] text-[var(--ota-obsidian)]' : ''}`} onClick={() => setIsFocusMode(!isFocusMode)}>
                {isFocusMode ? "Odak Modu Açık" : "Odak Modu"}
              </button>
              <button type="button" className={`ota-btn-ghost small ${!showHistorical ? 'bg-[var(--ota-gold)] text-[var(--ota-obsidian)]' : ''}`} onClick={() => setShowHistorical(!showHistorical)}>
                {showHistorical ? "Analizi Gizle" : "Analizi Aç"}
              </button>
            </div>

          </div>


          
          

          {/* ── Three Panel Grid & Sidebar Wrapper ── */}

          <div className="flex-1 min-w-0 flex flex-col gap-6 w-full">
              <div className={`ota-workspace-grid ${!showHistorical ? "hide-sidebar" : ""}`}>

            {/* Panel 1: Original Document */}

            <article className="ota-panel" aria-label="Orijinal Belge">

              <header className="ota-panel-header">

                <h2 className="ota-panel-title">Orijinal Belge</h2>

                <div className="ota-panel-toolbar">

                  <button

                    type="button"

                    className="ota-viewer-btn"

                    onClick={() => setZoom((v) => Math.max(50, v - 25))}

                    aria-label="Küçült"

                    title="Küçült"

                  >−</button>

                  <span className="ota-zoom-label">%{zoom}</span>

                  <button

                    type="button"

                    className="ota-viewer-btn"

                    onClick={() => setZoom((v) => Math.min(300, v + 25))}

                    aria-label="Büyüt"

                    title="Büyüt"

                  >+</button>

                  <button

                    type="button"

                    className="ota-viewer-btn"

                    onClick={fitToScreen}

                    aria-label="Ekrana sığdır"

                    title="Sığdır"

                  >⛶</button>

                  <button

                    type="button"

                    className="ota-viewer-btn"

                    onClick={() => setRotation((v) => (v + 90) % 360)}

                    aria-label="Döndür"

                    title="Döndür"

                  >↻</button>

                  <button

                    type="button"

                    className="ota-viewer-btn"

                    onClick={openFullscreen}

                    aria-label="Tam ekran"

                    title="Tam Ekran"

                  >⛶</button>

                  <button

                    type="button"

                    className="ota-viewer-btn"

                    onClick={downloadAnalysis}

                    aria-label="Analizi indir"

                    title="İndir"

                  >⬇</button>

                </div>

              </header>

              <div

                ref={viewerRef}

                className="ota-viewer-body"

                onPointerDown={(e) => {

                  setIsPanning(true);

                  panStartRef.current = {

                    x: e.clientX, y: e.clientY,

                    panX: pan.x, panY: pan.y,

                  };

                }}

                onPointerMove={(e) => {

                  if (!isPanning) return;

                  setPan({

                    x: panStartRef.current.panX + e.clientX - panStartRef.current.x,

                    y: panStartRef.current.panY + e.clientY - panStartRef.current.y,

                  });

                }}

                onPointerUp={() => setIsPanning(false)}

                onPointerLeave={() => setIsPanning(false)}

              >

                {previewUrl ? (

                  // eslint-disable-next-line @next/next/no-img-element

                  <img

                    src={previewUrl}

                    alt="Orijinal Osmanlıca belge görüntüsü"

                    className="ota-viewer-img"

                    style={{

                      transform: `translate(${pan.x}px,${pan.y}px) scale(${zoom / 100}) rotate(${rotation}deg)`,

                    }}

                    draggable={false}

                  />

                ) : file?.type === "application/pdf" ? (

                  <div className="ota-viewer-pdf-placeholder">PDF Belgesi</div>

                ) : (

                  <EmptyState

                    title="Belge görüntüsü yüklenemedi"

                    description="Analiz sonucu korunuyor."

                    compact

                  />

                )}

              </div>

            </article>



            {/* Panel 2: OCR — Ottoman */}

            <article className="ota-panel" aria-label="Osmanlıca Metin">

              <header className="ota-panel-header">

                <div>

                  <h2 className="ota-panel-title">Osmanlıca Metin</h2>

                  <span className="ota-panel-subtitle">OCR Sonucu</span>

                </div>

                <div className="ota-panel-header-right">

                  {result.ocr.confidence != null && (

                    <ConfidenceBadge value={result.ocr.confidence} label="Güven" small />

                  )}

                  <div className="ota-panel-actions">

                    {!ocrEditMode ? (

                      <>

                        <button

                          type="button"

                          className="ota-btn-ghost small"

                          onClick={() => copyText(result.ocr.ottoman_text || "")}

                          aria-label="Osmanlıca metni kopyala"

                        >

                          Kopyala

                        </button>

                        <button

                          type="button"

                          className="ota-btn-ghost small"

                          onClick={addManualLine}

                          aria-label="Manuel satır ekle"

                        >

                          Satır Ekle

                        </button>

                        <button

                          type="button"

                          className="ota-btn-ghost small"

                          onClick={startOcrEdit}

                          disabled={!activeOcrLine}

                          aria-label="Seçili satırı düzenle"

                        >

                          Düzenle

                        </button>

                      </>

                    ) : (

                      <>

                        <button

                          type="button"

                          className="ota-btn-primary small"

                          onClick={saveOcrCorrection}

                          disabled={!ocrDraft.trim()}

                        >

                          Kaydet

                        </button>

                        <button

                          type="button"

                          className="ota-btn-ghost small"

                          onClick={cancelOcrEdit}

                        >

                          Vazgeç

                        </button>

                      </>

                    )}

                  </div>

                </div>

              </header>



              {ocrEditMode && (

                <div className="ota-inline-editor">

                  <textarea

                    className="ota-edit-textarea"

                    value={ocrDraft}

                    onChange={(e) => setOcrDraft(e.target.value)}

                    dir="rtl"

                    aria-label="OCR düzeltme metni"

                    rows={4}

                  />

                  {ocrSaveStatus && (

                    <small className="ota-edit-status">{ocrSaveStatus}</small>

                  )}

                </div>

              )}



              <div className="ota-panel-body ota-ottomanic-text" dir="rtl">

                {ocrLines.length > 0 ? (

                  ocrLines.map((line, i) => {

                    const lineId = line.line_id || `ocr-${i}`;

                    const isActive = activeLineId === lineId;

                    return (

                      <p

                        key={lineId}

                        className={`ota-text-line${isActive ? " active" : ""}`}

                        onClick={() => handleLineClick(lineId)}

                        aria-selected={isActive}

                        role="option"

                      >

                        <span className="ota-line-num" aria-hidden="true">

                          {String(line.line_no || i + 1).padStart(2, "0")}

                        </span>

                        <span className={`ota-line-text ${(line as unknown as Record<string, boolean>).is_edited ? "ota-edited-text" : ""}`}>

                          {line.text}

                        </span>

                      </p>

                    );

                  })

                ) : isComplete ? (

                  <EmptyState

                    title="Hiç metin bulunamadı"

                    description="Otomatik analiz metin tespit edemedi. 'Satır Ekle' butonuyla manuel olarak metin girebilirsiniz."

                    compact

                  />

                ) : (

                  <EmptyState

                    title="OCR sonucu bekleniyor"

                    compact

                  />

                )}

              </div>

            </article>



            {/* Panel 3: Modern Turkish */}

            <article className="ota-panel" aria-label="Günümüz Türkçesi">

              <header className="ota-panel-header">

                <div>

                  <h2 className="ota-panel-title">Günümüz Türkçesi</h2>

                  {modernBadge && (

                    <StatusBadge

                      variant={modernBadge.variant}

                      label={modernBadge.label}

                      tooltip={modernBadge.tooltip}

                      small

                    />

                  )}

                </div>

                <div className="ota-panel-header-right">

                  {result.confidence.modern_turkish != null && (

                    <ConfidenceBadge

                      value={result.confidence.modern_turkish}

                      label="Güven"

                      small

                    />

                  )}

                  <div className="ota-panel-actions">

                    {!modernEditMode ? (

                      <>

                        <button

                          type="button"

                          className="ota-btn-ghost small"

                          onClick={() => copyText(result.modern_turkish.text || "")}

                          aria-label="Modern Türkçe metni kopyala"

                        >

                          Kopyala

                        </button>

                        <button

                          type="button"

                          className="ota-btn-ghost small"

                          onClick={startModernEdit}

                          disabled={!activeModernLine}

                        >

                          Düzenle

                        </button>

                      </>

                    ) : (

                      <>

                        <button

                          type="button"

                          className="ota-btn-primary small"

                          onClick={saveModernDraft}

                          disabled={!modernDraft.trim()}

                        >

                          Kaydet

                        </button>

                        <button

                          type="button"

                          className="ota-btn-ghost small"

                          onClick={() => setModernEditMode(false)}

                        >

                          Vazgeç

                        </button>

                      </>

                    )}

                  </div>

                </div>

              </header>



              {modernEditMode && (

                <div className="ota-inline-editor">

                  <textarea

                    className="ota-edit-textarea"

                    value={modernDraft}

                    onChange={(e) => setModernDraft(e.target.value)}

                    aria-label="Modern Türkçe düzenleme metni"

                    rows={4}

                  />

                </div>

              )}



              <div className="ota-panel-body">

                {modernLines.length > 0 ? (

                  modernLines.map((line, i) => {

                    const lineId = line.line_id || `modern-${i}`;

                    const isActive = activeLineId === lineId;

                    // eslint-disable-next-line @typescript-eslint/no-explicit-any

                    const lineRec = line as unknown as Record<string, unknown>;

                    const text = lineRec.modern_text as string || line.text || "";

                    return (

                      <p

                        key={lineId}

                        className={`ota-text-line${isActive ? " active" : ""}`}

                        onClick={() => handleLineClick(lineId)}

                        aria-selected={isActive}

                        role="option"

                      >

                        <span className="ota-line-num" aria-hidden="true">

                          {String(line.line_no || i + 1).padStart(2, "0")}

                        </span>

                        <span className={`ota-line-text ${(line as unknown as Record<string, boolean>).is_edited ? "ota-edited-text" : ""}`}>

                          <HighlightedText text={text} entities={flatEntities} />

                        </span>

                      </p>

                    );

                  })

                ) : isComplete ? (

                  <EmptyState

                    title="Hiç metin bulunamadı"

                    compact

                  />

                ) : (

                  <EmptyState

                    title="Modern Türkçe aktarım bekleniyor"

                    compact

                  />

                )}

              </div>

            </article>

{showHistorical && <HistoricalSidebar result={result} onGoToOcr={() => setActiveTab("technical")} />}

</div>

{/* ── Latin Transliteration (collapsible) ── */}

          <div className="ota-latin-section">

            <div

              className="ota-latin-header"

              role="button"

              tabIndex={0}

              aria-expanded={showLatin}

              onClick={() => setShowLatin((v) => !v)}

              onKeyDown={(e) => e.key === "Enter" && setShowLatin((v) => !v)}

            >

              <div className="ota-latin-header-left">

                <span className="ota-latin-title">Latin Harfli Okunuş</span>

                <span className="ota-badge ota-badge-neutral small">İsteğe Bağlı</span>

              </div>

              <button

                type="button"

                className="ota-btn-ghost small"

                aria-label={showLatin ? "Latin panelini kapat" : "Latin panelini aç"}

                onClick={(e) => { e.stopPropagation(); setShowLatin((v) => !v); }}

              >

                {showLatin ? "Kapat ▲" : "Aç ▼"}

              </button>

            </div>



            {showLatin && (

              <div className="ota-latin-body">

                <div className="ota-latin-actions">

                  <button

                    type="button"

                    className="ota-btn-ghost small"

                    onClick={() => copyText(result.transliteration.latin_text || "")}

                  >

                    Kopyala

                  </button>

                  {result.transliteration.confidence != null && (

                    <ConfidenceBadge

                      value={result.transliteration.confidence}

                      label="Güven"

                      small

                    />

                  )}

                </div>

                <div className="ota-latin-scroll" role="list">

                  {transliterationLines.length > 0 ? (

                    transliterationLines.map((line, i) => {

                      const lineId = line.line_id || `latin-${i}`;

                      const isActive = activeLineId === lineId;

                      // eslint-disable-next-line @typescript-eslint/no-explicit-any

                      const lineRec = line as unknown as Record<string, unknown>;

                      const text = lineRec.latin_text as string || line.text || "";

                      return (

                        <div

                          key={lineId}

                          className={`ota-latin-line${isActive ? " active" : ""}`}

                          onClick={() => handleLineClick(lineId)}

                          role="listitem"

                        >

                          <span className="ota-line-num" aria-hidden="true">

                            {String(line.line_no || i + 1).padStart(2, "0")}

                          </span>

                          <span className="ota-latin-text">

                            <HighlightedText text={text} entities={flatEntities} />

                          </span>

                        </div>

                      );

                    })

                  ) : isComplete ? (

                    <p className="ota-empty-text">Hiç metin bulunamadı.</p>

                  ) : (

                    <p className="ota-empty-text">Latin okunuş bekleniyor.</p>

                  )}

                </div>

              </div>

            )}

          </div>



          {/* ── Document Tabs ── */}

          <div className="ota-doc-tabs-section">

            <div className="ota-tabs-nav" role="tablist" aria-label="Belge bilgi sekmeleri">

              <div className="flex items-center gap-6">
                <div className="flex gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[var(--ota-text-muted)] self-center mr-2">Temel</span>
                  {PRIMARY_TABS.map((tab) => (
                    <button
                      key={tab.key}
                      type="button"
                      role="tab"
                      className={`ota-tab${activeTab === tab.key ? " active" : ""}`}
                      aria-selected={activeTab === tab.key}
                      aria-controls={`tab-panel-${tab.key}`}
                      onClick={() => setActiveTab(tab.key)}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
                <div className="w-px h-4 bg-[var(--glass-border)] mx-2" />
                <div className="flex gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[var(--ota-text-muted)] self-center mr-2">İleri</span>
                  {ADVANCED_TABS.map((tab) => (
                    <button
                      key={tab.key}
                      type="button"
                      role="tab"
                      className={`ota-tab${activeTab === tab.key ? " active" : ""}`}
                      aria-selected={activeTab === tab.key}
                      aria-controls={`tab-panel-${tab.key}`}
                      onClick={() => setActiveTab(tab.key)}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div

              className="ota-tab-content"

              id={`tab-panel-${activeTab}`}
              role="tabpanel"
              aria-label={ALL_TABS.find((t) => t.key === activeTab)?.label}
            >

              {activeTab === "info" && (

                <DocumentInfoTab result={result} />

              )}



              {activeTab === "entities" && (

                <EntitiesTab result={result} />

              )}



              {activeTab === "sources" && <SourcesTab result={result} />}
              {activeTab === "technical" && <TechnicalDetailsTab result={result} />}
              {activeTab === "historical" && (
                <div className="w-full max-w-[900px] mx-auto">
                  <HistoricalContextTab result={result} onGoToOcr={() => setActiveTab("technical")} />
                </div>
              )}
              {activeTab === "preprocessing" && (
                <EmptyState title="Preprocessing Data" description="Görüntü iyileştirme adımları ve filtre logları burada listelenecek." compact />
              )}
              {activeTab === "model_comparison" && (
                <EmptyState title="Model Karşılaştırması" description="Yerel ve NVIDIA OCR modellerinin metin karşılaştırması." compact />
              )}
              {activeTab === "ai_notes" && (
                <EmptyState title="Yapay Zeka Notları" description="Modelin çeviri ve analiz esnasında çıkardığı notlar." compact />
              )}
            </div>
          </div>
        </div>
      </div>
    )}
  <ChatWidget documentId={result?.document?.document_id || null} isOpen={isChatOpen} onToggle={setIsChatOpen} />

</div>

  );

}



