"use client";

import { useState, useMemo } from "react";
import { Icons } from "@/components/Icons";
import { Search, Book } from 'lucide-react';


const MOCK_DICTIONARY = [
  { id: 1, ottoman: "كتاب", latin: "Kitap", modern: "Yazılı veya basılı eser", origin: "Arapça", example: "Kütüphanede binlerce kitap bulunurdu." },
  { id: 2, ottoman: "عشق", latin: "Aşk", modern: "Şiddetli sevgi, derin muhabbet", origin: "Arapça", example: "Mevlana'nın şiirleri ilahi aşkı anlatır." },
  { id: 3, ottoman: "زمان", latin: "Zaman", modern: "Vakit, çağ, devir", origin: "Farsça", example: "Zaman su gibi akıp geçti." },
  { id: 4, ottoman: "مكتب", latin: "Mektep", modern: "Okul, eğitim yuvası", origin: "Arapça", example: "Mektebe giden çocuklar çok neşeliydi." },
  { id: 5, ottoman: "دولت", latin: "Devlet", modern: "Büyük güç, yönetim, saadet", origin: "Arapça", example: "Devlet-i Aliyye asırlar boyu hüküm sürdü." },
  { id: 6, ottoman: "چشمه", latin: "Çeşme", modern: "Su akan yer, pınar", origin: "Farsça", example: "Meydanın ortasındaki tarihi çeşme restore edildi." },
  { id: 7, ottoman: "قلم", latin: "Kalem", modern: "Yazı aracı, bürokrasi", origin: "Arapça", example: "Kalem kılıçtan daha keskindir." },
  { id: 8, ottoman: "روزگار", latin: "Rüzgâr", modern: "Yel, esinti", origin: "Farsça", example: "Sert bir rüzgâr dalları eğiyordu." },
  { id: 9, ottoman: "آفتاب", latin: "Aftâb", modern: "Güneş", origin: "Farsça", example: "Aftâb ufuktan yavaşça yükseldi." },
  { id: 10, ottoman: "حيات", latin: "Hayat", modern: "Yaşam, dirilik", origin: "Arapça", example: "Hayat kısa, ilim ise sonsuzdur." },
  { id: 11, ottoman: "كلیمه", latin: "Kelime", modern: "Sözcük", origin: "Arapça", example: "O güzel kelimeler kalpleri fethetti." },
  { id: 12, ottoman: "درد", latin: "Derd", modern: "Acı, sıkıntı, hastalık", origin: "Farsça", example: "Derdine derman arayanlar tabibe koştu." },
  { id: 13, ottoman: "آب", latin: "Âb", modern: "Su", origin: "Farsça", example: "Âb-ı hayat içmişcesine gençleşti." },
  { id: 14, ottoman: "شمس", latin: "Şems", modern: "Güneş", origin: "Arapça", example: "Şems yeryüzünü ısıttı." },
  { id: 15, ottoman: "قمر", latin: "Kamer", modern: "Ay", origin: "Arapça", example: "Kamer gece karanlığını aydınlatıyordu." },
  { id: 16, ottoman: "يول", latin: "Yol", modern: "Gidilen yön, tarîkat", origin: "Türkçe", example: "Uzun ve ince bir yoldayız." },
  { id: 17, ottoman: "سو", latin: "Su", modern: "Su, hayat kaynağı", origin: "Türkçe", example: "Dere suyu buz gibi soğuktu." },
  { id: 18, ottoman: "گوز", latin: "Göz", modern: "Görme organı, pınar", origin: "Türkçe", example: "Gözleri ufka doğru dalıp gitmişti." },
  { id: 19, ottoman: "خيال", latin: "Hayal", modern: "Düş, zihinde canlanan", origin: "Arapça", example: "Bütün hayalleri gerçeğe dönüştü." },
  { id: 20, ottoman: "بحر", latin: "Bahr", modern: "Deniz", origin: "Arapça", example: "Bahr-i Sefid (Akdeniz) gemilerle doluydu." },
];

