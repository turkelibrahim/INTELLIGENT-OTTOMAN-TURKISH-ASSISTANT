"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { documentsApi, type DocumentResponse } from "@/lib/api";
import { saveActiveDocumentContext } from "@/lib/documentContext";
import { Icons } from "@/components/Icons";
import { Database, FileText, Search, Archive } from 'lucide-react';


export default function ArchivePage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState("Tümü");
  const [search, setSearch] = useState("");

  const loadArchive = async () => {
    setIsLoading(true);
    try {
      const res = await documentsApi.list({ status_filter: "archived", page_size: 50 });
      setDocuments(res.documents);
    } catch (err) {
      console.error("Arşiv yüklenemedi", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => loadArchive(), 0);
    return () => clearTimeout(timer);
  }, []);

  const toggleArchive = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await documentsApi.toggleArchive(id);
      loadArchive();
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenDoc = async (doc: DocumentResponse) => {
    try {
      const response = await documentsApi.getResult(doc.id);
      saveActiveDocumentContext(response);
      router.push("/dashboard");
    } catch (err) {
      alert("Belge detayı yüklenemedi.");
    }
  };

  const categories = ["Tümü", "Vakfiye", "Ferman", "Defter", "Mektup", "Diğer"];

  const filteredDocs = documents.filter(doc => {
    if (filter !== "Tümü" && doc.title.indexOf(filter) === -1) return false;
    if (search && !doc.title.toLowerCase().includes(search.toLowerCase()) && !doc.original_filename.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="w-full p-4 lg:p-8 animate-in slide-in-from-bottom-4 fade-in duration-700">
      <div className="glass-panel min-h-[80vh] flex flex-col rounded-2xl overflow-hidden shadow-[var(--glass-shadow)] border border-[var(--ota-border)]">
        
        {/* Header */}
        <header className="ota-page-header">
          <div className="ota-page-header-inner">
            <div className="ota-page-header-icon" aria-hidden="true">
              <span className="text-2xl drop-shadow-md"><Archive className="w-8 h-8 text-current" /></span>
            </div>
            <div>
              <h1 className="ota-page-title">Arşiv</h1>
              <p className="ota-page-subtitle">Tüm belgelerinizin yönetim ve arşivi.</p>
            </div>
          </div>
          
          <button onClick={() => router.push('/dashboard')} className="ota-btn-primary flex items-center gap-2">
            <span>+</span> Yeni Belge
          </button>
        </header>

        {/* Filters & Search */}
        <div className="p-6 border-b border-[var(--ota-border)] bg-[var(--ota-bg)] flex flex-col md:flex-row items-center gap-4 justify-between">
          <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0 custom-scrollbar">
            {categories.map(c => (
              <button 
                key={c}
                onClick={() => setFilter(c)}
                className={`whitespace-nowrap px-4 py-2 text-sm font-medium rounded-full transition-all border ${filter === c ? 'bg-[var(--ota-gold-dim)] text-[var(--ota-gold)] border-[var(--ota-gold)]/30' : 'bg-[var(--ota-bg-2)] text-[var(--ota-text-muted)] border-[var(--ota-border)] hover:text-[var(--ota-text)] hover:border-[var(--ota-border-hover)]'}`}
              >
                {c}
              </button>
            ))}
          </div>

          <div className="relative w-full md:w-64 flex-shrink-0">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--ota-text-muted)]"><Search className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>
            <input 
              type="text" 
              placeholder="Belge adı, içerik veya tarih ara..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-[var(--ota-bg-2)] border border-[var(--ota-border)] text-[var(--ota-text)] rounded-full pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-[var(--ota-gold)]/50 transition-colors"
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 bg-[var(--ota-bg)]">
          {isLoading ? (
            <div className="flex justify-center items-center h-full text-[var(--ota-text-muted)] font-medium">Yükleniyor...</div>
          ) : filteredDocs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-10 opacity-70">
              <div className="mb-4 opacity-50"><Database className="w-16 h-16 inline-block text-[var(--ota-text-muted)]" /></div>
              <h3 className="text-[var(--ota-text)] text-lg font-medium mb-2">Arşiviniz Boş</h3>
              <p className="text-[var(--ota-text-muted)] text-sm max-w-sm text-center">
                Arama kriterlerine uygun belge bulunamadı veya arşivinizde henüz belge yok.
              </p>
            </div>
          ) : (
            <div className="w-full overflow-x-auto custom-scrollbar">
              <table className="w-full text-left border-collapse min-w-[800px]">
                <thead>
                  <tr className="border-b border-[var(--ota-border)] text-[var(--ota-text-muted)] text-xs uppercase tracking-wider">
                    <th className="pb-3 font-medium px-4">Belge</th>
                    <th className="pb-3 font-medium px-4">Tür</th>
                    <th className="pb-3 font-medium px-4">Tarih</th>
                    <th className="pb-3 font-medium px-4 text-center">Güven</th>
                    <th className="pb-3 font-medium px-4">Durum</th>
                    <th className="pb-3 font-medium px-4 text-right">İşlemler</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--ota-border)]">
                  {filteredDocs.map((doc) => (
                    <tr key={doc.id} className="hover:bg-[var(--ota-bg-2)]/50 transition-colors group cursor-pointer" onClick={() => handleOpenDoc(doc)}>
                      <td className="py-4 px-4 flex items-center gap-4">
                        <div className="w-10 h-12 bg-[var(--ota-bg-2)] rounded border border-[var(--ota-border)] flex items-center justify-center text-xl shadow-sm">
                          <FileText className="w-5 h-5 inline-block mr-1 align-text-bottom" />
                        </div>
                        <div className="flex flex-col max-w-[200px] lg:max-w-[300px]">
                          <span className="font-semibold text-[var(--ota-text)] truncate group-hover:text-[var(--ota-gold)] transition-colors">{doc.title}</span>
                          <span className="text-xs text-[var(--ota-text-muted)] truncate">{doc.original_filename}</span>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <span className="text-sm text-[var(--ota-text-2)]">{doc.title.includes('Ferman') ? 'Ferman' : doc.title.includes('Defter') ? 'Defter' : 'Vakfiye'}</span>
                      </td>
                      <td className="py-4 px-4 text-sm text-[var(--ota-text-2)]">
                        {new Date(doc.created_at).toLocaleDateString("tr-TR")}
                      </td>
                      <td className="py-4 px-4 text-center">
                        <span className="inline-block px-2 py-1 bg-[var(--ota-success)]/10 text-[var(--ota-success)] text-xs font-semibold rounded-md border border-[var(--ota-success)]/20">
                          %86
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <span className="text-xs font-medium px-2 py-1 bg-[var(--ota-teal-active)] text-[var(--ota-iznik-turquoise)] rounded border border-[var(--ota-iznik-turquoise)]/20 uppercase">
                          Arşivlendi
                        </span>
                      </td>
                      <td className="py-4 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button 
                            onClick={(e) => toggleArchive(doc.id, e)}
                            title="Arşivden Çıkar"
                            className="p-1.5 rounded-md text-[var(--ota-text-muted)] hover:text-[var(--ota-text)] hover:bg-[var(--ota-bg-2)] transition-colors border border-transparent hover:border-[var(--ota-border)]"
                          >
                            ↑ Çıkar
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
