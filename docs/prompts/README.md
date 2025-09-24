# Prompt Library

Bu bölüm, sunucu tarafındaki prompt kütüphanesinin kullanımını açıklar.

Konum: `src/cloud-server/app/core/ai/prompts/`

Bileşenler:
- `loader.py` → Dosya sisteminden şablon yükler
- `renderer.py` → Jinja2 ile context render eder
- `templates/` → Sürümlemeli şablon dosyaları (`*_v1.md`)

Örnek kullanım:
```python
from app.core.ai.prompts import FileSystemPromptTemplateLoader, JinjaPromptRenderer

loader = FileSystemPromptTemplateLoader()
renderer = JinjaPromptRenderer()

tmpl = loader.load("layout_generation", version="v1")
result = renderer.render(tmpl, {
    "project_name": "Sample Tower",
    "constraints": {"site_area": 1200, "floors": 10, "max_height": 45},
    "requirements": ["residential", "retail podium"]
})
print(result.prompt_text)
```

# Prompt Kataloğu ve Kullanımı

Bu klasör, tekrar kullanılabilir görev promptlarını içerir.

## Mevcut Promptlar
- `universal-app-autobuilder.prompt.md`: Doğal dilden tam uygulama planla/uygula.
- `draft-design-blueprint.prompt.md`: Mimari taslak ve design.md güncellemesi.
- `plan-implementation-tasks.prompt.md`: Dikey dilim planı ve tasks.md.
- `ship-vertical-slice.prompt.md`: İlk dikey dilimi kodla/test et.
- `write-requirements-ears.prompt.md`: EARS formatında gereksinimler.
- `integrate-new-feature-and-sync-registry.prompt.md`: Yeni özelliği mevcut yapıyla entegre et; registry/test güncelle.
- `extend-api-contract-and-migrate.prompt.md`: API versiyonla, migration ve geriye uyum planı.
- `persist-context-and-rehydrate.prompt.md`: Oturum özetini yaz, context’i tazele.
- `refactor-with-contracts-and-tests.prompt.md`: Contract’ları koruyarak refactor.
- `conflict-resolution-governance.prompt.md`: Çakışma tespit ve çözüm yönetişimi.

## Kurallar
- Her prompt, registry/context güncellemelerini açıkça talep eder.
- Windows PowerShell komutları ile çalıştırma talimatı verilir.
