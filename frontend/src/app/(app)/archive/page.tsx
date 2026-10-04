"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { documentsApi, type DocumentResponse } from "@/lib/api";
import { saveActiveDocumentContext } from "@/lib/documentContext";
import { Icons } from "@/components/Icons";

export default function ArchivePage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);

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

  return (
    <div className="w-full p-8 animate-in slide-in-from-bottom-4 fade-in duration-700">
      <div className="glass-panel min-h-[80vh] flex flex-col rounded-2xl overflow-hidden">
        <div className="p-8 border-b border-dashed border-slate-700/50 bg-slate-900/30">
          <div>
            <h2 className="text-3xl font-bold mb-3 flex items-center gap-3 text-slate-100">
              <span className="text-slate-400 bg-slate-800/50 p-2 rounded-xl">{Icons.archive}</span>
              Arşiv
            </h2>
            <p className="text-slate-400 m-0 text-lg">
              Geçmişte işlenmiş ve ana ekrandan kaldırdığınız belgeleriniz.
            </p>
          </div>
        </div>

        <div className="flex-1 p-8 bg-slate-900/10">
          {isLoading ? (
            <div className="flex justify-center items-center h-full text-slate-400 font-medium text-lg">Yükleniyor...</div>
          ) : documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-20">
              <div className="text-6xl mb-6 text-slate-500/50 drop-shadow-md">🗄️</div>
              <h3 className="text-slate-200 text-2xl font-semibold m-0 mb-3">Arşiviniz Şu An Boş</h3>
              <p className="text-slate-400 m-0 max-w-md text-center text-lg">
                Tamamlanan belgelerinizi veya klasörlerinizi arşivlediğinizde burada listeleyebileceksiniz.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {documents.map((doc) => (
                <div 
                  key={doc.id}
                  className="glass-panel p-6 rounded-xl cursor-pointer border border-transparent hover:border-slate-500/50 transition-all hover:bg-slate-800/80 hover:shadow-lg flex flex-col gap-3 group"
                  onClick={() => handleOpenDoc(doc)}
                >
                  <div className="flex items-start justify-between">
                    <span className="text-3xl group-hover:scale-110 transition-transform origin-bottom-left filter drop-shadow-md grayscale group-hover:grayscale-0">📄</span>
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={(e) => toggleArchive(doc.id, e)}
                        title="Arşivden Çıkar"
                        className="p-2 rounded-lg transition-colors text-slate-300 bg-slate-700/50 hover:bg-red-400/20 hover:text-red-400"
                      >
                        ↑ Çıkar
                      </button>
                      <span className="text-xs font-medium px-2 py-1 bg-slate-800/80 text-slate-400 rounded-md border border-slate-700/50">
                        {new Date(doc.created_at).toLocaleDateString("tr-TR")}
                      </span>
                    </div>
                  </div>
                  <h4 className="font-semibold text-lg text-slate-300 truncate mt-2 group-hover:text-slate-100 transition-colors">
                    {doc.title}
                  </h4>
                  <p className="text-sm text-slate-500 truncate">
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
