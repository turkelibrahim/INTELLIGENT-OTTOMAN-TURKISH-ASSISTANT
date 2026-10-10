"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { documentsApi, type DocumentResponse } from "@/lib/api";
import { saveActiveDocumentContext } from "@/lib/documentContext";
import { Icons } from "@/components/Icons";
import { FileText, Search, Star } from 'lucide-react';


export default function FavoritesPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");

  const loadFavorites = async () => {
    setIsLoading(true);
    try {
      const res = await documentsApi.list({ is_favorite: true, page_size: 50 });
      setDocuments(res.documents);
    } catch (err: unknown) {
      console.error("Favoriler yüklenemedi", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadFavorites();
  }, []);

  const toggleFavorite = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await documentsApi.toggleFavorite(id);
      loadFavorites();
    } catch (err: unknown) {
      console.error("Error toggling favorite");
    }
  };

  const handleOpenDoc = async (doc: DocumentResponse) => {
    try {
      const response = await documentsApi.getResult(doc.id);
      saveActiveDocumentContext(response);
      router.push("/dashboard");
    } catch (err: unknown) {
      alert("Belge detayı yüklenemedi.");
    }
  };

  const filteredDocs = documents.filter(doc => {
    if (search && !doc.title.toLowerCase().includes(search.toLowerCase()) && !doc.original_filename.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="w-full p-4 lg:p-8 animate-in slide-in-from-bottom-4 fade-in duration-700">
      <div className="glass-panel min-h-[80vh] flex flex-col rounded-2xl overflow-hidden shadow-[var(--glass-shadow)] border border-[var(--ota-border)]">
        
        {/* Header */}
        <div className="p-6 lg:p-8 border-b border-[var(--ota-border)] bg-[var(--ota-bg-2)]/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-[var(--ota-gold-dim)] flex items-center justify-center border border-[var(--ota-border-hover)] text-[var(--ota-gold)] text-2xl">
              <Star className="w-5 h-5 inline-block mr-1 align-text-bottom" />
            </div>
            <div>
              <h2 className="text-2xl font-serif font-bold text-[var(--ota-text)] mb-1">
                Favoriler
              </h2>
              <p className="text-[var(--ota-text-muted)] text-sm">
                Sık kullandığınız veya önemli işaretlediğiniz belgeleriniz.
              </p>
            </div>
          </div>
          
          <button onClick={() => router.push('/dashboard')} className="ota-btn-primary flex items-center gap-2">
            <span>+</span> Yeni Belge
          </button>
        </div>

        {/* Filters & Search */}
        <div className="p-6 border-b border-[var(--ota-border)] bg-[var(--ota-bg)] flex flex-col md:flex-row items-center gap-4 justify-between">
          <div className="relative w-full md:w-80 flex-shrink-0">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--ota-text-muted)]"><Search className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>
            <input 
              type="text" 
              placeholder="Favorilerde ara..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-[var(--ota-bg-2)] border border-[var(--ota-border)] text-[var(--ota-text)] rounded-full pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-[var(--ota-gold)]/50 transition-colors"
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 bg-[var(--ota-bg)]">
          {isLoading ? (
            <div className="flex justify-center items-center h-full text-[var(--ota-gold)] font-medium">Yükleniyor...</div>
          ) : filteredDocs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-10 opacity-70">
              <div className="mb-4 opacity-50 text-[var(--ota-gold)] drop-shadow-[0_0_15px_rgba(215,165,72,0.3)]"><Star className="w-16 h-16 inline-block" /></div>
              <h3 className="text-[var(--ota-text)] text-lg font-medium mb-2">Favori Belgeniz Yok</h3>
              <p className="text-[var(--ota-text-muted)] text-sm max-w-sm text-center">
                Ana panodan veya listelerden yıldız ikonuna tıklayarak favorilerinize ekleyebilirsiniz.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredDocs.map((doc) => (
                <div 
                  key={doc.id}
                  className="glass-panel p-6 rounded-xl cursor-pointer border border-transparent hover:border-[var(--ota-gold)]/50 transition-all hover:bg-[var(--ota-bg-2)]/80 hover:shadow-[0_0_20px_rgba(215,165,72,0.15)] flex flex-col gap-3 group"
                  onClick={() => handleOpenDoc(doc)}
                >
                  <div className="flex items-start justify-between">
                    <span className="text-3xl group-hover:scale-110 transition-transform origin-bottom-left filter drop-shadow-md"><FileText className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={(e) => toggleFavorite(doc.id, e)}
                        title="Favorilerden Çıkar"
                        className="p-2 rounded-lg transition-colors text-[var(--ota-gold)] bg-[var(--ota-gold-dim)] hover:bg-[var(--ota-gold)] hover:text-[#0A202A]"
                      >
                        <Star className="w-5 h-5 fill-current" />
                      </button>
                    </div>
                  </div>
                  <h4 className="font-semibold text-lg text-[var(--ota-text)] truncate mt-2 group-hover:text-[var(--ota-gold)] transition-colors">
                    {doc.title}
                  </h4>
                  <p className="text-sm text-[var(--ota-text-muted)] truncate mb-2">
                    {doc.original_filename}
                  </p>
                  <div className="mt-auto pt-3 border-t border-[var(--ota-border)] flex justify-between items-center text-xs">
                    <span className="text-[var(--ota-text-2)]">{new Date(doc.created_at).toLocaleDateString("tr-TR")}</span>
                    <span className="inline-block px-2 py-1 bg-[var(--ota-success)]/10 text-[var(--ota-success)] font-semibold rounded-md border border-[var(--ota-success)]/20">
                      Aktif
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
