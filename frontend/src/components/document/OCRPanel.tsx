"use client";

import { useState } from "react";
import type { OCRPipelineLine } from "@/lib/api";
import { Icons } from "@/components/Icons";
import { Copy, Edit2 } from 'lucide-react';

export default function OCRPanel({
  ocrLines,
  isProcessing,
  hasResult,
  overallConfidence,
  onStartOcr,
  onCopy,
  highlightedLine,
  setHighlightedLine,
  onSave
}: {
  ocrLines: OCRPipelineLine[];
  isProcessing: boolean;
  hasResult: boolean;
  overallConfidence: number;
  onStartOcr: () => void;
  onCopy: () => void;
  highlightedLine: number | null;
  setHighlightedLine: (index: number | null) => void;
  onSave?: (newText: string) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState("");

  const fullText = ocrLines.map(l => l.text).join("\n");

  const handleEdit = () => {
    setEditText(fullText);
    setIsEditing(true);
  };

  const handleSave = () => {
    setIsEditing(false);
    if (onSave) onSave(editText);
  };

  const confidenceClass = (score: number) => {
    if (score >= 0.9) return "high";
    if (score >= 0.7) return "medium";
    return "low";
  };

  return (
    <div className="db-panel">
      <div className="db-panel-header">
        <h2 className="db-panel-title">
          <span className="db-panel-icon">T</span>
          OCR Metni
        </h2>
        <div className="db-panel-actions">
          <button className="db-icon-btn flex items-center justify-center" onClick={onCopy} title="Metni Kopyala"><Copy className="w-4 h-4 text-current" /></button>
        </div>
      </div>
      
      <div className="db-panel-content">
        {!hasResult ? (
           <div className="db-empty-state">
             {isProcessing ? (
                <>
                  <div className="db-spinner" />
                  <p>OCR İşleniyor...</p>
                </>
             ) : (
                <>
                  <p>Belge işlendiğinde OCR sonucu burada görünecek.</p>
                  <button className="db-primary-btn" onClick={onStartOcr}>OCR Başlat</button>
                </>
             )}
           </div>
        ) : ocrLines.length === 0 ? (
           <div className="db-empty-state">Metin bulunamadı.</div>
        ) : isEditing ? (
           <textarea 
             className="db-editor-textarea" 
             dir="rtl"
             value={editText}
             onChange={(e) => setEditText(e.target.value)}
           />
        ) : (
           <div className="db-text-content">
             {ocrLines.map((line, index) => (
                <div 
                  key={`${line.text}-${index}`} 
                  className={`db-text-line ${highlightedLine === index ? "active" : ""}`}
                  onClick={() => setHighlightedLine(index)}
                  dir="rtl"
                >
                  <span className="db-line-text">{line.text}</span>
                  {line.confidence && (
                     <span className={`db-line-confidence ${confidenceClass(line.confidence)}`}>
                        {Math.round(line.confidence * 100)}%
                     </span>
                  )}
                </div>
             ))}
           </div>
        )}
      </div>

      <div className="db-panel-footer">
         <div className="db-footer-left">
           {hasResult && !isEditing && (
             <span className="db-confidence-indicator">
                ✨ OCR güveni: %{Math.round(overallConfidence * 100)}
             </span>
           )}
         </div>
         <div className="db-footer-right">
           {hasResult && !isEditing && (
             <button className="db-action-btn" onClick={handleEdit}>
               Metni Düzenle <Edit2 className="w-4 h-4 ml-1 inline-block" />
             </button>
           )}
           {isEditing && (
             <>
               <button className="db-text-btn" onClick={() => setIsEditing(false)}>İptal</button>
               <button className="db-primary-btn" onClick={handleSave}>Kaydet</button>
             </>
           )}
         </div>
      </div>
    </div>
  );
}
