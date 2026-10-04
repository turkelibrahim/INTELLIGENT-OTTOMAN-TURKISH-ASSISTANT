"use client";

import { Icons } from "@/components/Icons";

export default function HelpPage() {
  return (
    <div className="db-workspace">
      <div className="db-panel" style={{ flex: 1, minHeight: '80vh' }}>
        <div className="db-panel-header" style={{ padding: '24px', height: 'auto', borderBottom: '1px dashed var(--border-primary)' }}>
          <div>
            <h2 className="db-panel-title" style={{ fontSize: '24px', marginBottom: '12px' }}>
              <span className="db-panel-icon">{Icons.help}</span>
              Yardım ve Destek
            </h2>
            <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
              Sistemi nasıl kullanabileceğinize dair dokümantasyon ve yardım içerikleri.
            </p>
          </div>
        </div>

        <div className="db-panel-content" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 24px' }}>
          <div className="db-empty-state">
            <div style={{ fontSize: '48px', marginBottom: '16px', color: 'var(--gold-muted)' }}>📚</div>
            <h3 style={{ color: 'var(--text-primary)', margin: '0 0 8px 0' }}>Yardım Merkezi Hazırlanıyor</h3>
            <p style={{ color: 'var(--text-muted)', margin: 0, maxWidth: '400px', textAlign: 'center' }}>
              Osmanlıca Belge Asistanıı kullanım kılavuzu ve S.S.S. bölümleri yakında eklenecektir.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
