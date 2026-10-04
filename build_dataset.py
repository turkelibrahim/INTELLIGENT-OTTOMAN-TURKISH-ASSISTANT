import json
import wikipediaapi
import os
import time

# Wikipedia API'sini Türkçe için ayarla (User-Agent zorunludur)
wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='OsmanlicaAI_Dataset_Builder/1.0 (ibrahim@example.com)',
    language='tr',
    extract_format=wikipediaapi.ExtractFormat.WIKI
)

# Çekilecek devasa konular listesi (Bu listeyi binlerce kelimeye çıkarabilirsin)
osmanli_konulari = [
    "Tanzimat Fermanı", "Islahat Fermanı", "Mecelle", "Sened-i İttifak", 
    "Kanunname-i Âli Osman", "Vaka-i Hayriye", "Yeniçeri Ocağı", "Tımar sistemi",
    "İltizam sistemi", "Düyun-u Umumiye", "Osmanlı'da vakıf sistemi",
    "Sultan Süleyman kanunları", "Gülhane Hatt-ı Hümayunu", "Divan-ı Hümayun",
    "Osmanlı İmparatorluğu gerileme dönemi", "Celâlî isyanları", "Kapıkulu Ocakları",
    "Devşirme sistemi", "Osmanlı millet sistemi", "Ahilik", "Lonca teşkilatı"
    # Buraya Dilediğin Kadar Konu, Antlaşma ve Kanun Ekleyebilirsin...
]

dataset_path = os.path.join("datasets", "osmanli_egitim_verisi_mega.jsonl")

print("Web'den veriler kazınıyor ve eğitim seti oluşturuluyor...")
basarili_kayit = 0

with open(dataset_path, "w", encoding="utf-8") as f:
    for konu in osmanli_konulari:
        try:
            page = wiki_wiki.page(konu)
            
            if page.exists():
                # Sayfanın özetini alıyoruz
                summary = page.summary
                
                # Çok kısa özetleri atla
                if len(summary) < 100:
                    continue
                
                # Soru - Cevap Çifti 1: Genel Analiz
                data1 = {
                    "instruction": f"Aşağıdaki belgede/konuda geçen '{konu}' hakkında detaylı bir tarihsel analiz yap.",
                    "input": f"Konu/Belge: {konu}",
                    "output": summary
                }
                
                # Soru - Cevap Çifti 2: Neden-Sonuç Analizi
                data2 = {
                    "instruction": f"Tarihsel bağlamı göz önüne alarak '{konu}' olayının/kurumunun Osmanlı devlet yapısındaki yerini ve ortaya çıkış amacını açıkla.",
                    "input": f"Anahtar Kelime: {konu}",
                    "output": f"Osmanlı tarihi bağlamında incelendiğinde; {summary}"
                }
                
                # JSONL dosyasına satır satır yaz
                f.write(json.dumps(data1, ensure_ascii=False) + "\n")
                f.write(json.dumps(data2, ensure_ascii=False) + "\n")
                
                basarili_kayit += 2
                print(f"[BAŞARILI] eklendi: {konu}")
            else:
                print(f"[BULUNAMADI] atlandı: {konu}")
                
            # Wikipedia sunucularını yormamak (banlanmamak) için ufak bir bekleme süresi
            time.sleep(0.5)
            
        except Exception as e:
            print(f"[HATA] {konu} işlenirken hata oluştu: {e}")

print(f"\nİşlem Tamamlandı! Toplam {basarili_kayit} adet yüksek kaliteli eğitim verisi '{dataset_path}' dosyasına kaydedildi.")