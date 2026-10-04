"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { documentsApi, type DocumentResponse } from "@/lib/api";
import { saveActiveDocumentContext } from "@/lib/documentContext";
import { Icons } from "@/components/Icons";

export default function FavoritesPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);

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

  return (
    <div className="w-full p-8 animate-in slide-in-from-bottom-4 fade-in duration-700">
      <div className="glass-panel min-h-[80vh] flex flex-col rounded-2xl overflow-hidden">
        <div className="p-8 border-b border-dashed border-slate-700/50 bg-slate-900/30">
          <div>
            <h2 className="text-3xl font-bold mb-3 flex items-center gap-3 text-slate-100">
              <span className="text-amber-500 bg-amber-500/10 p-2 rounded-xl">{Icons.star}</span>
              Favoriler
            </h2>
            <p className="text-slate-400 m-0 text-lg">
              Sık kullandığınız veya önemli işaretlediğiniz belgeleriniz.
            </p>
          </div>
        </div>

        <div className="flex-1 p-8 bg-slate-900/10">
          {isLoading ? (
            <div className="flex justify-center items-center h-full text-amber-500 font-medium text-lg">Yükleniyor...</div>
          ) : documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-20">
              <div className="text-6xl mb-6 text-amber-500/50 drop-shadow-[0_0_15px_rgba(215,165,72,0.3)]">⭐</div>
              <h3 className="text-slate-200 text-2xl font-semibold m-0 mb-3">Henüz Favori Belgeniz Yok</h3>
              <p className="text-slate-400 m-0 max-w-md text-center text-lg">
                Ana panodan veya listelerden yıldız ikonuna tıklayarak favorilerinize ekleyebilirsiniz.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {documents.map((doc) => (
                <div 
                  key={doc.id}
                  className="glass-panel p-6 rounded-xl cursor-pointer border border-transparent hover:border-amber-500/50 transition-all hover:bg-slate-800/80 hover:shadow-[0_0_20px_rgba(215,165,72,0.15)] flex flex-col gap-3 group"
                  onClick={() => handleOpenDoc(doc)}
                >
                  <div className="flex items-start justify-between">
                    <span className="text-3xl group-hover:scale-110 transition-transform origin-bottom-left filter drop-shadow-md">📄</span>
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={(e) => toggleFavorite(doc.id, e)}
                        title="Favorilerden Çıkar"
                        className="p-2 rounded-lg transition-colors text-amber-400 bg-amber-400/10 hover:bg-amber-400/20"
                      >
                        ★
                      </button>
                      <span className="text-xs font-medium px-2 py-1 bg-slate-800/80 text-slate-300 rounded-md border border-slate-700/50">
                        {new Date(doc.created_at).toLocaleDateString("tr-TR")}
                      </span>
                    </div>
                  </div>
                  <h4 className="font-semibold text-lg text-slate-100 truncate mt-2 group-hover:text-amber-400 transition-colors">
                    {doc.title}
                  </h4>
                  <p className="text-sm text-slate-400 truncate">
                    {doc.original_filename}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
