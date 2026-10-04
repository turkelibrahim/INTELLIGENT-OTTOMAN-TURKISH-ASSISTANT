# Windows Quickstart

## 1) ZIP'i çıkartın
Dosya Gezgini > **Extract all / Tümünü ayıkla**.

## 2) PowerShell açın
Kök klasörde adres çubuğuna `powershell` yazıp Enter'a basabilirsiniz.

## 3) CORE veri setini hazırla
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\08_scripts\RUN_CORE.ps1
```

Script `.venv` oluşturur, gerekli Python paketlerini kurar, açık veri setlerini indirir, line image/GT çiftlerini çıkarır, split'leri oluşturur ve QA raporu üretir.

## 4) FULL sayfa/layout kaynağı da gerekirse
```powershell
.\08_scripts\RUN_FULL.ps1
```

## 5) Tekrar doğrulama
```powershell
.\.venv\Scripts\python.exe .\08_scripts\09_validate_pack.py
```

> Eğitim kodunuz, yalnız `07_splits/*.jsonl` içindeki `eligible_for_ocr_train=true` kayıtlarını kullanmalıdır.
