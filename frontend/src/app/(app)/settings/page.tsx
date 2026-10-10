"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, systemApi, type SystemStatusResponse } from "@/lib/api";
import {   AlertTriangle, Binary, Brain, Database, Eye, MessageSquare, Search, Settings , Key , FileText } from "lucide-react";


export default function SettingsPage() {
  const router = useRouter();
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    
    systemApi.getStatus()
      .then(res => setStatus(res))
      .catch(err => setError(err instanceof Error ? err.message : "Sistem bilgileri yüklenemedi."));
  }, [router]);

  return (
    <div className="w-full max-w-6xl mx-auto p-4 lg:p-8 animate-in slide-in-from-bottom-4 fade-in duration-700 space-y-8">
      
      {/* ── Başlık & Açıklama ── */}
      <div className="relative glass-panel p-8 lg:p-10 rounded-3xl border border-[var(--ota-border)] shadow-[var(--glass-shadow)] bg-[var(--ota-surface-dark)]/90 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-[var(--ota-gold)]/5 via-transparent to-[var(--ota-gold)]/10 pointer-events-none" />
        <div className="absolute inset-0 opacity-[0.03] bg-[url('/auth/floral-pattern.png')] bg-repeat-x bg-[length:120px] pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div>
            <h1 className="text-3xl font-serif font-bold text-[var(--ota-text)] mb-2 drop-shadow-sm">Yönetim ve Ayarlar</h1>
            <p className="text-[var(--ota-text-muted)] text-sm max-w-2xl font-medium">
              Sistem durumu, yapay zekâ modelleri ve uygulama yapılandırması.
            </p>
          </div>
          {status && (
            <div className="flex gap-4">
              <div className="text-right">
                <div className="text-xs text-[var(--ota-text-muted)] uppercase tracking-wider font-bold mb-1">Versiyon</div>
                <div className="font-mono text-[var(--ota-gold)] font-bold">{status.system.version} {status.system.debug_mode && <span className="text-[var(--ota-ruby)] text-xs ml-1">(Geliştirici Modu)</span>}</div>
              </div>
              <div className="w-px bg-[var(--ota-border)]"></div>
              <div className="text-right">
                <div className="text-xs text-[var(--ota-text-muted)] uppercase tracking-wider font-bold mb-1">Durum</div>
                <div className="flex items-center gap-2 text-[var(--ota-success)] font-bold text-sm">
                  <span className="w-2 h-2 rounded-full bg-[var(--ota-success)] animate-pulse"></span> {status.system.status}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-[var(--ota-ruby)]/10 border border-[var(--ota-ruby)]/30 text-[var(--ota-ruby)] rounded-xl text-sm flex items-center gap-3 font-medium shadow-sm">
          <span className="text-xl"><AlertTriangle className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> {error}
        </div>
      )}

      {!status && !error ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-12 h-12 border-4 border-[var(--ota-gold)]/30 border-t-[var(--ota-gold)] rounded-full animate-spin"></div>
        </div>
      ) : status ? (
        <div className="flex flex-col gap-8">
          
          {/* ── Sistem Analizi ── */}
          <section>
            <h2 className="text-lg font-serif font-bold text-[var(--ota-text)] mb-4 flex items-center gap-3">
              <span className="text-[var(--ota-gold)] text-xl"><Settings className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> Sistem Analizi
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="glass-panel p-5 rounded-2xl border border-[var(--ota-border)] text-center hover:border-[var(--ota-gold)]/30 transition-colors">
                <div className="text-2xl font-serif font-bold text-[var(--ota-text)] mb-2 truncate">{status.models.ocr_engine}</div>
                <div className="text-[10px] text-[var(--ota-text-muted)] font-bold uppercase tracking-wider">Ana OCR Motoru</div>
              </div>
              <div className="glass-panel p-5 rounded-2xl border border-[var(--ota-border)] text-center hover:border-[var(--ota-gold)]/30 transition-colors">
                <div className="text-2xl font-serif font-bold text-[var(--ota-success)] mb-2">Aktif</div>
                <div className="text-[10px] text-[var(--ota-text-muted)] font-bold uppercase tracking-wider">RAG Durumu</div>
              </div>
              <div className="glass-panel p-5 rounded-2xl border border-[var(--ota-border)] text-center hover:border-[var(--ota-gold)]/30 transition-colors">
                <div className="text-2xl font-serif font-bold text-[var(--ota-gold)] mb-2">{status.system.data_privacy}</div>
                <div className="text-[10px] text-[var(--ota-text-muted)] font-bold uppercase tracking-wider">Veri Gizliliği</div>
              </div>
              <div className="glass-panel p-5 rounded-2xl border border-[var(--ota-border)] text-center hover:border-[var(--ota-gold)]/30 transition-colors">
                <div className="text-2xl font-serif font-bold text-[var(--ota-success)] mb-2">
                  {status.system.status}
                </div>
                <div className="text-[10px] text-[var(--ota-text-muted)] font-bold uppercase tracking-wider">Backend API</div>
              </div>
              <div className="glass-panel p-5 rounded-2xl border border-[var(--ota-border)] text-center hover:border-[var(--ota-gold)]/30 transition-colors">
                <div className={`text-2xl font-serif font-bold mb-2 ${status.api_integrations.nvidia_nim === "active" ? "text-[var(--ota-success)]" : "text-[var(--ota-text-muted)]"}`}>
                  {status.api_integrations.nvidia_nim === "active" ? "Yapılandırıldı" : "Yapılandırılmadı"}
                </div>
                <div className="text-[10px] text-[var(--ota-text-muted)] font-bold uppercase tracking-wider">NVIDIA NIM</div>
              </div>
            </div>
          </section>

          {/* ── AI Modelleri & OCR ── */}
          <section>
            <h2 className="text-lg font-serif font-bold text-[var(--ota-text)] mb-4 flex items-center gap-3">
              <span className="text-[var(--ota-gold)] text-xl"><Brain className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> Model Kartları
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { title: "OCR Motoru", value: status.models.ocr_engine, detail: status.models.ocr_model, icon: <FileText className="w-5 h-5 inline-block mr-1 align-text-bottom" />, status: "Yüklü" },
                { title: "Ana LLM (Transliterasyon)", value: status.models.llm, detail: "Kelime Dağarcığı & Çeviri", icon: <MessageSquare className="w-5 h-5 inline-block mr-1 align-text-bottom" />, status: "Bağlı" },
                { title: "Varlık İsmi Tanıma (NER)", value: status.models.ner, detail: "Lokasyon & Kişi Tespiti", icon: <Search className="w-5 h-5 inline-block mr-1 align-text-bottom" />, status: "Aktif" },
                { title: "Vektör Veritabanı", value: status.models.vector_db, detail: "Gelişmiş Semantik Arama", icon: <Database className="w-5 h-5 inline-block mr-1 align-text-bottom" />, status: "Yerel" },
                { title: "Embedding Modeli", value: status.models.embedding, detail: "Metin Vektörleştirme", icon: <Binary className="w-5 h-5 inline-block mr-1 align-text-bottom" />, status: "Aktif" },
                { title: "Görüntü İşleme Modeli", value: status.api_integrations.nvidia_vision_model || "Devre Dışı", detail: "NVIDIA Vision", icon: <Eye className="w-5 h-5 inline-block mr-1 align-text-bottom" />, status: status.api_integrations.nvidia_vision_model ? "Bulut" : "Pasif" },
              ].map((model, idx) => (
                <div key={idx} className="glass-panel p-6 rounded-2xl border border-[var(--ota-border)] flex flex-col justify-between hover:border-[var(--ota-gold)]/30 transition-all bg-[var(--ota-surface)] shadow-sm">
                  <div className="flex justify-between items-start mb-4">
                    <div className="w-10 h-10 rounded-xl bg-[var(--ota-bg-2)]/80 border border-[var(--ota-border)] flex items-center justify-center text-lg shadow-inner">
                      {model.icon}
                    </div>
                    <span className="px-2 py-1 bg-[var(--ota-success)]/10 text-[var(--ota-success)] border border-[var(--ota-success)]/20 text-[10px] font-bold uppercase rounded tracking-wider">
                      {model.status}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-[10px] text-[var(--ota-text-muted)] font-bold uppercase tracking-wider mb-1">{model.title}</h3>
                    <p className="text-sm font-bold text-[var(--ota-text)] truncate font-mono">{model.value}</p>
                    <p className="text-xs text-[var(--ota-text-muted)] mt-2 opacity-80">{model.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* ── API Entegrasyonları (NVIDIA vb.) ── */}
          <section>
            <h2 className="text-lg font-serif font-bold text-[var(--ota-text)] mb-4 flex items-center gap-3">
              <span className="text-[var(--ota-gold)] text-xl"><Key className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span> Güvenlik & API
            </h2>
            <div className="glass-panel p-6 lg:p-8 rounded-2xl border border-[var(--ota-border)] bg-[var(--ota-surface)] shadow-sm">
              <div className="flex flex-col md:flex-row gap-8 items-start md:items-center justify-between border-b border-[var(--ota-border)] pb-6 mb-6">
                <div>
                  <h3 className="text-base font-bold text-[var(--ota-text)] mb-1 flex items-center gap-2">
                    NVIDIA API (NIM) 
                    {status.api_integrations.nvidia_nim === "active" ? (
                      <span className="text-[10px] bg-[var(--ota-success)]/10 text-[var(--ota-success)] px-2 py-0.5 rounded border border-[var(--ota-success)]/20 uppercase tracking-wider font-bold">Bağlı</span>
                    ) : (
                      <span className="text-[10px] bg-[var(--ota-ruby)]/10 text-[var(--ota-ruby)] px-2 py-0.5 rounded border border-[var(--ota-ruby)]/20 uppercase tracking-wider font-bold">Pasif</span>
                    )}
                  </h3>
                  <p className="text-xs text-[var(--ota-text-muted)]">Gelişmiş bulut tabanlı GPU hızlandırması ve yüksek başarımlı LLM yetenekleri.</p>
                </div>
                <div className="w-full md:w-auto flex gap-3">
                  <span className="bg-[var(--ota-bg-2)] border border-[var(--ota-border)] rounded-xl px-4 py-2 text-sm text-[var(--ota-text-muted)] opacity-80 font-mono shadow-inner">API Anahtarı Güvenli Bir Şekilde Saklanıyor</span>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-[var(--ota-bg-2)]/30 rounded-xl p-5 border border-[var(--ota-border)]">
                  <div className="text-[10px] text-[var(--ota-text-muted)] font-bold uppercase tracking-wider mb-2">Bulut Yönlendirici Model</div>
                  <div className="text-sm font-bold text-[var(--ota-text)] font-mono mb-1">{status.api_integrations.nvidia_primary_model || "Devre Dışı"}</div>
                  <p className="text-xs text-[var(--ota-text-muted)] opacity-80">Yoğun işlemlerde devreye giren birincil bulut modeli.</p>
                </div>
                <div className="bg-[var(--ota-bg-2)]/30 rounded-xl p-5 border border-[var(--ota-border)]">
                  <div className="text-[10px] text-[var(--ota-text-muted)] font-bold uppercase tracking-wider mb-2">Fallback (Yedek) Model</div>
                  <div className="text-sm font-bold text-[var(--ota-text)] font-mono mb-1">{status.models.fallback_model}</div>
                  <p className="text-xs text-[var(--ota-text-muted)] opacity-80">Local model başarısız olduğunda kullanılacak yedek LLM.</p>
                </div>
              </div>
            </div>
          </section>

        </div>
      ) : null}
    </div>
  );
}
