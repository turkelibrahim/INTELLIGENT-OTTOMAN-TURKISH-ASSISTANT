"use client";

import { useState, useMemo } from "react";
import { CircleHelp, Database, Eye, Rocket, ScanSearch, ScrollText } from 'lucide-react';


const Search = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
);

const ChevronDown = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><polyline points="6 9 12 15 18 9"></polyline></svg>
);

type HelpItem = {
  title: string;
  content: React.ReactNode;
};

type HelpCategory = {
  id: string;
  title: string;
  icon: React.ReactNode;
  items: HelpItem[];
};

const HELP_DATA: HelpCategory[] = [
  {
    id: "baslangic",
    title: "BAŞLANGIÇ",
    icon: <Rocket className="w-5 h-5 inline-block mr-1 align-text-bottom" />,
    items: [
      {
        title: "Belge Yükleme",
        content: (
          <div className="space-y-3">
            <p><strong>Intelligent Ottoman Turkish Assistant</strong> sistemine belge yüklemek için Ana Analiz (Dashboard) ekranındaki yükleme alanını kullanabilirsiniz.</p>
            <ul className="list-disc ml-5 space-y-1 text-[var(--ota-text-muted)]">
              <li><strong>Desteklenen Formatlar:</strong> PNG, JPG, TIFF, PDF</li>
              <li><strong>Maksimum Dosya Boyutu:</strong> 50 MB</li>
              <li><strong>Önerilen Çözünürlük:</strong> Karakter ayrımı için en az 300 DPI (Netlik, OCR başarısını doğrudan etkiler).</li>
            </ul>
          </div>
        )
      },
      {
        title: "İlk Analiz",
        content: (
          <p>Belge yüklendikten sonra sistem tarafından analiz süreci otomatik başlatılır. Analiz sırasında belge; görüntü iyileştirme, OCR (Optik Karakter Tanıma), Latin harflerine transkripsiyon ve Modern Türkçeye aktarım adımlarından geçer. İlerlemeyi ekrandaki ilerleme çubuğundan takip edebilirsiniz.</p>
        )
      }
    ]
  },
  {
    id: "belge-analizi",
    title: "BELGE ANALİZİ",
    icon: <Eye className="w-5 h-5 inline-block mr-1 align-text-bottom" />,
    items: [
      {
        title: "OCR Nedir?",
        content: (
          <p>OCR (Optik Karakter Tanıma), görüntü formatındaki yazıları makine tarafından okunabilir metin formatına dönüştürme işlemidir. Sistemimiz, Osmanlıca el yazısı (rika, divani vb.) ve matbu metinleri tanımak üzere özel olarak eğitilmiş, NVIDIA GPU destekli yerel modeller kullanır.</p>
        )
      },
      {
        title: "Osmanlıca Metin",
        content: (
          <div className="space-y-3">
            <p>OCR aşamasının doğrudan çıktısıdır. Arap alfabesiyle (Osmanlıca) yazılmış metnin orijinal halini gösterir.</p>
            <ul className="list-disc ml-5 space-y-1 text-[var(--ota-text-muted)]">
              <li>Sağdan sola (RTL) okuma düzeni korunur.</li>
              <li>Her satır ve blok için bounding-box (çerçeve) bilgisi tutularak orijinal belge üzerindeki konumuyla eşleştirilir.</li>
            </ul>
          </div>
        )
      },
      {
        title: "Latin Transkripsiyon",
        content: (
          <p>Osmanlıca karakterlerin Latin alfabesi karşılıklarıyla yazılmasıdır. Bu süreçte İSAM transkripsiyon kurallarına olabildiğince sadık kalınır. Harflerin orijinal ses değerleri ve yazım özellikleri Latin karakterleriyle aslına uygun şekilde (örn. ayn, hemze, kef varyasyonları) ifade edilir.</p>
        )
      },
      {
        title: "Modern Türkçe",
        content: (
          <p>Latin alfabesine aktarılmış metnin, RAG entegrasyonu ve dil modelleri kullanılarak günümüz Türkçesine anlam bütünlüğü korunarak çevrildiği son aşamadır. Eski kelimeler, güncel kelime dağarcığına göre (bağlam dikkate alınarak) anlaşılır şekilde dönüştürülür.</p>
        )
      }
    ]
  },
  {
    id: "tarihsel-analiz",
    title: "TARİHSEL ANALİZ",
    icon: <ScrollText className="w-5 h-5 inline-block mr-1 align-text-bottom" />,
    items: [
      {
        title: "Tarihsel Bağlam",
        content: (
          <p>Sistem, belgenin içeriğini analiz ederek ait olduğu dönemi, belgenin türünü (ferman, berat, arzuhal vb.) ve ilgili olabileceği padişah veya tarihi dönemi tahmin eder. Bu bağlam, metnin daha iyi anlaşılmasına katkı sağlar.</p>
        )
      },
      {
        title: "Kişiler ve Yerler",
        content: (
          <p>Metin içerisindeki varlık isimleri (NER - Named Entity Recognition) tespit edilir. Kişi (Şahıs), Yer (Mekân), Kurum (Organizasyon) ve Tarih gibi unsurlar renklerle işaretlenerek belge hakkındaki spesifik bilgilerin kolayca ayırt edilmesi sağlanır.</p>
        )
      },
      {
        title: "Kaynaklar",
        content: (
          <p>Yerel RAG (Retrieval-Augmented Generation) altyapısı sayesinde, analiz edilen belge yerel veritabanınızdaki (Qdrant) diğer belgelerle karşılaştırılır. Aynı kişi, yer veya olayın geçtiği önceki çalışmalarınız bulunarak çapraz referanslar oluşturulur.</p>
        )
      },
      {
        title: "Güven Skoru",
        content: (
          <div className="space-y-3">
            <p>Modeller, analiz sırasında elde edilen her sonuç için bir Güven (Confidence) skoru üretir. Bu skorlar renklerle ifade edilir:</p>
            <ul className="list-disc ml-5 space-y-1 text-[var(--ota-text-muted)]">
              <li><strong className="text-[var(--ota-success)]">Yüksek (%80-100):</strong> Sistemin sonucuna yüksek oranda güvendiği durumlar.</li>
              <li><strong className="text-[var(--ota-gold)]">Orta (%50-79):</strong> Kullanıcı tarafından doğrulanması önerilen sonuçlar.</li>
              <li><strong className="text-[var(--ota-ruby)]">Düşük (%0-49):</strong> Kesinlikle insan onayına ihtiyaç duyan, hata payı yüksek çıkarımlar.</li>
            </ul>
          </div>
        )
      }
    ]
  },
  {
    id: "goruntu-isleme",
    title: "GÖRÜNTÜ İŞLEME",
    icon: <ScanSearch className="w-5 h-5 inline-block mr-1 align-text-bottom" />,
    items: [
      {
        title: "Deskew (Eğiklik Düzeltme)",
        content: (
          <p>Taranmış veya fotoğraflanmış belgelerde oluşan fiziksel eğikliklerin tespit edilip metnin yatay düzleme tam paralel hale getirilmesini sağlar. Eğik belgelerde OCR performansının düşmesini engeller.</p>
        )
      },
      {
        title: "Denoise (Gürültü Temizleme)",
        content: (
          <p>Eski belgelerdeki fiziksel yıpranmalar, mürekkep dağılmaları, kağıt sararmaları veya tarayıcı hatalarından kaynaklanan arkaplan gürültülerini filtreleyerek, sadece asıl metnin (sinyalin) kalmasına yardımcı olur.</p>
        )
      },
      {
        title: "Threshold (Binarization)",
        content: (
          <p>Görüntüyü renkli tonlardan arındırıp tamamen siyah (metin) ve beyaz (arkaplan) olacak şekilde ikili yapıya (binary) indirger. Böylece karakterlerin arka plandan kesin sınırlarla ayrışması sağlanır.</p>
        )
      },
      {
        title: "Segmentation (Bölütleme)",
        content: (
          <p>Belgedeki ana metin bloklarını (paragraflar, başlıklar, mühürler vb.) ve bu bloklar içerisindeki tekil satırları tespit etme işlemidir. Osmanlıcadaki karmaşık satır yapısını anlamlandırmak için kullanılır.</p>
        )
      }
    ]
  },
  {
    id: "yonetim",
    title: "YÖNETİM",
    icon: <Database className="w-5 h-5 inline-block mr-1 align-text-bottom" />,
    items: [
      {
        title: "Arşiv",
        content: (
          <p>Sisteme yükleyip analiz ettiğiniz tüm belgeler kalıcı arşivinize kaydedilir. Arşiv sekmesinde geçmiş belgelerinizi listeleyebilir, arama yapabilir ve belge tiplerine veya tarihe göre filtreleme yapabilirsiniz.</p>
        )
      },
      {
        title: "Favoriler",
        content: (
          <p>Arşivinizdeki önemli veya üzerinde çalışmaya devam edeceğiniz belgeleri yıldızlayarak favorilere ekleyebilirsiniz. Bu belgelere Favoriler sekmesi üzerinden hızlı erişim sağlayabilirsiniz.</p>
        )
      },
      {
        title: "Raporlar",
        content: (
          <p>Analizi tamamlanmış bir belgeyi PDF, Word (DOCX) veya JSON formatında dışa aktarabilirsiniz. Dışa aktarma menüsü, Orijinal Belge, Osmanlıca Metin, Transkripsiyon ve Tarihsel Analiz verilerinin hangilerini rapora dâhil edeceğinizi seçmenizi sağlar.</p>
        )
      },
      {
        title: "Ayarlar",
        content: (
          <p>Sistem durumu, kullanılan yapay zeka modelleri, OCR motoru, donanım ivmelendirmesi (GPU), Vektör veritabanı (Qdrant) ve diğer uygulama tercihlerini yapılandırıp sistem sağlığını izleyebileceğiniz denetim merkezidir.</p>
        )
      }
    ]
  },
  {
    id: "sss",
    title: "SSS (Sıkça Sorulan Sorular)",
    icon: <CircleHelp className="w-5 h-5 inline-block mr-1 align-text-bottom" />,
    items: [
      {
        title: "Verilerim internete yükleniyor mu?",
        content: (
          <p>Hayır, Intelligent Ottoman Turkish Assistant tamamen yerel (local-first) bir mimariye sahiptir. Belgeleriniz, çevirileriniz ve arşiviniz tamamen kendi makinenizde (Local LLM ve Qdrant) kalır. Sistem sadece ihtiyaç duyduğunda NVIDIA gibi fallback modelleri için yapılandırılmış (maskelenmiş) API&apos;leri kullanabilir.</p>
        )
      },
      {
        title: "Model Türkçe çeviride hata yapıyor, ne yapmalıyım?",
        content: (
          <p>Ana Analiz ekranındaki metin alanlarına tıklayarak manuel düzeltme (edit) işlemini gerçekleştirebilirsiniz. Manuel olarak kaydettiğiniz düzenlemeler, doğrudan belgenin analiz sonucunu günceller ve arşive kaydedilir.</p>
        )
      },
      {
        title: "Mühürler ve görseller okunabiliyor mu?",
        content: (
          <p>Kraken/EasyOCR motorları metin satırları (lines) üzerine yoğunlaşmıştır. Mühürlerin tespiti blok seviyesinde yapılabilir, ancak çok karmaşık tuğra veya dairesel mühürlerin okunması metinden çok semantik bir işlem gerektirdiğinden OCR başarısı sınırlı olabilir. Bu tarz durumlarda Görüntü İşleme Laboratuvarı kullanılarak belgenin kontrastı maksimize edilebilir.</p>
        )
      }
    ]
  }
];

