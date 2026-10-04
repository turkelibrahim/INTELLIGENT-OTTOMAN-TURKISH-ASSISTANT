"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken, analysisApi, ApiError, type AnalysisStage } from "@/lib/api";
import { saveActiveDocumentContext } from "@/lib/documentContext";
import AnalysisProgress from "@/components/ui/AnalysisProgress";

const ACCEPTED_TYPES = ".jpg,.jpeg,.png,.tiff,.tif,.pdf";
const MAX_SIZE_MB = 50;

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  
  // Yükleme & Analiz Süreci
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [stage, setStage] = useState<AnalysisStage>("IDLE");
  const [error, setError] = useState("");

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  const handleFile = (selectedFile: File) => {
    setError("");
    if (selectedFile.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`Dosya boyutu ${MAX_SIZE_MB} MB sınırını aşıyor`);
      return;
    }
    const ext = selectedFile.name.split(".").pop()?.toLowerCase() || "";
    if (!["jpg", "jpeg", "png", "tiff", "tif", "pdf"].includes(ext)) {
      setError(`Desteklenmeyen dosya türü: .${ext}`);
      return;
    }
    setFile(selectedFile);
    if (selectedFile.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(selectedFile);
    } else {
      setPreview(null);
    }
    if (!title) {
      setTitle(selectedFile.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " "));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) { setError("Lütfen bir dosya seçin"); return; }
    if (!title.trim()) { setError("Lütfen belge başlığı girin"); return; }
    
    setIsUploading(true);
    setError("");
    setStage("UPLOADING");
    setUploadProgress(0);

    try {
      // 1. Belgeyi sunucuya gönder ve analiz işini başlat
      const job = await analysisApi.analyze(
        file,
        { title: title.trim(), description: description.trim() || undefined },
        (pct) => {
          setUploadProgress(pct);
          if (pct >= 100) setStage("PREPROCESSING");
        }
      );

      const stageForStatus = (statusValue: string): AnalysisStage => {
        const normalized = statusValue.toUpperCase();
        if (normalized.includes("OCR")) return "OCR";
        if (normalized.includes("TRANSLITER")) return "TRANSLITERATION";
        if (normalized.includes("MODERN")) return "MODERNIZATION";
        if (normalized.includes("NER")) return "ENTITY_ANALYSIS";
        if (normalized.includes("COMPLETED")) return "COMPLETE";
        if (normalized.includes("FAILED")) return "ERROR";
        return "PREPROCESSING";
      };

      const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
      let latestJob = job;
      setStage(stageForStatus(latestJob.status));
      
      // 2. Analizin durumunu periyodik olarak kontrol et (Polling)
      while (true) {
        if (latestJob.status === "COMPLETED") break;
        if (latestJob.status === "FAILED") {
          throw new ApiError(500, latestJob.error_message || "Analiz işlemi başarısız oldu");
        }
        await sleep(1500);
        latestJob = await analysisApi.getJob(latestJob.job_id);
        setStage(stageForStatus(latestJob.status));
      }

      // 3. Analiz tamamlandı, sonucu al
      const response = await analysisApi.getJobResult(latestJob.job_id);
      
      // 4. Global context'e kaydet ve Dashboard'a yönlendir
      saveActiveDocumentContext(response);
      setStage("COMPLETE");
      
      // Biraz bekle (kullanıcı tamamlandığını görsün) ve yönlendir
      setTimeout(() => router.push("/dashboard"), 1000);

    } catch (err: unknown) {
      setStage("ERROR");
      setIsUploading(false);
      if (err instanceof ApiError) setError(err.detail);
      else setError((err as Error).message || "Yükleme ve analiz sırasında hata oluştu.");
    }
  };

  const formats = [
    { label: "PDF", color: "#ef4444" },
    { label: "PNG", color: "#3b82f6" },
    { label: "JPG", color: "#22c55e" },
    { label: "TIFF", color: "#a855f7" },
  ];

  // Ekran: Analiz Süreci Gösterimi
  if (isUploading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] p-8 animate-in fade-in duration-500">
        <div className="w-full max-w-3xl glass-panel p-10 rounded-2xl border border-amber-500/20 shadow-[0_10px_40px_rgba(215,165,72,0.1)] text-center">
          <h2 className="text-2xl font-bold text-amber-500 mb-2">Belge Analiz Ediliyor</h2>
          <p className="text-slate-400 mb-10">Lütfen bekleyin, Osmanlıca belgeniz yapay zeka sistemlerimiz tarafından işleniyor.</p>
          
          <AnalysisProgress stage={stage} uploadProgress={uploadProgress} />
          
          {stage === "COMPLETE" && (
            <div className="mt-8 text-emerald-400 font-semibold animate-bounce">
              Analiz tamamlandı! Çalışma alanına yönlendiriliyorsunuz...
            </div>
          )}
          {stage === "ERROR" && (
            <div className="mt-8 text-red-400 font-semibold">
              Bir hata oluştu: {error}
              <button onClick={() => { setIsUploading(false); setStage("IDLE"); }} className="block mt-4 mx-auto text-amber-500 underline">Geri Dön ve Tekrar Dene</button>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Ekran: Dosya Seçimi ve Bilgi Girişi
  return (
    <div className="w-full p-8 animate-in slide-in-from-bottom-4 fade-in duration-700 flex justify-center items-center min-h-[80vh]">
      <div className="w-full max-w-2xl glass-panel rounded-2xl overflow-hidden shadow-lg border border-slate-700/50">
        <div className="p-8 border-b border-dashed border-slate-700/50 bg-slate-900/30">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <span className="text-amber-500 bg-amber-500/10 p-2 rounded-xl">📄</span> 
            Yeni Belge Yükle
          </h1>
          <p className="text-slate-400 text-sm mt-2">
            Osmanlıca belgenizi yükleyin, akıllı analiz motorumuz hemen çalışmaya başlasın.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-8">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-medium flex items-center gap-2">
              ⚠️ {error}
            </div>
          )}

          {/* Dropzone */}
          <div
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300 mb-6 relative group ${
              isDragging ? "border-amber-500 bg-amber-500/5" : file ? "border-emerald-500/50 bg-emerald-500/5" : "border-slate-700 hover:border-amber-500/50 hover:bg-white/5"
            }`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
            onDrop={(e) => { e.preventDefault(); setIsDragging(false); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); }}
            onClick={() => fileInputRef.current?.click()}
          >
            <input ref={fileInputRef} type="file" accept={ACCEPTED_TYPES} onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} className="hidden" />

            {file ? (
              <div className="flex flex-col items-center">
                {preview ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={preview} alt="Ön izleme" className="max-h-40 rounded-lg shadow-md border border-slate-700/50 mb-4" />
                ) : (
                  <div className="w-16 h-20 rounded-lg bg-slate-800 flex items-center justify-center border border-slate-700 mb-4 shadow-md">
                    <span className="text-lg font-bold text-amber-500">PDF</span>
                  </div>
                )}
                <p className="font-semibold text-emerald-400 mb-1">{file.name}</p>
                <p className="text-xs text-slate-400">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                <button type="button" onClick={(e) => { e.stopPropagation(); setFile(null); setPreview(null); }} className="mt-4 text-xs text-red-400 hover:text-red-300 font-medium px-3 py-1.5 rounded-md hover:bg-red-500/10 transition-colors">
                  ✕ Dosyayı Değiştir
                </button>
              </div>
            ) : (
              <div>
                <div className="w-16 h-16 rounded-2xl bg-slate-800/80 flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform shadow-inner">
                  <span className="text-2xl text-amber-500">↑</span>
                </div>
                <p className="font-medium text-slate-300 mb-2">Dosyayı sürükleyin veya seçmek için tıklayın</p>
                <p className="text-xs text-slate-500 mb-6">Maksimum dosya boyutu: {MAX_SIZE_MB} MB</p>
                <div className="flex gap-2 justify-center">
                  {formats.map(f => (
                    <span key={f.label} className="px-2.5 py-1 rounded-md text-[10px] font-bold" style={{ backgroundColor: `${f.color}15`, color: f.color, border: `1px solid ${f.color}30` }}>
                      {f.label}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Metadata Form */}
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Belge Başlığı <span className="text-red-400">*</span>
              </label>
              <input 
                required 
                value={title} 
                onChange={(e) => setTitle(e.target.value)} 
                className="w-full h-12 px-4 bg-slate-900/50 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50 transition-all" 
                placeholder="Örn: Vakfiye Belgesi 1832" 
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Açıklama</label>
              <textarea 
                value={description} 
                onChange={(e) => setDescription(e.target.value)} 
                className="w-full p-4 bg-slate-900/50 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50 transition-all resize-y min-h-[100px]" 
                placeholder="Belge hakkında kısa açıklama..." 
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4 justify-end mt-8 pt-6 border-t border-dashed border-slate-700/50">
            <button type="button" onClick={() => router.push("/dashboard")} className="px-6 py-3 rounded-xl font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 transition-colors">
              İptal
            </button>
            <button type="submit" disabled={!file} className={`px-6 py-3 rounded-xl font-bold text-slate-900 bg-amber-500 hover:bg-amber-400 transition-all shadow-[0_0_15px_rgba(245,158,11,0.3)] ${!file ? 'opacity-50 cursor-not-allowed' : ''}`}>
              Yükle ve Analizi Başlat
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
