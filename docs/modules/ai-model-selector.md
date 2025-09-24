# AI Model Selector

Bu belge, `app/core/ai/model_selector.py` içindeki model seçiminin kurallarını özetler.

- Sağlayıcı adları: OpenAI, Azure OpenAI (varsa), Vertex AI, Anthropic, Local.
- Örnek kurallar:
  - validation → Vertex AI `text-bison-001`
  - layout_generation → OpenAI `gpt-4o` (latency → `gpt-4o-mini`)
  - fallback → Anthropic `claude-3-haiku-20240307`

Genişletme: Kurallar `docs/conf/llm-selector.json` ile dışarıdan yönetilebilir hale getirilecek.

# AI Model Seçici Dokumentasyonu

## Genel Bakış
Bu belge, ArchBuilder.AI bulut sunucusunun `AIModelSelector` sınıfını açıklar. Bu sınıf, belirli bir görev bağlamına (dil, doküman türü, karmaşıklık, dosya formatı, analiz türü ve kullanıcı tercihi) göre en uygun yapay zeka sağlayıcısını ve modelini dinamik olarak seçer: Vertex AI (Gemini) veya OpenAI/Azure OpenAI (GPT-4.x). Amaç, maliyet etkinliği, performans ve doğruluk arasında denge kurmaktır.

## Kurulum ve Bağımlılıklar
`AIModelSelector` sınıfı `src/cloud-server/app/core/ai/model_selector.py` dosyasında tanımlanmıştır. Temel bağımlılıklar şunlardır:
- Python 3.12+
- `app.core.logging` (Uygulama loglaması için)
- `app.models.ai.models` (AI modelleri enum'ı için)

Bu sınıfın doğrudan harici bir pip bağımlılığı yoktur, ancak kullandığı `AIModel` enum'ı `pydantic` tabanlıdır ve `app.models.ai.models` modülünde tanımlıdır.

## Kullanım
`AIModelSelector`, genellikle bir AI hizmeti sınıfı (örn. `IAIService`'i uygulayan bir sınıf) içinde başlatılır ve `select_model` metodu çağrılarak görev için en uygun AI modeli belirlenir.

**Örnek Kullanım:**
```python
from app.core.ai.model_selector import AIModelSelector
from app.models.ai.models import AIModel

# Model seçiciyi başlatma
ai_model_selector = AIModelSelector()

# Mimari düzen oluşturma görevi için model seçimi
selected_model = ai_model_selector.select_model(
    language="tr",
    document_type="prompt_generation",
    complexity="simple",
    user_preference=AIModel.GEMINI_2_5_FLASH_LITE
)

print("Seçilen Model:", selected_model)
# Çıktı örneği: {'provider': 'vertex_ai', 'model': 'gemini-2.5-flash-lite', 'reason': 'Kullanıcı tercihi'}

# Mevcut proje analizi için model seçimi
selected_model_for_analysis = ai_model_selector.select_model(
    language="en",
    document_type="project_analysis",
    complexity="high",
    analysis_type="existing_project_analysis"
)

print("Analiz için Seçilen Model:", selected_model_for_analysis)
# Çıktı örneği: {'provider': 'openai', 'model': 'gpt-4.1', 'reason': 'Kapsamlı BIM analizi ve iyileştirme önerileri için en iyisi'}
```

## API Referansı
### `app.core.ai.model_selector.AIModelSelector` Sınıfı
Bu sınıfın ana metodları:

- `__init__(self)`
    - `AIModelSelector` sınıfını başlatır ve önceden tanımlanmış model konfigürasyonlarını yükler.

- `select_model(self, language: str, document_type: str, complexity: str, file_format: Optional[str] = None, analysis_type: str = "creation", user_preference: Optional[AIModel] = None) -> Dict[str, Any]`
    - **`language` (str)**: Kullanıcı veya doküman dili (örn. `"tr"`, `"en"`).
    - **`document_type` (str)**: İşlem türü (örn. `"building_code"`, `"prompt_generation"`).
    - **`complexity` (str)**: Görevin karmaşıklığı (örn. `"simple"`, `"high"`).
    - **`file_format` (Optional[str])**: İşlenen dosya formatı (örn. `"dwg"`, `"ifc"`).
    - **`analysis_type` (str)**: Analiz türü (varsayılan `"creation"`, diğer seçenek `"existing_project_analysis"`).
    - **`user_preference` (Optional[AIModel])**: Kullanıcının belirli bir modeli tercih etmesi durumunda kullanılır.
    - **Dönüş**: Seçilen modelin `provider` (sağlayıcı), `model` (model adı) ve `reason` (seçim nedeni) bilgilerini içeren bir sözlük döndürür.

## Hata Yönetimi
`AIModelSelector` sınıfı, model seçimi sırasında doğrudan hata üretmez. Geçersiz giriş parametreleri için tip ipuçları ve Pydantic modelleri aracılığıyla dolaylı doğrulama sağlanır. Model konfigürasyonunda tanımlanmayan bir `user_preference` verilirse, bu durum dahili olarak loglanır ve varsayılan seçim mantığı devreye girer.

## Güvenlik
`AIModelSelector`, doğrudan güvenlik açıkları yaratmaz. Ancak, model seçimi kararları, hassas veri işleme ve maliyet yönetimi açısından dolaylı güvenlik etkilerine sahip olabilir:
- **Maliyet Yönetimi**: Yüksek maliyetli modellerin gereksiz kullanımını önleyerek beklenmedik harcamaların önüne geçer.
- **Doğru Model Kullanımı**: Belirli görevler için daha uygun (ve potansiyel olarak daha güvenli) modellerin seçilmesini sağlar.
- **İnsan İncelemesi**: AI çıktıları için `requires_human_review` bayrağının doğru ayarlanması, kritik kararların insan tarafından onaylanmasını garanti eder.

## Konfigürasyon
Model konfigürasyonu, `AIModelSelector` sınıfının `__init__` metodunda `self.model_config` sözlüğü içinde tanımlanmıştır. Bu konfigürasyon, her AI modelinin sağlayıcısını, desteklediği dilleri, maksimum token limitlerini, uzmanlık alanlarını ve maliyet seviyelerini içerir. Gelecekte, bu konfigürasyonun harici bir kaynaktan (örn. veritabanı veya yapılandırma dosyası) dinamik olarak yüklenmesi düşünülebilir.

## Loglama
`AIModelSelector`, tüm model seçim kararlarını `app.core.logging.logger` aracılığıyla `info` seviyesinde loglar. Bu loglar, hangi modelin neden seçildiğini, kullanıcının tercihinin etkisini ve genel model dağıtım stratejisinin izlenmesini sağlar. `correlation_id` gibi bilgiler loglara eklenerek izlenebilirlik artırılır.