export default function HelpPage() {
  const [activeCategoryId, setActiveCategoryId] = useState<string>("baslangic");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({});

  const toggleAccordion = (categoryId: string, itemIndex: number) => {
    const key = `${categoryId}-${itemIndex}`;
    setExpandedItems(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // Filter functionality based on search query
  const filteredData = useMemo(() => {
    if (!searchQuery.trim()) return HELP_DATA;
    
    const query = searchQuery.toLowerCase();
    
    return HELP_DATA.map(category => {
      const filteredItems = category.items.filter(item => 
        item.title.toLowerCase().includes(query) || 
        (typeof item.content === 'string' && item.content.toLowerCase().includes(query)) ||
        // Simple heuristic for checking text content inside React nodes if we used plain strings mainly,
        // but since we have React elements, we will mostly search titles, unless we recursively extract text.
        // For this purpose, title search and basic category search is often enough.
        category.title.toLowerCase().includes(query)
      );
      
      if (filteredItems.length > 0 || category.title.toLowerCase().includes(query)) {
        return {
          ...category,
          items: filteredItems.length > 0 ? filteredItems : category.items
        };
      }
      return null;
    }).filter(Boolean) as HelpCategory[];
  }, [searchQuery]);

  const activeCategory = filteredData.find(c => c.id === activeCategoryId) || filteredData[0];

  return (
    <div className="w-full p-4 lg:p-8 animate-in slide-in-from-bottom-4 fade-in duration-700 flex flex-col h-full min-h-[calc(100vh-64px)]">
      
      {/* Header */}
      <header className="ota-page-header">
        <div className="absolute inset-0 opacity-[0.03] bg-[url('/auth/floral-pattern.png')] bg-repeat pointer-events-none" />
        <div className="relative z-10 max-w-2xl">
          <p className="text-[var(--ota-gold)] font-medium uppercase tracking-wider mb-2 text-xs">Dokümantasyon</p>
          <h1 className="text-3xl font-serif font-bold text-[var(--ota-text)] mb-3 flex items-center gap-3">
            Yardım Merkezi
          </h1>
          <p className="text-[var(--ota-text-muted)] text-sm leading-relaxed">
            Platformun özelliklerini, yapay zeka analiz akışını ve sistem yapılandırmasını anlamak için kategorileri inceleyebilirsiniz.
          </p>
        </div>
        
        {/* Search */}
        <div className="relative z-10 w-full lg:w-[320px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--ota-text-muted)]" />
            <input 
              type="text" 
              placeholder="Yardım konusunda ara..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[var(--ota-bg-1)] border border-[var(--ota-border)] rounded-full pl-10 pr-4 py-2.5 text-sm text-[var(--ota-text)] focus:outline-none focus:border-[var(--ota-gold)] focus:ring-1 focus:ring-[var(--ota-gold)]/50 placeholder-[var(--ota-text-muted)] transition-all"
            />
          </div>
        </div>
      </header>

      {/* Content Area */}
      <div className="flex flex-col lg:flex-row gap-6 lg:gap-8 flex-1 min-h-0">
        
        {/* Navigation Sidebar */}
        <aside className="w-full lg:w-[280px] flex-shrink-0 flex flex-col overflow-y-auto custom-scrollbar max-h-full">
          <nav className="glass-panel border border-[var(--ota-border)] rounded-2xl p-4 bg-[var(--ota-surface)] shadow-[var(--glass-shadow)] sticky top-0">
            <h3 className="text-[10px] font-bold uppercase tracking-wider text-[var(--ota-text-muted)] mb-4 px-2">Kategoriler</h3>
            
            {filteredData.length === 0 ? (
              <p className="text-sm text-[var(--ota-text-muted)] px-2">Sonuç bulunamadı.</p>
            ) : (
              <ul className="flex flex-col gap-1.5">
                {filteredData.map((category) => {
                  const isActive = activeCategoryId === category.id;
                  return (
                    <li key={category.id}>
                      <button
                        onClick={() => setActiveCategoryId(category.id)}
                        className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 flex items-center gap-3 text-sm font-medium
                          ${isActive 
                            ? "bg-gradient-to-r from-[var(--ota-gold)]/20 to-transparent border border-[var(--ota-gold)]/30 text-[var(--ota-gold)] shadow-sm" 
                            : "hover:bg-[var(--ota-bg-1)] text-[var(--ota-text-muted)] hover:text-[var(--ota-text)]"
                          }`}
                      >
                        <span className="text-lg flex-shrink-0">{category.icon}</span>
                        <span className="truncate">{category.title}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </nav>
        </aside>

        {/* Content Panel */}
        <main className="flex-1 min-w-0 flex flex-col overflow-y-auto custom-scrollbar lg:pr-2">
          {activeCategory ? (
            <div className="glass-panel border border-[var(--ota-border)] rounded-2xl p-6 lg:p-10 bg-[var(--ota-surface)] shadow-[var(--glass-shadow)] min-h-full">
              <div className="flex items-center gap-4 mb-8 pb-6 border-b border-[var(--ota-border)]">
                <div className="w-12 h-12 rounded-xl bg-[var(--ota-bg-2)] border border-[var(--ota-border)] flex items-center justify-center text-2xl shadow-sm">
                  {activeCategory.icon}
                </div>
                <div>
                  <h2 className="text-2xl font-serif font-bold text-[var(--ota-text)]">{activeCategory.title}</h2>
                  <p className="text-[var(--ota-text-muted)] text-sm mt-1">Bu kategorideki başlıkları inceleyin</p>
                </div>
              </div>
              
              <div className="flex flex-col gap-4">
                {activeCategory.items.map((item, index) => {
                  const key = `${activeCategory.id}-${index}`;
                  // Make first item expanded by default if none are set
                  const isExpanded = expandedItems[key] ?? (index === 0 && !searchQuery);
                  
                  return (
                    <div 
                      key={index} 
                      className={`border rounded-xl transition-all duration-300 overflow-hidden ${isExpanded ? 'border-[var(--ota-gold)]/40 bg-[var(--ota-bg-1)]/50 shadow-sm' : 'border-[var(--ota-border)] bg-[var(--ota-surface-dark)] hover:border-[var(--ota-border-hover)]'}`}
                    >
                      <button 
                        onClick={() => toggleAccordion(activeCategory.id, index)}
                        className="w-full flex items-center justify-between p-5 text-left focus:outline-none"
                      >
                        <h3 className={`font-medium ${isExpanded ? 'text-[var(--ota-gold)]' : 'text-[var(--ota-text)]'}`}>
                          {item.title}
                        </h3>
                        <span className={`text-[var(--ota-text-muted)] transition-transform duration-300 ${isExpanded ? 'rotate-180 text-[var(--ota-gold)]' : ''}`}>
                          <ChevronDown className="w-5 h-5" />
                        </span>
                      </button>
                      
                      <div 
                        className={`transition-all duration-300 ease-in-out px-5 overflow-hidden ${isExpanded ? 'max-h-[800px] pb-5 opacity-100' : 'max-h-0 pb-0 opacity-0'}`}
                      >
                        <div className="text-sm text-[var(--ota-text-2)] leading-relaxed prose prose-invert max-w-none prose-p:my-2 prose-ul:my-2 prose-li:my-0">
                          {item.content}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="glass-panel border border-[var(--ota-border)] rounded-2xl p-10 bg-[var(--ota-surface)] flex flex-col items-center justify-center text-center h-full min-h-[400px]">
              <Search className="w-12 h-12 text-[var(--ota-text-muted)] mb-4 opacity-50" />
              <h3 className="text-xl font-medium text-[var(--ota-text)] mb-2">Sonuç bulunamadı</h3>
              <p className="text-[var(--ota-text-muted)] max-w-md mx-auto">
                &quot;{searchQuery}&quot; aramasıyla eşleşen bir yardım başlığı bulunamadı. Lütfen farklı anahtar kelimeler deneyin.
              </p>
              <button 
                onClick={() => setSearchQuery("")}
                className="mt-6 px-6 py-2 bg-[var(--ota-bg-2)] hover:bg-[var(--ota-bg-1)] border border-[var(--ota-border)] rounded-lg text-sm transition-colors"
              >
                Aramayı Temizle
              </button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
