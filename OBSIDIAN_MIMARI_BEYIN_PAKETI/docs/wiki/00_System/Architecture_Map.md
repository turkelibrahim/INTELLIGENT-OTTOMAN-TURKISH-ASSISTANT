---
type: architecture-map
status: documented
last_verified:
tags: [architecture, map]
---

# Architecture Map

**Özet:** UI, servisler, veri katmanı ve yapay zekâ işleme hattı arasındaki üst seviye bağlantıları gösterir.

**Kütüphaneler:** Streamlit, FastAPI, OpenCV, Kraken, SQLAlchemy

**Bağlantılar:** [[Streamlit_UI]], [[FastAPI_API]], [[Database_Model]], [[Processing_Job_State_Machine]]

## Katmanlar

## Ana Veri Akışı
[[Document_Ingestion]] → [[Image_Preprocessing]] → [[Layout_Analysis]] → [[OCR_Service]] → [[Transliteration_Service]] → [[Modernization_Service]] → [[NER_Service]] → [[RAG_Chat_Service]]

## Çapraz Kesitler
- [[Audit_Log]]
- [[Security_Model]]
- [[Model_Registry]]
- [[Evaluation_Service]]
- [[Export_Service]]

## Mermaid
```mermaid
flowchart LR
    UI[Streamlit UI] --> DOC[Document Ingestion]
    DOC --> PRE[Image Preprocessing]
    PRE --> LAY[Layout Analysis]
    LAY --> OCR[OCR Service]
    OCR --> TRN[Transliteration]
    TRN --> MOD[Modernization]
    MOD --> NER[NER]
    MOD --> RAG[RAG Chat]
    NER --> RAG
    RAG --> UI
    OCR --> EVAL[Evaluation]
    NER --> EVAL
    DOC --> DB[(Database)]
    OCR --> DB
    TRN --> DB
    MOD --> DB
    NER --> DB
    RAG --> DB
```

## Doğrulama Notu
Bu harita başlangıç hipotezidir. İlk INGEST sırasında gerçek codebase ile doğrulanmalı ve statüler güncellenmelidir.