export default function DictionaryPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<string>("Tümü");

  const categories = ["Tümü", "Arapça", "Farsça", "Türkçe"];

  const filteredWords = useMemo(() => {
    return MOCK_DICTIONARY.filter((w) => {
      const matchesSearch =
        w.latin.toLowerCase().includes(searchQuery.toLowerCase()) ||
        w.modern.toLowerCase().includes(searchQuery.toLowerCase()) ||
        w.ottoman.includes(searchQuery);
      
      const matchesFilter = activeFilter === "Tümü" || w.origin === activeFilter;

      return matchesSearch && matchesFilter;
    });
  }, [searchQuery, activeFilter]);

  return (
    <div className="w-full p-4 lg:p-8 animate-in slide-in-from-bottom-4 fade-in duration-700">
      <div className="glass-panel min-h-[85vh] flex flex-col rounded-2xl overflow-hidden relative border border-[var(--ota-border)] shadow-[var(--glass-shadow)]">
        
        {/* Header */}
        <div className="p-6 lg:p-10 border-b border-[var(--ota-border)] bg-[var(--ota-bg-2)]/80 relative z-10 flex flex-col lg:flex-row gap-6 items-start lg:items-center justify-between">
          <div className="flex flex-col gap-2">
            <h2 className="text-3xl font-serif font-bold flex items-center gap-4 text-[var(--ota-text)]">
              <span className="text-[var(--ota-gold)] bg-[var(--ota-gold-dim)] p-3 rounded-2xl border border-[var(--ota-gold)]/20 shadow-sm"><Book className="w-8 h-8 text-current" /></span>
              Osmanlıca Sözlük
            </h2>
            <p className="text-[var(--ota-text-muted)] m-0 text-sm max-w-2xl">
              Kelimenin Latin harfli okunuşunu, günümüz Türkçesi anlamını veya Arap harfli orijinal yazılışını arayarak geçmişin kelime hazinesini keşfedin.
            </p>
          </div>
          
          <div className="flex flex-col items-start lg:items-end p-4 bg-[var(--ota-bg)] border border-[var(--ota-border)] rounded-xl">
            <span className="text-3xl font-serif text-[var(--ota-gold)] mb-1 leading-none">{filteredWords.length}</span>
            <span className="text-xs text-[var(--ota-text-muted)] uppercase tracking-wider font-semibold flex items-center gap-2">
              Kelime Bulundu

            </span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 lg:p-10 bg-[var(--ota-bg)] relative z-10">
          
          {/* Arama ve Filtreleme Çubuğu */}
          <div className="flex flex-col xl:flex-row gap-6 mb-10">
            <div className="relative flex-1 group">
              <div className="absolute left-5 top-1/2 -translate-y-1/2 text-[var(--ota-text-muted)] group-focus-within:text-[var(--ota-gold)] transition-colors">
                <Search className="w-5 h-5 inline-block mr-1 align-text-bottom" />
              </div>
              <input
                type="text"
                placeholder="Kelime ara... (Örn: Aşk, Zaman, كتاب)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-14 pl-14 pr-12 bg-[var(--ota-bg-2)] border border-[var(--ota-border)] rounded-2xl text-[var(--ota-text)] placeholder-[var(--ota-text-muted)] focus:outline-none focus:border-[var(--ota-gold)] focus:ring-1 focus:ring-[var(--ota-gold)] transition-all shadow-inner"
              />
              {searchQuery && (
                <button 
                  onClick={() => setSearchQuery("")}
                  className="absolute right-5 top-1/2 -translate-y-1/2 text-[var(--ota-text-muted)] hover:text-[var(--ota-text)] p-1 transition-colors"
                >
                  ✕
                </button>
              )}
            </div>
            
            <div className="flex gap-2 p-1 bg-[var(--ota-bg-2)] rounded-2xl border border-[var(--ota-border)] self-start overflow-x-auto custom-scrollbar">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setActiveFilter(cat)}
                  className={`px-5 py-2.5 rounded-xl whitespace-nowrap text-sm font-medium transition-all duration-300 ${
                    activeFilter === cat 
                      ? 'bg-[var(--ota-gold-dim)] text-[var(--ota-gold)] shadow-sm' 
                      : 'text-[var(--ota-text-muted)] hover:text-[var(--ota-text)] hover:bg-[var(--ota-bg)]'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Grid List */}
          {filteredWords.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredWords.map((word) => (
                <div 
                  key={word.id} 
                  className="relative glass-panel rounded-2xl border border-[var(--ota-border)] hover:border-[var(--ota-gold)]/50 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg group overflow-hidden flex flex-col bg-[var(--ota-surface-dark)]/80"
                >
                  {/* Filigran (Arkaplan Osmanlıca) */}
                  <div className="absolute -right-2 -bottom-6 text-7xl font-serif text-[var(--ota-gold)]/5 group-hover:text-[var(--ota-gold)]/10 transition-colors pointer-events-none select-none z-0" dir="rtl">
                    {word.ottoman}
                  </div>
                  
                  <div className="p-6 relative z-10 flex flex-col h-full">
                    <div className="flex justify-between items-start mb-6">
                      <h3 className="m-0 text-2xl font-bold text-[var(--ota-text)] group-hover:text-[var(--ota-gold)] transition-colors">
                        {word.latin}
                      </h3>
                      <span className="text-3xl font-serif text-[var(--ota-gold)] drop-shadow-sm" dir="rtl">
                        {word.ottoman}
                      </span>
                    </div>
                    
                    <div className="flex-1">
                      <p className="text-[var(--ota-text-2)] text-base mb-4">
                        <span className="text-[var(--ota-gold)]/70 text-xs block mb-1 uppercase tracking-wider font-semibold">Anlamı</span>
                        {word.modern}
                      </p>
                      
                      {word.example && (
                        <p className="text-[var(--ota-text-muted)] text-sm italic mb-4 border-l-2 border-[var(--ota-gold)]/30 pl-3 leading-relaxed">
                          &quot;{word.example}&quot;
                        </p>
                      )}
                    </div>

                    <div className="mt-auto pt-4 border-t border-[var(--ota-border)] flex justify-between items-center">
                      <span className={`text-xs font-medium px-2 py-1 rounded border ${
                        word.origin === 'Arapça' ? 'bg-[var(--ota-success)]/10 text-[var(--ota-success)] border-[var(--ota-success)]/20' :
                        word.origin === 'Farsça' ? 'bg-[var(--ota-iznik-turquoise)]/10 text-[var(--ota-iznik-turquoise)] border-[var(--ota-iznik-turquoise)]/20' :
                        word.origin === 'Türkçe' ? 'bg-[var(--ota-ruby)]/10 text-[var(--ota-ruby)] border-[var(--ota-ruby)]/20' :
                        'bg-[var(--ota-bg-2)] text-[var(--ota-text-muted)] border-[var(--ota-border)]'
                      }`}>
                        {word.origin}
                      </span>
                      
                      <button className="text-[var(--ota-gold)]/0 group-hover:text-[var(--ota-gold)]/100 transition-all text-xs font-medium flex items-center gap-1">
                        Detay <span aria-hidden="true">→</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 opacity-70">
              <div className="text-5xl mb-4 text-[var(--ota-gold)]/40 drop-shadow-sm"><Search className="w-5 h-5 inline-block mr-1 align-text-bottom" /></div>
              <h3 className="text-[var(--ota-text)] text-xl font-bold mb-2">Sonuç Bulunamadı</h3>
              <p className="text-[var(--ota-text-muted)] text-sm max-w-sm text-center">
                &quot;{searchQuery}&quot; araması ve &quot;{activeFilter}&quot; filtresiyle eşleşen kelime yok.
              </p>
              <button 
                onClick={() => { setSearchQuery(""); setActiveFilter("Tümü"); }}
                className="mt-6 px-4 py-2 bg-[var(--ota-bg-2)] text-[var(--ota-text)] border border-[var(--ota-border)] hover:border-[var(--ota-gold)] hover:text-[var(--ota-gold)] rounded-lg transition-colors text-sm font-medium"
              >
                Tüm Filtreleri Temizle
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
