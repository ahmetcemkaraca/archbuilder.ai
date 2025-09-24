# AI Çekirdek Arayüzleri ve Modelleri Dokumentasyonu

## Genel Bakış
Bu belge, ArchBuilder.AI bulut sunucusu uygulamasının yapay zeka entegrasyonunun temelini oluşturan Pydantic modellerini ve soyut servis arayüzlerini açıklamaktadır. Bu yapılar, AI modelleriyle iletişim, çıktı doğrulama ve mimari düzen oluşturma gibi kritik süreçlerde tutarlılık ve tip güvenliği sağlar. Amaç, AI bileşenleri arasında net bir sözleşme oluşturmak ve geliştirme sürecini kolaylaştırmaktır.

## Kurulum ve Bağımlılıklar
AI çekirdek arayüzleri ve modelleri, `src/cloud-server/app/core/ai/interfaces.py` ve `src/cloud-server/app/models/ai/models.py` dosyalarında tanımlanmıştır. Temel bağımlılıklar şunlardır:
- Python 3.13+
- `Pydantic` (veri modelleri ve doğrulama için)
- `abc` (soyut temel sınıflar için)

Bu modülleri kullanmak için `requirements.txt` dosyanızda `pydantic` paketinin bulunduğundan emin olun.

## Kullanım
Bu modeller ve arayüzler, AI hizmetleri katmanında (örn. `src/cloud-server/app/services/ai_service.py`) AI modelleriyle etkileşimde bulunurken, veri girişlerini ve çıkışlarını yapılandırmak için kullanılır.

**Örnek Model Kullanımı:**
```python
from app.models.ai.models import RoomProgram, BuildingType, Point3D, WallDefinition
from app.core.ai.interfaces import IAIService

# RoomProgram modeli oluşturma
room_program = RoomProgram(
    correlation_id="COR_12345",
    rooms=[
        {"name": "LivingRoom", "area_m2": 30.0, "required_features": ["window"]},
        {"name": "Bedroom", "area_m2": 15.0}
    ],
    total_area_m2=45.0,
    building_type=BuildingType.RESIDENTIAL
)

# IAIService arayüzünü uygulayan bir servis örneği (örnek amaçlı)
class AIServiceImplementation(IAIService):
    async def process_ai_command(self, request: AICommandRequest) -> AICommandResponse:
        # ... uygulama
        pass
    
    async def generate_architectural_layout(self, room_program: RoomProgram, correlation_id: str) -> LayoutResult:
        # ... AI modelini çağırma ve LayoutResult döndürme
        wall1 = WallDefinition(
            start_point=Point3D(x=0, y=0),
            end_point=Point3D(x=5000, y=0),
            height_mm=2700,
            wall_type_name="Generic - 200mm",
            level_name="Level 1"
        )
        return LayoutResult(correlation_id=correlation_id, walls=[wall1])

# Servis kullanımı
ai_service = AIServiceImplementation()
# layout = await ai_service.generate_architectural_layout(room_program, "COR_12345")
# print(layout.json(indent=2))
```

## API Referansı
### `app.models.ai.models` Modülü
Bu modül, AI entegrasyonu için kullanılan tüm Pydantic tabanlı veri modellerini içerir:

**Enum'lar:**
- `BuildingType`: (`residential`, `office`, `retail`, `industrial`)
- `ValidationStatus`: (`valid`, `invalid_but_correctable`, `requires_manual_review`, `rejected`)
- `ValidationSeverity`: (`info`, `warning`, `error`, `critical`)
- `WallJoinBehavior`: (`butt`, `miter`, `square_off`)
- `DoorSwingDirection`: (`left_in`, `left_out`, `right_in`, `right_out`)
- `AIModel`: (`gpt-4`, `claude-3-5-sonnet`, `gemini-pro`, `gemini-2.5-flash-lite`)

