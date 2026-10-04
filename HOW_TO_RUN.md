# Intelligent Ottoman Turkish Assistant Nasıl Çalıştırılır

Normal kullanım:

**START_APP.bat dosyasına çift tıklayın.**

Bu dosya backend, OCR worker ve frontend servislerini güvenli sırayla başlatır. Sistem hazır olunca tarayıcıda:

`http://127.0.0.1:3000/login`

adresini açar.

## İlk Kurulum

Normalde her açılışta kurulum çalıştırmanız gerekmez.

Yeni bir makinede eksik bağımlılık varsa:

1. `FIRST_RUN_SETUP.bat` dosyasını çalıştırın.
2. Hata yoksa `START_APP.bat` ile uygulamayı açın.

Bu script Kraken modelini silmez, yeniden indirmez ve OCR eğitimi başlatmaz.

## Uygulamayı Açma

`START_APP.bat`

Başlatılan servisler:

- FastAPI backend: `http://127.0.0.1:8000`
- Next.js frontend: `http://127.0.0.1:3000`
- OCR worker: arka planda processing job'ları işler

## Uygulamayı Kapatma

`STOP_APP.bat`

Sadece launcher tarafından başlatılan PID dosyalarındaki processleri kapatır. Başka Python, Node veya WSL processlerini topluca öldürmez.

## Yeniden Başlatma

`RESTART_APP.bat`

Önce kendi processlerini kapatır, sonra uygulamayı yeniden başlatır.

## Durum Kontrolü

`STATUS_APP.bat`

Backend, frontend, database, WSL Ubuntu, Kraken, CUDA, model SHA ve port durumlarını gösterir.

## Sağlık Kontrolü

`HEALTH_CHECK.bat`

Read-only diagnostic çalıştırır. Servisleri değiştirmez.

## Debug Başlatma

- Sadece backend: `START_BACKEND.bat`
- Sadece frontend: `START_FRONTEND.bat`

## Loglar

Loglar şu klasördedir:

`runtime\logs\`

Önemli loglar:

- `launcher.log`
- `backend_*.log`
- `backend_error_*.log`
- `worker_*.log`
- `worker_error_*.log`
- `frontend_*.log`
- `frontend_error_*.log`

## Sorun Çıkarsa

1. `STATUS_APP.bat` çalıştırın.
2. `HEALTH_CHECK.bat` çalıştırın.
3. Hata mesajında belirtilen log dosyasına bakın.
4. Port 3000 veya 8000 başka bir uygulama tarafından kullanılıyorsa launcher o processi öldürmez; önce o uygulamayı kendiniz kapatmanız gerekir.
