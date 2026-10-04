import os
from pathlib import Path

root = Path(r"c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT")
docs = root / "docs/wiki/00_System"
handoff = root / "docs/wiki/10_Handoffs/Latest_Handoff.md"
tq = docs / "Task_Queue.md"
cs = docs / "Current_State.md"

if cs.exists():
    text = cs.read_text(encoding="utf-8")
    if "BUILD_REAL_DATA_ANNOTATION_PIPELINE_AND_PILOT_NEXT_QUEUE" not in text:
        text = text.replace("## Sonraki Güvenli Adım", "## Sonraki Güvenli Adım\n- BUILD_REAL_DATA_ANNOTATION_PIPELINE_AND_PILOT_NEXT_QUEUE başarıyla tamamlandı. İnsan etiketleme bekleniyor.")
        cs.write_text(text, encoding="utf-8")

if tq.exists():
    text = tq.read_text(encoding="utf-8")
    text += "\n## TASK-BUILD_ANNOTATION_PIPELINE\n- **Durum:** DONE\n- **Amaç:** Annotation pipeline scaffold ve testleri.\n"
    tq.write_text(text, encoding="utf-8")
else:
    tq.write_text("# Task Queue\n\n## TASK-BUILD_ANNOTATION_PIPELINE\n- **Durum:** DONE\n- **Amaç:** Annotation pipeline scaffold ve testleri.\n", encoding="utf-8")

if handoff.exists():
    text = handoff.read_text(encoding="utf-8")
    if "BUILD_REAL_DATA_ANNOTATION_PIPELINE_AND_PILOT_NEXT_QUEUE" not in text:
        text = text.replace("## 2. Tamamlanan Görevler", "## 2. Tamamlanan Görevler\n- BUILD_REAL_DATA_ANNOTATION_PIPELINE_AND_PILOT_NEXT_QUEUE")
        handoff.write_text(text, encoding="utf-8")

print("Wiki updated.")
