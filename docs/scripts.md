# Script Kullanımı

## validate-registry.ps1
- Amaç: Registry dosyalarının mevcut ve geçerli olduğundan emin olur; olası API değişiminde boş registry uyarısı verir.
- Çalıştırma:
```
pwsh -File scripts/validate-registry.ps1
```
- Çıkış kodları: 0 (OK), 2 (eksik), 3 (JSON hatası), 4 (muhtemel değişim ama endpoints boş)

## rehydrate-context.ps1
- Amaç: Registry içeriğini `current-context.md` içine özetler.
- Çalıştırma:
```
pwsh -File scripts/rehydrate-context.ps1
```
