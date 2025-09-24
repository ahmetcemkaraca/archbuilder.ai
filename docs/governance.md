# Yönetişim ve Operasyon Kuralları

Bu belge; dil politikası, kayıt defteri (registry), kalıcı bağlam (persistent context), oturum yönetimi, sürümleme kadransı, CI/kalite kapıları ve geliştirici akışını tanımlar.

## Dil Politikası
- Kod ve tanımlayıcılar (identifiers): English
- Kod içi yorumlar ve log mesajları: Türkçe
- UI metinleri: i18n ile; varsayılan EN, TR çeviri sağlanır. Bileşenlerde string hardcode edilmez.
- Kullanıcıya sohbet yanıtları: Türkçe, kısa ve uygulanabilir.

## Registry (Kayıt Defteri)
- Konum: `docs/registry/`
  - `identifiers.json`: modüller, export edilen fonksiyonlar/sınıflar, değişkenler, config anahtarları
  - `endpoints.json`: HTTP/gRPC/GraphQL sözleşmeleri (method, path, input/output şemaları, auth, version)
  - `schemas.json`: veri modelleri, DB tabloları, migration kimlikleri
- Kural: Public sözleşme/kimlik değiştiğinde aynı branch içinde registry güncellenir, test eklenir.

## Kalıcı Bağlam (Persistent Context)
- Konum: `.mds/context/`
  - `current-context.md`: aktif sözleşmelerin ve kritik değişkenlerin kısa özeti
  - `history/NNNN.md`: her oturum için eklenen kısa özet; özetleme/temizleme öncesi yazılır
- Rehydrate: Yeni oturumda önce registry + `current-context.md` okunur.

## Oturum Yönetimi
- Özetleme ve bağlam sıfırlama öncesi: `history/NNNN.md` yarat ve `current-context.md`yi güncelle.
- Ardından bir sonraki oturumda rehydrate et ve işe başla.

## Sürümleme ve Kadans
- SemVer kullanılır (MAJOR.MINOR.PATCH). Conventional Commits ile eşle.
- Yerel kadans: Her 2 prompt sonunda `version.md` güncellenir. Zaman damgası PowerShell ile yazılır: `Get-Date -Format 'yyyy-MM-dd HH:mm:ss'`.

## CI ve Kalite Kapıları
- Windows CI workflow: `scripts/validate-registry.ps1` ve `scripts/rehydrate-context.ps1` çalıştırır.
- Registry kodla uyumsuzsa merge engellenir.

## Geliştirici Akışı
- Before coding: `.mds/context/current-context.md` + `docs/registry/*.json` oku; i18n planla.
- After coding: Registry güncelle; `current-context.md`yi tazele; `history/NNNN.md`ye özet yaz; test ekle; scriptleri çalıştır.

## Replit Agent ve Copilot
- Promptlar registry/context adımlarını açıkça talep eder.
- Çakışma durumlarında `conflict-resolution-governance.prompt.md` kullan ve kararı `history/` içine yaz.

## RAGFlow Upstream Policy (Sunucu-Tabanlı)
- Client → Server → RAGFlow zinciri zorunludur. Client doğrudan RAGFlow'a bağlanmaz.
- RAGFlow API anahtarları yalnızca sunucuda tutulur (env, secret store). Koda yazılmaz.
- Çok kiracılı izolasyon: Her kullanıcı/proje için ayrı `dataset` oluşturulur; eşleşmeler DB'de saklanır.
- PII & veri hijyeni: Client verileri sunucuya gelmeden önce mümkün olduğunda maskelenir; sunucu tarafında ek maskeleme/doğrulama uygulanır.
- Asenkron ingest: Yükleme sonrası parse/index işlemleri kuyruk ile asenkron yürütülür; durum WS/HTTP ile raporlanır.
- Retrieval seçimi: LLM'e gidecek içerik sunucuda kurallar + (opsiyonel) LLM yardımıyla seçilir; token/kost limitleri uygulanır.
- Hata eşleme: RAGFlow hataları standart hata zarfına dönüştürülür (docs/api/endpoints.md formatı), correlation ID zorunludur.
- Gözlemlenebilirlik: Upstream gecikme, sucesso/oranları ve hacimler metriklenir; loglar PII sızdırmaz.