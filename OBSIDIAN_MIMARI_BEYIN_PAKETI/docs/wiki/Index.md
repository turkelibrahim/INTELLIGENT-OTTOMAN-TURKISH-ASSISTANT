---
type: index
status: active
last_verified:
tags: [index, knowledge-graph]
---

# Index

**Özet:** Bu sayfa projenin Obsidian Bilgi Grafiği için ana navigasyon ve içerik haritasıdır. Her önemli düğüm buradan ulaşılabilir olmalıdır.

**Kütüphaneler:** Obsidian, Markdown

**Bağlantılar:** [[Current_State]], [[Task_Queue]], [[Architecture_Map]], [[Latest_Handoff]]

## Sistem Hafızası
- [[Current_State]] — Projenin doğrulanmış güncel durumu
- [[Task_Queue]] — Bağımlılık sıralı görev kuyruğu
- [[Execution_Lock]] — Aktif ajan ve dosya kilitleri
- [[Decisions]] — Mimari karar dizini
- [[Architecture_Map]] — Üst seviye bileşen haritası
- [[Source_Map]] — İddia-kaynak eşleştirmesi
- [[Ingest_Log]] — Ingest geçmişi
- [[Change_Log]] — Değişiklik geçmişi
- [[Risks]] — Aktif riskler
- [[Open_Questions]] — Cevaplanmamış sorular
- [[Lint_Report]] — Wiki sağlık raporu
- [[Latest_Handoff]] — Son ajan devir notu

## Mimari
- [[System_Context]]
- [[Processing_Job_State_Machine]]
- [[Deployment_Architecture]]
- [[Security_Model]]

## Modüller
- [[Document_Ingestion]]
- [[Image_Preprocessing]]
- [[Layout_Analysis]]
- [[OCR_Service]]
- [[Transliteration_Service]]
- [[Modernization_Service]]
- [[NER_Service]]
- [[Glossary_Service]]
- [[RAG_Chat_Service]]
- [[Evaluation_Service]]
- [[Audit_Log]]
- [[Export_Service]]

## UI
- [[Streamlit_UI]]
- [[Document_Workspace]]
- [[OCR_Review_UI]]
- [[Chat_UI]]

## Veri
- [[Database_Model]]
- [[Model_Registry]]
- [[Document_Data_Model]]
- [[Citation_Data_Model]]

## Test
- [[Test_Strategy]]
- [[Acceptance_Criteria_Map]]

## Durum Anahtarı
- `verified`: Kod veya test ile doğrulandı
- `partial`: Bir kısmı doğrulandı
- `documented`: Belgede var, kodda doğrulanmadı
- `planned`: Planlandı, uygulanmadı
- `stale`: Yeniden doğrulama gerekiyor
- `deprecated`: Artık kullanılmıyor
