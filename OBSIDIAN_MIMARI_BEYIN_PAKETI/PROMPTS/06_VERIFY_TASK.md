# Bağımsız Görev Doğrulama Promptu

MODE: VERIFY

Doğrulanacak görev: [TASK-ID]

Görev açıklamasını, kabul kriterlerini, kod farkını, testleri ve ilgili wiki düğümlerini incele. Uygulayan ajanın iddialarını varsayım olarak kabul etme. Gerekli testleri yeniden çalıştır.

Sonucu yalnız `PASS`, `PARTIAL`, `FAIL` veya `BLOCKED` olarak ver. Eksik kabul kriterlerini ve gerçek hata kanıtlarını kaydet. Sonuç PASS değilse görev `DONE` kalamaz.
