"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";

export default function SettingsPage() {
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  return (
    <div style={{ padding: "24px", maxWidth: "900px" }}>
      <div style={{ marginBottom: "24px" }}>
        <h1 style={{ fontSize: "22px", fontWeight: 700, color: "var(--text-primary)" }}>Yönetim ve Ayarlar</h1>
        <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px" }}>
          Sistem durumu, model bilgileri ve yapılandırma ayarları.
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {/* Model Status */}
        <div className="glass-card" style={{ padding: "20px" }}>
          <h2 style={{ fontSize: "15px", fontWeight: 600, color: "var(--gold-400)", marginBottom: "14px" }}>Model Durumu (AI/ML)</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {[
              { label: "OCR Motoru", value: "Kraken (v1)", status: "Aktif" },
              { label: "Model Dosyası", value: "ottoman_recognition_final_v1.mlmodel", status: "Yüklü" },
              { label: "Modernizasyon", value: "Rule-based", status: "Aktif" },
              { label: "NER", value: "savasy/bert-base-turkish-ner", status: "Aktif" },
              { label: "Vektör Veritabanı", value: "ChromaDB", status: "Bağlı" },
            ].map(item => (
              <div key={item.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 14px", borderRadius: "8px", background: "var(--surface)", border: "1px solid var(--border)" }}>
                <div>
                  <span style={{ fontSize: "13px", color: "var(--text-primary)", fontWeight: 500 }}>{item.label}</span>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)", marginLeft: "8px" }}>{item.value}</span>
                </div>
                <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--success)" }}>● {item.status}</span>
              </div>
            ))}
          </div>
        </div>

        {/* System Metrics */}
        <div className="glass-card" style={{ padding: "20px" }}>
          <h2 style={{ fontSize: "15px", fontWeight: 600, color: "var(--gold-400)", marginBottom: "14px" }}>Sistem Analizi</h2>
          <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "14px" }}>Performans metrikleri ve kullanım bilgileri.</p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div style={{ padding: "16px", borderRadius: "10px", background: "var(--surface)", border: "1px solid var(--border)", textAlign: "center" }}>
              <div style={{ fontSize: "24px", fontWeight: 700, color: "var(--text-primary)" }}>95.6%</div>
              <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>Ortalama OCR Doğruluğu</div>
            </div>
            <div style={{ padding: "16px", borderRadius: "10px", background: "var(--surface)", border: "1px solid var(--border)", textAlign: "center" }}>
              <div style={{ fontSize: "24px", fontWeight: 700, color: "var(--text-primary)" }}>Kraken</div>
              <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>Primary OCR Engine</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
