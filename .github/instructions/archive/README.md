# Archived Instructions

**Tarih:** 2025-09-27  
**İşlem:** Instruction dosyalarının birleştirilmesi ve arşivlenmesi

## 📋 Arşivlenen Dosyalar

### `developer.instructions.md` ✅ Arşivlendi
- **Sebep:** İçeriği `copilot-instructions.md` dosyasına birleştirildi
- **Arşiv Dosyası:** `developer.instructions.md.archived`
- **Ana İçerik:** Developer workflow, before/after coding checklists

### `vibe-coding-checkpointing.instructions.md` ✅ Arşivlendi
- **Sebep:** İçeriği `copilot-instructions.md` dosyasına birleştirildi
- **Arşiv Dosyası:** `vibe-coding-checkpointing.instructions.md.archived`
- **Ana İçerik:** Checkpoint rules, context rehydration, rollback procedures

### `core-development.instructions.md` ❌ Dosya Bulunamadı
- **Sebep:** Dosya zaten mevcut değildi
- **Durum:** Arşivlenmeye gerek yok

## 🔧 Birleştirme Sonucu

Tüm instruction kuralları artık tek dosyada toplanmıştır:
- **Ana Dosya:** `.github/copilot-instructions.md`
- **Kapsam:** Development workflow, registry management, context handling, quality standards

## 📊 Karar Verilen Kurallar

1. **Dil Politikası:** In-code comments ve log messages **English**
2. **Branch Strategy:** **GitFlow** (develop branch'ten feature branch'ler)  
3. **Versioning Cadence:** Her **1 prompt**ta update
4. **Python Version:** **Python 3.11 veya 3.12**

## ✅ Birleştirilen İçerikler

- Issue-first workflow
- Before/after coding checklists
- Registry management rules
- Context rehydration procedures
- Quality gates ve security standards
- Documentation templates
- Error handling ve coaching mode
- Environment targets
- Rollback/rollforward procedures

## 🎯 Sonuç

Artık tek bir `copilot-instructions.md` dosyası tüm geliştirme kurallarını içeriyor. Çelişkiler çözüldü, tekrarlar kaldırıldı, tutarlılık sağlandı.