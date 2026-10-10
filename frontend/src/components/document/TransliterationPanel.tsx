"use client";

import { useState } from "react";
import { Icons } from "@/components/Icons";
import { Copy, Info } from 'lucide-react';

export default function TransliterationPanel({
  transliterationLines,
  hasResult,
  onCopy
}: {
  transliterationLines: string[];
  hasResult: boolean;
  onCopy: () => void;
}) {
  const [isOpen, setIsOpen] = useState(true);

  if (!hasResult && transliterationLines.length === 0) {
    return null; // or could show empty state, but design shows it collapsible at bottom
  }

  return (
    <div className={`db-panel-bottom ${isOpen ? "open" : "closed"}`}>
      <div className="db-panel-header" onClick={() => setIsOpen(!isOpen)} style={{ cursor: 'pointer' }}>
        <h2 className="db-panel-title">
          <span className="db-panel-icon">Aa</span>
          Latin Harfli Okunuş (İsteğe Bağlı) <Info className="w-4 h-4 ml-1 inline-block" />
        </h2>
        <div className="db-panel-actions">
           <button className="db-text-btn" onClick={(e) => { e.stopPropagation(); setIsOpen(!isOpen); }}>
             Aç / Kapat {isOpen ? "▲" : "▼"}
           </button>
        </div>
      </div>
      
      {isOpen && (
        <div className="db-panel-content">
           <div className="db-text-content">
             {transliterationLines.length === 0 ? (
               <div className="db-empty-state">Latin harfli okunuş oluşturulduğunda burada gösterilecek.</div>
             ) : (
               transliterationLines.map((line, index) => (
                  <div key={index} className="db-text-line">
                    <span className="db-line-text">{line}</span>
                  </div>
               ))
             )}
           </div>
           <button 
             className="db-icon-btn absolute-top-right" 
             onClick={onCopy} 
             title="Okunuşu Kopyala"
             style={{ position: 'absolute', top: 16, right: 120 }}
           >
             <Copy className="w-4 h-4 text-current" />
           </button>
        </div>
      )}
    </div>
  );
}
