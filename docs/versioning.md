# Sürümleme ve Kadans

## SemVer
- MAJOR: Geriye uyumsuz değişiklikler, kıran API/migration.
- MINOR: Geriye uyumlu özellik ekleme, yeni endpoint/flag.
- PATCH: Hata düzeltme, küçük performans/doküman/CI iyileştirmeleri.

## Conventional Commits Eşleme
- feat → MINOR
- fix/perf → PATCH
- refactor/docs/chore/test → PATCH (breaking ise MAJOR)
- feat! / fix! → MAJOR

## Kadans
- Her 2 prompt sonunda `version.md` güncellenir.
- Tarih/saat: `Get-Date -Format 'yyyy-MM-dd HH:mm:ss'` (PowerShell).

## CHANGELOG
- `CHANGELOG.md` içinde Added/Changed/Fixed/Removed/Deprecated/Security başlıkları altında toplanır.
