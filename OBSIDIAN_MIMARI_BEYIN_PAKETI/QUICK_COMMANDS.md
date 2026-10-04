# Hızlı Kullanım Komutları

## İlk Kez Başlat
`PROMPTS/00_MASTER_ORCHESTRATOR.md` içeriğini ajana ver.

## Yarım Kaldıysa
`PROMPTS/00_MASTER_ORCHESTRATOR.md` tekrar ver. Orkestratör `RECOVER` yapar.

## Sıradaki Aşamayı Manuel Çalıştır
En son PASS olan numaranın bir sonraki promptunu ver.

## Ajanın İşini Kontrol Ettir
İlgili aşama bittikten sonra başka bir ajana:

```text
MODE: VERIFY
AGENTS.md kurallarını uygula.
Son tamamlandığı iddia edilen görevi, kabul kriterlerini, diff'i, testleri ve wiki kanıtlarını bağımsız doğrula.
PASS değilse Task_Queue durumunu düzelt ve sonraki aşamaya geçme.
```

## Projeyi Uçuşa Hazır Sayma
Yalnız:
- Prompt 18 PASS
- Prompt 19 PASS
- Prompt 20 yayın sonrası smoke PASS
olduğunda.
