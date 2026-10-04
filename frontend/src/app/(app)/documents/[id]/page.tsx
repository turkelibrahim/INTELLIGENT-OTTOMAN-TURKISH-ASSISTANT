"use client";

import { use, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  documentsApi,
  getToken,
  ocrApi,
  pagesApi,
  type DocumentResponse,
  type OCRJobStatusResponse,
  type OCRPipelineLine,
  type PageResponse,
} from "@/lib/api";

import OriginalDocumentPanel from "@/components/document/OriginalDocumentPanel";
import OCRPanel from "@/components/document/OCRPanel";
import ModernTurkishPanel from "@/components/document/ModernTurkishPanel";
import TransliterationPanel from "@/components/document/TransliterationPanel";
import { FloatingChatWidget } from "@/components/ui/FloatingChatWidget";

const ACTIVE_OCR_STATUSES = new Set([
  "pending", "running", "QUEUED", "PREPROCESSING", "LAYOUT_ANALYSIS",
  "OCR_RUNNING", "TRANSLITERATING", "MODERNIZING", "NER_RUNNING"
]);

const TERMINAL_OCR_STATUSES = new Set([
  "completed", "COMPLETED", "OCR_LOW_QUALITY", "PARTIAL", "failed", "FAILED"
]);

export default function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();

  const [document, setDocument] = useState<DocumentResponse | null>(null);
  const [pages, setPages] = useState<PageResponse[]>([]);
  const [selectedPage, setSelectedPage] = useState<PageResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const [ocrJobId, setOcrJobId] = useState<number | null>(null);
  const [ocrStatus, setOcrStatus] = useState<string | null>(null);
  const [ocrResult, setOcrResult] = useState<NonNullable<OCRJobStatusResponse["result"]> | null>(null);
  const [highlightedLine, setHighlightedLine] = useState<number | null>(null);

  const loadDocument = useCallback(async () => {
    try {
      const docId = Number.parseInt(id, 10);
      const [docData, pagesData] = await Promise.all([documentsApi.get(docId), pagesApi.list(docId)]);
      setDocument(docData);
      setPages(pagesData.pages);
      setSelectedPage(pagesData.pages[0] ?? null);
    } catch {
      router.replace("/dashboard");
    } finally {
      setIsLoading(false);
    }
  }, [id, router]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const timer = window.setTimeout(() => void loadDocument(), 0);
    return () => window.clearTimeout(timer);
  }, [loadDocument, router]);

  useEffect(() => {
    if (!ocrJobId || !ocrStatus || !ACTIVE_OCR_STATUSES.has(ocrStatus)) return;
    if (!document) return;

    const interval = window.setInterval(async () => {
      try {
        const response = await ocrApi.getJobStatus(document.id);
        setOcrStatus(response.status);
        if (TERMINAL_OCR_STATUSES.has(response.status)) {
          setOcrResult(response.result ?? null);
          window.clearInterval(interval);
        }
      } catch {
        window.clearInterval(interval);
      }
    }, 3000);

    return () => window.clearInterval(interval);
  }, [document, ocrJobId, ocrStatus]);

  useEffect(() => {
    if (!document || ocrResult) return;
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      try {
        const response = await ocrApi.getJobStatus(document.id);
        if (cancelled) return;
        setOcrStatus(response.status);
        setOcrResult(response.result ?? null);
      } catch {
        // expected if no OCR run
      }
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [document, ocrResult]);

  const handleStartOcr = async () => {
    if (!document) return;
    try {
      const response = await ocrApi.triggerJob(document.id);
      setOcrJobId(response.job_id);
      setOcrStatus(response.status);
      setDocument({ ...document, status: "ocr" });
    } catch {
      alert("OCR baslatilamadi");
    }
  };

  const pipeline = ocrResult?.pipeline_results;
  const ocrText = pipeline?.original_ocr_text || "";
  const transcriptionText = pipeline?.transliterated_text || "";
  const modernText = pipeline?.modernized_text || "";
  
  const overallConfidence = ocrResult?.confidence_scores?.overall ?? ocrResult?.confidence_scores?.ocr ?? 0;
  
  const ocrLines: OCRPipelineLine[] = (() => {
    if (pipeline?.lines?.length) {
      const selectedPageId = selectedPage?.id == null ? null : String(selectedPage.id);
      const hasPageScopedPayload = pipeline.lines.some((line) => line.page_id != null && line.page_id !== "");
      return selectedPageId && hasPageScopedPayload
        ? pipeline.lines.filter((line) => String(line.page_id) === selectedPageId)
        : pipeline.lines;
    }
    return ocrText.split("\n").map(text => ({ text: text.trim() })).filter(l => l.text);
  })();

  const transcriptionLines = transcriptionText.split("\n").map(t => t.trim()).filter(Boolean);
  const modernLines = modernText.split("\n").map(t => t.trim()).filter(Boolean);
  
  const currentImageUrl = document && selectedPage ? pagesApi.getImageUrl(document.id, selectedPage.page_no) : "";
  const isProcessing = Boolean(ocrStatus && ACTIVE_OCR_STATUSES.has(ocrStatus));
  const hasResult = Boolean(ocrResult);

  const copyText = (text: string) => {
    void navigator.clipboard.writeText(text);
    // Ideally a toast would be shown here
  };

  if (isLoading || !document) {
    return (
      <div className="db-loading-state">
        <div className="db-spinner" />
      </div>
    );
  }

  return (
    <div className="db-workspace">
      <div className="db-workspace-main-panels">
        <OriginalDocumentPanel
          pages={pages}
          selectedPage={selectedPage}
          setSelectedPage={setSelectedPage}
          imageUrl={currentImageUrl}
          ocrLines={ocrLines}
          highlightedLine={highlightedLine}
          setHighlightedLine={setHighlightedLine}
        />
        <OCRPanel
          ocrLines={ocrLines}
          isProcessing={isProcessing}
          hasResult={hasResult}
          overallConfidence={overallConfidence}
          onStartOcr={handleStartOcr}
          onCopy={() => copyText(ocrText)}
          highlightedLine={highlightedLine}
          setHighlightedLine={setHighlightedLine}
          onSave={(_newText) => {
             // Mock update for now
             alert("OCR kaydedildi!");
          }}
        />
        <ModernTurkishPanel
          modernLines={modernLines}
          hasResult={hasResult}
          overallConfidence={overallConfidence}
          onCopy={() => copyText(modernText)}
          onSave={(_newText) => {
            alert("Günümüz Türkçesi kaydedildi!");
          }}
        />
      </div>

      <TransliterationPanel
        transliterationLines={transcriptionLines}
        hasResult={hasResult}
        onCopy={() => copyText(transcriptionText)}
      />
      <FloatingChatWidget documentId={document?.id ?? null} />
    </div>
  );
}
