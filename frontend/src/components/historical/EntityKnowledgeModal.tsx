import React, { useEffect, useState } from "react";
import { Icons } from "@/components/Icons";

interface EntityKnowledgeModalProps {
  isOpen: boolean;
  onClose: () => void;
  entityName: string;
  description: string;
}

export function EntityKnowledgeModal({ isOpen, onClose, entityName, description }: EntityKnowledgeModalProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    if (isOpen) {
      timeoutId = setTimeout(() => setIsVisible(true), 10);
    } else {
      timeoutId = setTimeout(() => setIsVisible(false), 300); // Wait for transition
    }
    return () => clearTimeout(timeoutId);
  }, [isOpen]);

  if (!isOpen && !isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className={`fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0'}`} 
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className={`relative w-full max-w-lg bg-slate-800/90 border border-amber-500/20 rounded-2xl shadow-2xl overflow-hidden transition-all duration-300 ${isOpen ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-4 scale-95'}`}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-amber-500/10 bg-slate-900/40">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
              {Icons.book}
            </div>
            <div>
              <h3 className="text-sm font-semibold text-amber-500/70 tracking-widest uppercase text-[10px]">Tarihi Bilgi</h3>
              <h2 className="text-lg font-medium text-slate-100 leading-none">{entityName}</h2>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
            aria-label="Kapat"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        
        {/* Body */}
        <div className="p-6 max-h-[60vh] overflow-y-auto custom-scrollbar">
          {description && description !== "Tespit edilemedi" ? (
            <div className="prose prose-sm prose-invert prose-amber max-w-none">
              <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">{description}</p>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-slate-500 gap-3">
              <div className="w-12 h-12 rounded-full border border-slate-700 flex items-center justify-center opacity-50">
                {Icons.search}
              </div>
              <p>Bu varlık hakkında detaylı ansiklopedik bilgi bulunamadı.</p>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="px-6 py-4 border-t border-amber-500/10 bg-slate-900/40 flex justify-end">
          <button 
            onClick={onClose}
            className="px-4 py-2 bg-slate-700/50 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-medium transition-colors"
          >
            Kapat
          </button>
        </div>
      </div>
    </div>
  );
}
