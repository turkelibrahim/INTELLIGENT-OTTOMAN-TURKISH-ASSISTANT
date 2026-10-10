"use client";

import { useState } from "react";
import { Icons } from "@/components/Icons";
import { CheckCircle, Book, Copy, Edit2 } from 'lucide-react';


export default function ModernTurkishPanel({
  modernLines,
  hasResult,
  overallConfidence,
  onCopy,
  onSave
}: {
  modernLines: string[];
  hasResult: boolean;
  overallConfidence: number;
  onCopy: () => void;
  onSave?: (newText: string) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState("");

  const fullText = modernLines.join("\n");

  const handleEdit = () => {
    setEditText(fullText);
    setIsEditing(true);
  };

  const handleSave = () => {
    setIsEditing(false);
    if (onSave) onSave(editText);
  };

  return (
    <div className="db-panel">
      <div className="db-panel-header">
        <h2 className="db-panel-title">
          <span className="db-panel-icon"><Book className="w-5 h-5 text-current" /></span>
          Günümüz Türkçesi
        </h2>
        <div className="db-panel-actions">
          <button className="db-icon-btn flex items-center justify-center" onClick={onCopy} title="Çeviriyi Kopyala"><Copy className="w-4 h-4 text-current" /></button>
        </div>
      </div>
      
      <div className="db-panel-content">
        {!hasResult ? (
           <div className="db-empty-state">
             <p>OCR tamamlandıktan sonra Günümüz Türkçesi burada gösterilecek.</p>
           </div>
        ) : modernLines.length === 0 ? (
           <div className="db-empty-state">Çeviri bulunamadı.</div>
        ) : isEditing ? (
           <textarea 
             className="db-editor-textarea" 
             value={editText}
             onChange={(e) => setEditText(e.target.value)}
           />
        ) : (
           <div className="db-text-content">
             {modernLines.map((line, index) => (
                <div key={index} className="db-text-line">
                  <span className="db-line-text">{line}</span>
                </div>
             ))}
           </div>
        )}
      </div>

      <div className="db-panel-footer">
         <div className="db-footer-left">
           {hasResult && !isEditing && (
             <span className="db-confidence-indicator">
                <CheckCircle className="w-5 h-5 inline-block mr-1 align-text-bottom" /> Çeviri güveni: Yüksek
             </span>
           )}
         </div>
         <div className="db-footer-right">
           {hasResult && !isEditing && (
             <button className="db-action-btn" onClick={handleEdit}>
               Çeviriyi Düzenle <Edit2 className="w-4 h-4 ml-1 inline-block" />
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
