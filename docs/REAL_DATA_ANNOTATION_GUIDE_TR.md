# OSMANLICA GERÇEK VERİ ETİKETLEME KILAVUZU (ANNOTATION GUIDE)

## 1. Uygulamanın Başlatılması
```bash
python ocr_studio_backend.py
```
Tarayıcıdan `http://localhost:8000` adresine girin.

## 2. Kullanım
- **Görsel Yükleme:** Sol menüden belgeyi seçin.
- **Text/Non-Text:** Satırın sağındaki 'Metin Değil' tikini kullanarak işaretleyin.
- **Bbox ve Baseline:** Kutu çizimi için fareyi sürükleyin. Taban çizgisi için Alt+Tık kullanın.
- **Reading Order:** RTL okuma yönü sırasına göre satır oklarını kullanın.
- **Osmanlıca Metin:** Sağdaki metin kutuları tam RTL destekler.
- **Human Verified:** Doğruladığınız satır için Onay butonuna basın. Otomatik onaylanmaz!
- **İkinci Kontrol (Double Review):** Farklı bir kullanıcı ikinci onayı verir.
- **Dataset Lock:** 300 satıra ulaşınca lisans vb. tamsa veri seti kilitlenir.
- **PAGE XML Export:** Dışa aktar butonuyla standart PAGE XML üretilir.
