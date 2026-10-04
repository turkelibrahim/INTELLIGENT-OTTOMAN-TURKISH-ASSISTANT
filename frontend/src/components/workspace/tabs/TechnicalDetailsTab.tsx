"use client";

import type { FullDocumentAnalysisResponse } from "@/lib/api";
import { mapConfidenceToPercent } from "@/lib/viewModel";

interface Props {
  result: FullDocumentAnalysisResponse;
}

// İlerleme çubuğu bileşeni (Progress Bar)
function ProgressBar({ label, value, tooltip }: { label: string; value: string; tooltip?: string }) {
  if (!value || value === "") return null;
  
  const numValue = parseInt(value.replace("%", ""), 10) || 0;
  
  // Rengi skora göre belirle
  let barColor = "bg-red-500";
  let textColor = "text-red-400";
  if (numValue >= 80) {
    barColor = "bg-emerald-500";
    textColor = "text-emerald-400";
  } else if (numValue >= 60) {
    barColor = "bg-amber-500";
    textColor = "text-amber-400";
  }

  return (
    <div className="flex flex-col gap-1.5 mb-4 last:mb-0" title={tooltip}>
      <div className="flex justify-between items-end">
        <span className="text-sm font-medium text-slate-300">{label}</span>
        <span className={`text-sm font-bold ${textColor}`}>{value}</span>
      </div>
      <div className="w-full bg-slate-800 rounded-full h-2.5 shadow-inner overflow-hidden border border-slate-700">
        <div 
          className={`h-2.5 rounded-full ${barColor} transition-all duration-1000 ease-out`} 
          style={{ width: `${numValue}%` }}
        ></div>
      </div>
    </div>
  );
}

// Bilgi satırı bileşeni (Info Row)
function InfoRow({ label, value }: { label: string; value?: string | number | boolean | null }) {
  if (value == null || value === "") return null;
  return (
    <div className="flex justify-between items-center py-2 border-b border-slate-700/50 last:border-0">
      <span className="text-sm text-slate-400">{label}</span>
      <span className="text-sm font-medium text-slate-200">{String(value)}</span>
    </div>
  );
}

export default function TechnicalDetailsTab({ result }: Props) {
  const ocrPct = mapConfidenceToPercent(result.confidence?.ocr);
  const translit = mapConfidenceToPercent(result.confidence?.transliteration);
  const modern = mapConfidenceToPercent(result.confidence?.modern_turkish);
  const entities = mapConfidenceToPercent(result.confidence?.entities);
  const retrieval = mapConfidenceToPercent(result.confidence?.retrieval_strength);
  const coverage = mapConfidenceToPercent(result.confidence?.evidence_coverage);

  return (
    <div className="p-6 h-full overflow-y-auto custom-scrollbar bg-slate-900/50">
      
      <div className="mb-8">
        <h3 className="text-xl font-bold text-slate-100 mb-2">Sistem Analiz Raporu</h3>
        <p className="text-sm text-slate-400">Belgenin yapay zeka tarafından ne kadar başarılı işlendiğini ve kalitesini gösteren kullanıcı dostu özet.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Sol Kolon: Grafiksel Kalite Skorları */}
        <div className="flex flex-col gap-6">
          <section className="bg-slate-800/80 p-5 rounded-2xl border border-slate-700 shadow-lg">
            <h4 className="text-base font-semibold text-amber-500 mb-5 flex items-center gap-2">
              <span>🎯</span> Okuma ve Çeviri Başarısı
            </h4>
            <ProgressBar label="Görüntüden Metin Okuma (OCR)" value={ocrPct} />
            <ProgressBar label="Latin Harflerine Çeviri" value={translit} />
            <ProgressBar label="Günümüz Türkçesine Aktarım" value={modern} />
          </section>

          <section className="bg-slate-800/80 p-5 rounded-2xl border border-slate-700 shadow-lg">
            <h4 className="text-base font-semibold text-amber-500 mb-5 flex items-center gap-2">
              <span>🧠</span> Yapay Zeka Zeka Puanları
            </h4>
            <ProgressBar 
              label="Özel İsim/Tarih Bulma Yeteneği" 
              value={entities} 
              tooltip="Belgedeki kişi, yer ve tarihleri doğru tespit etme başarısı"
            />
            <ProgressBar 
              label="Tarihi Arka Plan Tarama" 
              value={retrieval} 
              tooltip="Belgeyle ilgili tarihi olayları veri tabanından doğru getirme başarısı"
            />
            <ProgressBar 
              label="Belge Doğruluk Oranı" 
              value={coverage} 
              tooltip="Elde edilen bilgilerin belge içeriğiyle ne kadar örtüştüğü"
            />
          </section>
        </div>

        {/* Sağ Kolon: Belge Özeti ve Uyarılar */}
        <div className="flex flex-col gap-6">
          <section className="bg-slate-800/80 p-5 rounded-2xl border border-slate-700 shadow-lg">
            <h4 className="text-base font-semibold text-emerald-400 mb-4 flex items-center gap-2">
              <span>📄</span> Belge Künyesi
            </h4>
            <div className="flex flex-col">
              <InfoRow label="Dosya Adı" value={result.document.filename} />
              <InfoRow label="Belge Türü" value={result.document.document_type} />
              <InfoRow label="Tespit Edilen Dil" value={result.document.language} />
              <InfoRow label="Toplam Sayfa" value={result.document.page_count} />
              <InfoRow label="Okunan Satır Sayısı" value={result.ocr.lines.length} />
            </div>
          </section>

          <section className="bg-slate-800/80 p-5 rounded-2xl border border-slate-700 shadow-lg">
            <h4 className="text-base font-semibold text-emerald-400 mb-4 flex items-center gap-2">
              <span>⚙️</span> Kullanılan Motorlar
            </h4>
            <div className="flex flex-col">
              <InfoRow label="Okuma (OCR) Motoru" value={result.ocr.engine} />
              <InfoRow label="Yedek Sistem Devrede mi?" value={result.ocr.fallback_used ? "Evet" : "Hayır"} />
              <InfoRow label="Çeviri Sağlayıcısı" value={result.modern_turkish.provider} />
            </div>
          </section>

          {(result.warnings.length > 0 || result.uncertainties.length > 0 || result.image_processing.warnings.length > 0) && (
            <section className="bg-red-900/20 p-5 rounded-2xl border border-red-500/30 shadow-lg">
              <h4 className="text-base font-semibold text-red-400 mb-4 flex items-center gap-2">
                <span>⚠️</span> Sistem Uyarıları
              </h4>
              <ul className="list-disc list-inside text-sm text-red-300 flex flex-col gap-2">
                {result.image_processing.warnings.map((w, i) => <li key={`img-${i}`}>{w}</li>)}
                {result.uncertainties.map((u, i) => <li key={`unc-${i}`}>{u}</li>)}
                {result.warnings.map((w, i) => <li key={`warn-${i}`}>{w}</li>)}
              </ul>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
