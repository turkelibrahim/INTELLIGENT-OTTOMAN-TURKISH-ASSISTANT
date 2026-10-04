"use client";

import { useState, useMemo } from "react";
import { Icons } from "@/components/Icons";

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
    <div className="w-full p-8 animate-in slide-in-from-bottom-4 fade-in duration-700">
      <div className="glass-panel min-h-[85vh] flex flex-col rounded-2xl overflow-hidden relative">
        {/* Dekoratif Arkaplan Süsü */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-amber-500/5 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/3 pointer-events-none" />
        
        {/* Header */}
        <div className="p-10 border-b border-dashed border-slate-700/50 bg-slate-900/40 relative z-10">
          <div className="flex flex-col md:flex-row gap-6 items-start md:items-center justify-between">
            <div>
              <h2 className="text-4xl font-bold mb-4 flex items-center gap-4 text-slate-100">
                <span className="text-amber-500 bg-amber-500/10 p-3 rounded-2xl shadow-[0_0_20px_rgba(215,165,72,0.2)]">📖</span>
                Osmanlıca Sözlük
              </h2>
              <p className="text-slate-400 m-0 text-lg max-w-2xl">
                Kelimenin Latin harfli okunuşunu, günümüz Türkçesi anlamını veya Arap harfli orijinal yazılışını arayarak geçmişin kelime hazinesini keşfedin.
              </p>
            </div>
            
            {/* Canlı Sayaç */}
            <div className="flex flex-col items-end">
              <span className="text-4xl font-serif text-amber-500/80 mb-1">{filteredWords.length}</span>
              <span className="text-sm text-slate-500 uppercase tracking-wider font-semibold">Kelime Bulundu</span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-10 bg-slate-900/10 relative z-10">
          
          {/* Arama ve Filtreleme Çubuğu */}
          <div className="flex flex-col xl:flex-row gap-6 mb-12">
            <div className="relative flex-1 group">
              <div className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-amber-500 transition-colors">
                {Icons.search}
              </div>
              <input
                type="text"
                placeholder="Kelime ara... (Örn: Aşk, Zaman, كتاب)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-16 pl-14 pr-6 bg-slate-950/50 border border-slate-700/50 rounded-2xl text-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50 transition-all shadow-inner"
              />
              {searchQuery && (
                <button 
                  onClick={() => setSearchQuery("")}
                  className="absolute right-5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 p-1"
                >
                  ✕
                </button>
              )}
            </div>
            
            <div className="flex gap-2 p-2 bg-slate-950/50 rounded-2xl border border-slate-700/50 self-start overflow-x-auto">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setActiveFilter(cat)}
                  className={`px-6 py-3 rounded-xl whitespace-nowrap text-sm font-medium transition-all duration-300 ${
                    activeFilter === cat 
                      ? 'bg-amber-500/20 text-amber-400 shadow-[0_0_15px_rgba(215,165,72,0.15)]' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
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
                  className="relative glass-panel rounded-2xl border border-slate-700/50 hover:border-amber-500/50 transition-all duration-500 hover:-translate-y-1 hover:shadow-[0_10px_30px_rgba(215,165,72,0.1)] group overflow-hidden flex flex-col"
                >
                  {/* Filigran (Arkaplan Osmanlıca) */}
                  <div className="absolute -right-4 -bottom-8 text-8xl font-serif text-amber-500/[0.03] group-hover:text-amber-500/[0.07] transition-colors pointer-events-none select-none z-0" dir="rtl">
                    {word.ottoman}
                  </div>
                  
                  <div className="p-6 relative z-10 flex flex-col h-full">
                    <div className="flex justify-between items-start mb-6">
                      <h3 className="m-0 text-2xl font-bold text-slate-100 group-hover:text-amber-400 transition-colors">
                        {word.latin}
                      </h3>
                      <span className="text-4xl font-serif text-amber-500 filter drop-shadow-md" dir="rtl">
                        {word.ottoman}
                      </span>
                    </div>
                    
                    <div className="flex-1">
                      <p className="text-slate-300 text-lg mb-4">
                        <span className="text-amber-500/70 text-sm block mb-1 uppercase tracking-wider font-semibold">Anlamı</span>
                        {word.modern}
                      </p>
                      
                      {word.example && (
                        <p className="text-slate-400 text-sm italic mb-4 border-l-2 border-amber-500/30 pl-3">
                          &quot;{word.example}&quot;
                        </p>
                      )}
                    </div>

                    <div className="mt-4 pt-4 border-t border-dashed border-slate-700/50 flex justify-between items-center">
                      <span className={`text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-700/50 ${
                        word.origin === 'Arapça' ? 'bg-emerald-500/10 text-emerald-400' :
                        word.origin === 'Farsça' ? 'bg-blue-500/10 text-blue-400' :
                        word.origin === 'Türkçe' ? 'bg-red-500/10 text-red-400' :
                        'bg-slate-800/80 text-slate-300'
                      }`}>
                        {word.origin}
                      </span>
                      
                      <button className="text-amber-500/0 group-hover:text-amber-500/100 transition-all text-sm font-medium flex items-center gap-1">
                        Detay <span aria-hidden="true">→</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-32">
              <div className="text-7xl mb-6 text-amber-500/40 drop-shadow-[0_0_20px_rgba(215,165,72,0.2)]">🔍</div>
              <h3 className="text-slate-200 text-2xl font-bold m-0 mb-3">Sonuç Bulunamadı</h3>
              <p className="text-slate-400 text-lg">
                &quot;<strong className="text-amber-500">{searchQuery}</strong>&quot; araması ve &quot;<strong className="text-amber-500">{activeFilter}</strong>&quot; filtresiyle eşleşen kelime yok.
              </p>
              <button 
                onClick={() => { setSearchQuery(""); setActiveFilter("Tümü"); }}
                className="mt-6 px-6 py-3 bg-slate-800 text-slate-200 hover:bg-slate-700 rounded-xl transition-colors font-medium"
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
