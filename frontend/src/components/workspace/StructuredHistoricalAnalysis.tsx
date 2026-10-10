import React, { useState } from 'react';
import { ScrollText } from 'lucide-react';


interface Concept {
  term: string;
  meaning: string;
}

interface ParsedHistoricalData {
  summary: string;
  historicalAnalysis: string;
  concepts: Concept[];
  detailedAnalysis: string;
}

/** 
 * Safely strips ALL markdown artifacts (**, *, -, #) from text 
 * without losing meaning. 
 */
export function cleanMarkdown(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold
    .replace(/\*(.*?)\*/g, '$1')     // Remove italic
    .replace(/__(.*?)__/g, '$1')     // Remove underline
    .replace(/_(.*?)_/g, '$1')       // Remove italic 2
    .replace(/^#+\s+/gm, '')         // Remove headings (#)
    .replace(/^[-*+]\s+/gm, '')      // Remove bullets (- * +) at start of lines
    .replace(/```[\s\S]*?```/g, '')  // Remove code blocks
    .replace(/`([^`]+)`/g, '$1');    // Remove inline code
}

export function parseHistoricalContent(text: string): ParsedHistoricalData {
  const result: ParsedHistoricalData = {
    summary: '',
    historicalAnalysis: '',
    concepts: [],
    detailedAnalysis: ''
  };

  const lines = text.split('\n');
  let currentSection = 'summary'; // Default starting section
  let currentBuffer: string[] = [];

  const commitBuffer = () => {
    const textToSave = cleanMarkdown(currentBuffer.join('\n').trim());
    if (!textToSave) return;

    if (currentSection === 'summary') {
      result.summary = (result.summary ? result.summary + '\n\n' : '') + textToSave;
    } else if (currentSection === 'historicalAnalysis') {
      result.historicalAnalysis = (result.historicalAnalysis ? result.historicalAnalysis + '\n\n' : '') + textToSave;
    } else if (currentSection === 'concepts') {
      // Look for term: meaning patterns in the block
      const conceptLines = currentBuffer.join('\n').split('\n');
      let trailingAnalysis = '';
      
      conceptLines.forEach(line => {
        const trimmed = cleanMarkdown(line.trim());
        if (!trimmed) return;
        
        // Matches "Term : Meaning" or "Term - Meaning"
        const match = trimmed.match(/^([^:-]+)\s*[:-]\s*(.+)$/i);
        if (match && match[1].split(' ').length <= 4) { // term should be short
          result.concepts.push({ term: match[1].trim(), meaning: match[2].trim() });
        } else {
          trailingAnalysis += '\n' + trimmed;
        }
      });
      
      if (trailingAnalysis.trim()) {
        if (result.detailedAnalysis) result.detailedAnalysis += '\n\n' + trailingAnalysis.trim();
        else result.detailedAnalysis = trailingAnalysis.trim();
      }
    } else {
      if (result.detailedAnalysis) result.detailedAnalysis += '\n\n' + textToSave;
      else result.detailedAnalysis = textToSave;
    }
    currentBuffer = [];
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    // Check if line is a heading for a section
    const rawHeading = cleanMarkdown(line).toLowerCase();
    
    if (rawHeading === 'özet' || rawHeading === 'belge özeti' || rawHeading.includes('kısa özet')) {
      commitBuffer();
      currentSection = 'summary';
    } else if (rawHeading === 'tarihsel analiz' || rawHeading === 'tarihsel bağlam' || rawHeading.includes('bağlam')) {
      commitBuffer();
      currentSection = 'historicalAnalysis';
    } else if (rawHeading.includes('kavramlar') || rawHeading.includes('önemli kelimeler') || rawHeading.includes('terminoloji')) {
      commitBuffer();
      currentSection = 'concepts';
    } else if (rawHeading.includes('detaylı analiz') || rawHeading.includes('ek bilgiler') || rawHeading.includes('diğer')) {
      commitBuffer();
      currentSection = 'detailedAnalysis';
    } else if (rawHeading.includes('kanıt') || rawHeading.includes('kaynaklar')) {
      commitBuffer();
      currentSection = 'detailedAnalysis';
      currentBuffer.push(cleanMarkdown(line)); // Keep the heading as bold text inside detailed analysis
    } else {
      currentBuffer.push(line);
    }
  }
  commitBuffer();

  // Fallback: If AI just dumped everything without headers, treat it all as historical analysis
  if (!result.summary && !result.historicalAnalysis && !result.detailedAnalysis && result.concepts.length === 0) {
    result.historicalAnalysis = cleanMarkdown(text);
  }

  return result;
}

function renderPremiumParagraphs(text: string) {
  if (!text) return null;
  const paragraphs = text.split('\n\n').filter(Boolean);
  
  return paragraphs.map((para, i) => (
    <p key={i} className="mb-5 text-[var(--ota-text)] leading-[1.8] max-w-[75ch] text-[15px] text-justify tracking-wide">
      {para.trim()}
    </p>
  ));
}

interface Props {
  rawText: string;
}

export default function StructuredHistoricalAnalysis({ rawText }: Props) {
  const data = parseHistoricalContent(rawText);

  const hasSummary = !!data.summary;
  const hasHistoricalAnalysis = !!data.historicalAnalysis;
  const hasConcepts = data.concepts.length > 0;
  const hasDetailedAnalysis = !!data.detailedAnalysis;

  if (!hasSummary && !hasHistoricalAnalysis && !hasConcepts && !hasDetailedAnalysis) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center opacity-70">
        <span className="text-5xl mb-4 text-[var(--ota-text-muted)]"><ScrollText className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>
        <h3 className="font-serif text-lg text-[var(--ota-text)] mb-2">Tarihsel Analiz Bulunamadı</h3>
        <p className="text-sm text-[var(--ota-text-muted)] max-w-xs">
          Bu belge için yeterli bağlam çıkarılamadı veya OCR metni okunamadı.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-12 w-full max-w-[900px] mx-auto pb-12 pt-4">
      
      {/* BELGE ÖZETİ */}
      {hasSummary && (
        <section className="relative">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-1.5 h-6 bg-[var(--ota-gold)] rounded-full"></div>
            <h3 className="text-xl font-serif font-bold text-[var(--ota-text)] uppercase tracking-widest">
              Belge Özeti
            </h3>
          </div>
          <div className="bg-[var(--ota-surface)]/80 border border-[var(--ota-border)] rounded-2xl p-6 lg:p-8 shadow-sm">
            {renderPremiumParagraphs(data.summary)}
          </div>
        </section>
      )}

      {/* TARİHSEL ANALİZ */}
      {hasHistoricalAnalysis && (
        <section className="relative">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-1.5 h-6 bg-[var(--ota-ocean)] rounded-full"></div>
            <h3 className="text-xl font-serif font-bold text-[var(--ota-text)] uppercase tracking-widest">
              Tarihsel Analiz
            </h3>
          </div>
          <div className="px-2 lg:px-4">
            {renderPremiumParagraphs(data.historicalAnalysis)}
          </div>
        </section>
      )}

      {/* ÖNEMLİ TARİHSEL KAVRAMLAR */}
      {hasConcepts && (
        <section className="relative">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-1.5 h-6 bg-[var(--ota-iznik-turquoise)] rounded-full"></div>
            <h3 className="text-xl font-serif font-bold text-[var(--ota-text)] uppercase tracking-widest">
              Önemli Tarihsel Kavramlar
            </h3>
          </div>
          
          {/* 1 column mobile, 2 columns desktop */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-6 px-2 lg:px-4">
            {data.concepts.map((c, i) => (
              <div 
                key={i} 
                className="group bg-[var(--ota-bg-2)]/30 hover:bg-[var(--ota-surface)] border border-[var(--ota-border)] hover:border-[var(--ota-iznik-turquoise)]/50 p-5 rounded-xl transition-all duration-300 shadow-sm hover:shadow-md flex flex-col gap-3"
              >
                <div className="flex items-center justify-between border-b border-[var(--ota-border)] pb-3">
                  <h4 className="font-bold text-[var(--ota-text)] text-base font-serif capitalize tracking-wide group-hover:text-[var(--ota-iznik-turquoise)] transition-colors">
                    {c.term}
                  </h4>
                  <span className="text-[10px] uppercase font-bold text-[var(--ota-text-muted)] bg-[var(--ota-bg-1)] px-2 py-1 rounded">Kavram</span>
                </div>
                <p className="text-sm text-[var(--ota-text-muted)] leading-[1.6]">
                  {c.meaning}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* DETAYLI ANALİZ / KANIT / KAYNAKLAR */}
      {hasDetailedAnalysis && (
        <section className="relative mt-4">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-1.5 h-6 bg-[var(--ota-text-muted)] rounded-full"></div>
            <h3 className="text-xl font-serif font-bold text-[var(--ota-text)] uppercase tracking-widest">
              Detaylı Analiz & Ek Bağlam
            </h3>
          </div>
          <div className="bg-[var(--ota-bg-2)]/10 border border-[var(--ota-border)]/60 rounded-2xl p-6 lg:p-8">
            {renderPremiumParagraphs(data.detailedAnalysis)}
          </div>
        </section>
      )}

    </div>
  );
}