**Çekirdek Modeller:**
- `Point3D`: 3D bir nokta (x, y, z koordinatları).
- `ElementParameter`: Revit elemanlarına eklenebilecek genel parametreler.
- `WallDefinition`: Bir duvarın geometrik ve yapısal özelliklerini tanımlar.
- `DoorDefinition`: Bir kapının geometrik ve yerleşim özelliklerini tanımlar.
- `WindowDefinition`: Bir pencerenin geometrik ve yerleşim özelliklerini tanımlar.
- `RoomDefinition`: Bir odanın özelliklerini (alan, merkez, sınır duvarları) tanımlar.
- `FloorDefinition`: Bir katın veya döşemenin geometrik özelliklerini tanımlar.
- `RoofDefinition`: Bir çatının geometrik özelliklerini tanımlar.
- `AIMetadata`: AI modelinden gelen meta verileri (güven skoru, işlem süresi, token kullanımı).
- `ValidationError`: Doğrulama sırasında bulunan tek bir hatayı tanımlar.
- `ValidationWarning`: Doğrulama sırasında bulunan tek bir uyarıyı tanımlar.
- `ValidationResult`: Kapsamlı doğrulama sonucunu, hata ve uyarıları içerir.
- `LayoutResult`: AI tarafından oluşturulan tam mimari düzeni (duvarlar, kapılar, pencereler vb.) içerir.
- `RoomRequirement`: Bir odanın gereksinimlerini (adı, alanı, tercih edilen genişlik/yükseklik).
- `SpatialConstraints`: Mekansal kısıtlamaları (min oda alanı, max bina yüksekliği).
- `StylePreferences`: Mimari stil ve malzeme tercihleri.
- `RoomProgram`: Bir mimari düzen oluşturmak için giriş olarak kullanılan oda programı.

**AI Komut Modelleri:**
- `Attachment`: AI komutuna eklenen dosya verileri.
- `CommandContext`: AI komutunun yürütüldüğü bağlam (mevcut Revit modeli, seçili elemanlar).
- `AIOptions`: AI model seçenekleri (model adı, sıcaklık, max token).
- `AICommandRequest`: Bulut sunucusuna gönderilen genel AI komut isteği.
- `AICommandResponse`: Bulut sunucusundan dönen genel AI komut yanıtı.

### `app.core.ai.interfaces` Modülü
Bu modül, AI servis bileşenleri için soyut temel sınıfları (arayüzler) içerir:

- `IAIModelClient(ABC)`:
    - `generate_layout(self, prompt: str, correlation_id: str, options: Dict[str, Any] = None) -> Dict[str, Any]`
    - `analyze_project(self, project_data: Dict[str, Any], correlation_id: str, options: Dict[str, Any] = None) -> Dict[str, Any]`
- `IAIService(ABC)`:
    - `process_ai_command(self, request: AICommandRequest) -> AICommandResponse`
    - `generate_architectural_layout(self, room_program: RoomProgram, correlation_id: str) -> LayoutResult`
- `IPromptEngine(ABC)`:
    - `create_layout_prompt(self, room_program: RoomProgram, correlation_id: str) -> str`
    - `create_validation_prompt(self, layout_data: Dict[str, Any], correlation_id: str) -> str`
    - `create_project_analysis_prompt(self, project_data: Dict[str, Any], correlation_id: str) -> str`
- `IValidationService(ABC)`:
    - `validate_layout(self, ai_output: Dict[str, Any], correlation_id: str) -> ValidationResult`
    - `validate_building_codes(self, layout_data: Dict[str, Any], region: str, correlation_id: str) -> List[ValidationError]`

## Hata Yönetimi
Modeller, Pydantic'in yerleşik doğrulama yeteneklerini kullanır. Model oluşturulurken veya veriler atılırken doğrulama hataları otomatik olarak `pydantic.ValidationError` olarak yükseltilir. Servis arayüzlerini uygulayan somut sınıflar, kendi iş mantıkları içindeki hataları uygun şekilde yakalamalı ve ele almalıdır. `ValidationError` ve `ValidationWarning` modelleri, doğrulama sonuçlarını yapılandırılmış bir şekilde iletmek için kullanılır.

## Güvenlik
Bu modeller ve arayüzler doğrudan güvenlik mekanizmaları sağlamaz. Ancak, AI entegrasyonunun genel güvenlik stratejisi (veri doğrulama, insan incelemesi, yetkilendirme) bu modellerin doğru ve güvenli bir şekilde kullanılmasını gerektirir. Hassas verilerin (`Attachment` içindeki `data` alanı gibi) güvenli bir şekilde işlenmesi ve saklanması, bu modelleri kullanan servislerin sorumluluğundadır.

## Konfigürasyon
Modellerin ve arayüzlerin doğrudan bir konfigürasyonu yoktur. Ancak, `AIOptions` gibi modeller, AI model davranışını (sıcaklık, max token) çalışma zamanında yapılandırmak için kullanılabilir.

## Loglama
Bu modeller ve arayüzler loglama işlevselliği sağlamaz, ancak bunları kullanan servisler (`IAIService` uygulayan sınıflar) işlemleri `structlog` gibi bir kütüphane aracılığıyla loglamalıdır. `Correlation ID`'leri, AI komutlarının uçtan uca izlenebilirliği için kritik öneme sahiptir.

