# OpenAI/Azure OpenAI İstemci Dokumentasyonu

## Genel Bakış
Bu belge, ArchBuilder.AI bulut sunucusunun OpenAI/Azure OpenAI (ör. GPT-4.1) ile etkileşimini sağlayan `OpenAIAIClient` sınıfını açıklar. Bu istemci, mimari düzen oluşturma, proje analizi ve modelle çok turlu sohbet gibi AI destekli işlevleri yerine getirir. `IAIModelClient` arayüzünü uygulayarak, farklı AI modelleri arasında soyutlama sağlar.

## Kurulum ve Bağımlılıklar
`OpenAIAIClient` sınıfı `src/cloud-server/app/ai/openai/client.py` dosyasında tanımlanmıştır. Temel bağımlılıklar şunlardır:
- Python 3.12+
- `httpx` (Asenkron HTTP istekleri için)
- `app.core.ai.interfaces` (Ortak AI servis arayüzleri)
- `app.core.logging` (Uygulama loglaması)
- `app.models.ai.models` (Ortak AI modelleri)

Bu bağımlılıkları yüklemek için `src/cloud-server/requirements.txt` dosyanıza aşağıdaki paketi eklediğinizden ve `pip install -r requirements.txt` komutunu çalıştırdığınızdan emin olun:

```
httpx
```

OpenAI veya Azure OpenAI API'sini kullanmak için uygun bir API anahtarı sağlamanız gerekir. Bu anahtar genellikle çevre değişkenleri veya güvenli yapılandırma dosyaları aracılığıyla yönetilir (örn. `OPENAI_API_KEY` veya Azure için `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT`).

## Kullanım
`OpenAIAIClient`, bir AI hizmeti (örn. `ai_service.py`) tarafından enjekte edilerek veya doğrudan kullanılarak çağrılabilir. İstemcinin başlatılması sırasında bir `api_base_url` ve `api_key` (veya Azure için `endpoint` + `deployment`) belirtilmelidir.

**Örnek Kullanım:**
```python
import asyncio
import os
from app.ai.openai.client import OpenAIAIClient
from app.models.ai.models import BuildingType, RoomProgram

async def main():
    api_base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
    api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
    client = OpenAIAIClient(api_base_url=api_base_url, api_key=api_key)

    correlation_id = "TEST_LAYOUT_002"
    prompt = "Create a small, traditional 3-bedroom house layout with a separate dining area."
    
    try:
        # Düzen oluşturma
        layout_response = await client.generate_layout(prompt, correlation_id)
        print("Oluşturulan Düzen (Ham Yanıt):")
        print(layout_response)

        # Sohbet ile modelle etkileşim
        messages = [
            {"role": "user", "content": "Bana 4 odalı bir ev için modern tasarım fikirleri söyle."}
        ]
        chat_response = await client.chat_with_model(messages, correlation_id)
        print("\nSohbet Yanıtı:")
        print(chat_response)
        
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Referansı
### `app.ai.openai.client.OpenAIAIClient` Sınıfı
`IAIModelClient` arayüzünü uygulayan bu sınıfın ana metodları:

- `__init__(self, api_base_url: str, api_key: str, model_name: str = "gpt-4")`
    - `api_base_url` (str): GitHub AI modelinin API temel URL'si.
    - `api_key` (str): GitHub API anahtarı veya kişisel erişim tokenı.
    - `model_name` (str, isteğe bağlı): Kullanılacak modelin adı (varsayılan `gpt-4`).

- `async generate_layout(self, prompt: str, correlation_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`
    - `prompt` (str): AI modeline gönderilecek komut istemi.
    - `correlation_id` (str): İşlemi izlemek için benzersiz kimlik.
    - `options` (Dict, isteğe bağlı): `temperature` ve `max_tokens` gibi AI modeline özel ayarlar.
    - **Dönüş**: Ham JSON formatında AI yanıtı.
    - **İstisnalar**: `httpx.HTTPStatusError`, genel `Exception`.

- `async analyze_project(self, project_data: Dict[str, Any], correlation_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`
    - `project_data` (Dict): Analiz edilecek proje verileri (henüz uygulanmadı).
    - `correlation_id` (str): İşlemi izlemek için benzersiz kimlik.
    - `options` (Dict, isteğe bağlı): AI modeline özel ayarlar.
    - **Dönüş**: `NotImplementedError` (Henüz uygulanmadığı için).

- `async chat_with_model(self, messages: List[Dict[str, Any]], correlation_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`
    - `messages` (List[Dict[str, Any]]): Çok turlu sohbetin mesaj geçmişi (örn. `[{"role": "user", "content": "Merhaba"}]`).
    - `correlation_id` (str): İşlemi izlemek için benzersiz kimlik.
    - `options` (Dict, isteğe bağlı): `temperature` ve `max_tokens` gibi AI modeline özel ayarlar.
    - **Dönüş**: Ham JSON formatında AI yanıtı.
    - **İstisnalar**: `httpx.HTTPStatusError`, genel `Exception`.

## Hata Yönetimi
`OpenAIAIClient`, HTTP API çağrıları sırasında oluşabilecek hataları yakalar ve `httpx.HTTPStatusError` istisnasını yükseltir. Ayrıca, JSON ayrıştırma hatalarını ve diğer beklenmedik istisnaları da ele alır. Tüm hatalar `LoggerService` aracılığıyla loglanır ve çağrı yapan servislere yeniden yükseltilir.

- **`httpx.HTTPStatusError`**: HTTP istekleri sırasında oluşan sorunlar (ağ hataları, 4xx/5xx yanıtları).
- **`json.JSONDecodeError`**: AI modelinden gelen yanıtın geçerli bir JSON olmaması durumu.
- **`NotImplementedError`**: Henüz uygulanmamış metodlar çağrıldığında tetiklenir.

## Güvenlik
`GitHubAIClient` doğrudan hassas verileri işlemez, ancak AI modellerine gönderilen komut istemlerinin ve alınan yanıtların içeriği hassas olabilir. Bu nedenle:
- **Kimlik Doğrulama**: GitHub API anahtarı veya kişisel erişim tokenı güvenli bir şekilde yönetilmelidir.
- **Veri Kısıtlamaları**: AI modellerine gönderilen veriler, gizlilik ve güvenlik politikalarına uygun olmalıdır.
- **Çıktı Doğrulama**: AI çıktılarının güvenliği ve uygunluğu için kapsamlı doğrulama ve insan incelemesi gereklidir.

## Konfigürasyon
`GitHubAIClient`, `api_base_url`, `api_key` ve `model_name` gibi parametreler aracılığıyla başlatılır. Bu değerler genellikle çevre değişkenlerinden veya güvenli yapılandırma servisinden alınır. `options` parametresi aracılığıyla AI modelinin çalışma zamanı davranışları ayarlanabilir (örn. `temperature`).

## Loglama
`GitHubAIClient`, tüm önemli işlemleri (`info`, `error`, `critical` seviyelerinde) `LoggerService` aracılığıyla loglar. Her log mesajı, ilgili işlemin izlenebilirliğini sağlamak için `correlation_id` içerir. Bu, sorun giderme, performans analizi ve güvenlik denetimi için kritik öneme sahiptir.

