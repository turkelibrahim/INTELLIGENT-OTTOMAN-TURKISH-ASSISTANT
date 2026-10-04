# 98 — Otonom Watchdog ve Devralma

MODE: RECOVER
AUTORUN: ENABLED

1. `AGENTS.md` oku.
2. `docs/wiki/00_System/Autonomous_Run_State.md` oku.
3. `Execution_Lock.md`, `Task_Queue.md`, `Current_State.md` ve `Latest_Handoff.md` ile karşılaştır.
4. çalışma ağacındaki değişiklikleri aktif görevle eşleştir.
5. son başarılı test kanıtını kontrol et.
6. yarım işi tamamlanmış sayma.
7. güvenli ise görevi devral.
8. tamamlanmış ama doğrulanmamışsa VERIFY yap.
9. PASS ise sıradaki READY göreve otomatik geç.
10. HARD STOP yoksa kullanıcıdan komut bekleme.
11. `PROMPTS/00_AUTONOMOUS_MASTER_ORCHESTRATOR.md` kurallarını uygula.
