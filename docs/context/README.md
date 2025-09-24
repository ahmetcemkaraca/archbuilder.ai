# Context (Bağlam) Yönetimi

Kalıcı bağlam dosyaları `.mds/context/` altında tutulur.

## Dosya Yapısı
- `current-context.md`: aktif ve kısa özet
- `history/NNNN.md`: oturum başına kronolojik özet dosyaları

## Oturum Akışı
1. Yeni oturum: Registry + `current-context.md` oku (rehydrate).
2. Çalışma sonunda: `history/NNNN.md` oluştur/ekle; `current-context.md`yi güncelle.

## Yardımcı Script
- `scripts/rehydrate-context.ps1`: Registry’den anlık özet alır ve `current-context.md`yi yazar.

## İsimlendirme
- `NNNN` sıralı artan numara; PR veya sprint bazlı da yönetilebilir.
