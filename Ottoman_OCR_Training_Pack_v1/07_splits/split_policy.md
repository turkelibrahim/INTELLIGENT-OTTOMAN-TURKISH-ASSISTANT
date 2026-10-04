# Split Policy
1. Upstream OpenITI Ottoman Lines `test` = kilitli test; train/val'e asla taşınmaz.
2. Upstream `train` içinden deterministik SHA-256 ile yaklaşık %10 validation ayrılır.
3. Sentetik örnekler `synthetic_only` olarak ayrı kalır ve gold test'e girmez.
4. Mümkün olduğunda belge/sayfa kimliğine göre leakage engellenir.
