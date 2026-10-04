# Sıradaki Görevi Uygulama Promptu

MODE: EXECUTE

Kullanıcı bu komutla kod değişikliğine izin vermektedir. `AGENTS.md` içindeki EXECUTE protokolünü eksiksiz uygula.

`[[Task_Queue]]` içinden bağımlılıkları tamamlanmış en yüksek öncelikli `READY` görevi seç. `[[Execution_Lock]]` ile sahiplen. Görev kapsamı dışında değişiklik yapma. Önce başlangıç testlerini çalıştır, sonra küçük ve geri alınabilir değişiklikler yap. Kabul kriterlerini testlerle doğrula.

Görev tamamlandığında ilgili wiki düğümlerini, `[[Current_State]]`, `[[Task_Queue]]`, `[[Change_Log]]`, `[[Source_Map]]` ve `[[Latest_Handoff]]` dosyalarını güncelle. Kanıt eksikse görevi `DONE` yapma.
