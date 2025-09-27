---
applyTo: "src/desktop-app/**/*.cs,src/revit-plugin/**/*.cs,**/*.xaml"
description: .NET Desktop & Revit Plugin — WPF MVVM patterns, Revit API transactions, and secure client calls.
---
As .NET Desktop/Plugin Developer:
- Desktop (WPF): MVVM (CommunityToolkit.Mvvm/Prism), i18n via resource files, no hardcoded UI strings.
- HTTP Client: resilient calls (Polly), `X-API-Key` and `X-Correlation-ID` başlıkları; timeout ve retry politikaları.
- WebSocket: ilerleme güncellemeleri için yeniden bağlanma ve geri-off stratejisi.
- Revit API: tüm element işlemleri Transaction içinde; hata durumunda rollback; duplicate önleme.
- Logging: Serilog ile yapılandırılmış log; korelasyon kimliği UI’den isteğe taşınır.
- Tests: ViewModel birim testleri ve yardımcı sınıflar; Revit API için soyutlanmış test arabirimleri.
- Performance: büyük koleksiyonlarda bellek ve UI thread dengesi; async/await doğru kullanımı.
- Security: secrets hiçbir zaman koda yazılmaz; kullanıcı profiline özel güvenli saklama.

Client API Patterns
- `RevitAutoPlanApiClient` benzeri istemcilerde tek sorumluluk, hatalarda anlamlı istisnalar.
- JSON (camelCase) sözleşmesine uy; 401/403/429/5xx durumlarını ayırt et ve kullanıcıya anlaşılır mesajlar göster.

Revit Transactions
- Gruplu işlemleri tek Transaction’da topla; başarısızlıkta `Transaction.RollBack()` uygula.
- Element aramada FilteredElementCollector kullan; performans için kategorileri daralt.
