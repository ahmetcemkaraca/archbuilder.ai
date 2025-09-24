# Vertex AI İstemci Dokumentasyonu

## Genel Bakış
Bu belge, ArchBuilder.AI bulut sunucusu uygulamasının Vertex AI (özellikle Gemini-2.5-Flash-Lite) ile etkileşim kurmasını sağlayan `VertexAIClient` sınıfını açıklamaktadır. Bu istemci, mimari düzen oluşturma, proje analizi ve modelle çok turlu sohbet gibi AI destekli işlevleri yerine getirir. `IAIModelClient` arayüzünü uygulayarak, farklı AI modelleri arasında soyutlama sağlar.

## Kurulum ve Bağımlılıklar
`VertexAIClient` sınıfı `src/cloud-server/app/ai/vertex/client.py` dosyasında tanımlanmıştır. Temel bağımlılıklar şunlardır:
- Python 3.12+
- `vertexai` (Google Cloud Vertex AI SDK)
- `google-cloud-aiplatform` (Google Cloud AI Platform SDK)
- `app.core.ai.interfaces` (Ortak AI servis arayüzleri)
- `app.core.logging` (Uygulama loglaması)
- `app.models.ai.models` (Ortak AI modelleri)

Bu bağımlılıkları yüklemek için `src/cloud-server/requirements.txt` dosyanıza aşağıdaki paketleri eklediğinizden ve `pip install -r requirements.txt` komutunu çalıştırdığınızdan emin olun:

```
google-cloud-aiplatform
vertexai
```

Vertex AI SDK'sını kullanmak için uygun Google Cloud kimlik doğrulama yöntemlerini (örn. `gcloud auth application-default login` veya hizmet hesabı anahtarı) yapılandırmanız gerekmektedir.

## Kullanım
`VertexAIClient`, bir AI hizmeti (örn. `ai_service.py`) tarafından enjekte edilerek veya doğrudan kullanılarak çağrılabilir. İstemcinin başlatılması sırasında bir Google Cloud `project_id` ve `location` belirtilmelidir.

**Örnek Kullanım:**
```python
import asyncio
from app.ai.vertex.client import VertexAIClient
from app.models.ai.models import BuildingType, RoomProgram

async def main():
    project_id = "your-gcp-project-id"
    location = "us-central1"
    vertex_client = VertexAIClient(project_id=project_id, location=location)

    correlation_id = "TEST_LAYOUT_001"
    prompt = "Create a small, modern 2-bedroom apartment layout with an open-plan living area."
    
    try:
        # Düzen oluşturma
        layout_response = await vertex_client.generate_layout(prompt, correlation_id)
        print("Oluşturulan Düzen (Ham Yanıt):")
        print(layout_response)

        # Sohbet ile modelle etkileşim
        messages = [
            {"role": "user", "text": "Bana 3 odalı bir ev için temel düzeni sağlayabilir misin?"}
        ]
        chat_response = await vertex_client.chat_with_model(messages, correlation_id)
        print("\nSohbet Yanıtı:")
        print(chat_response)
        
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Referansı
### `app.ai.vertex.client.VertexAIClient` Sınıfı
`IAIModelClient` arayüzünü uygulayan bu sınıfın ana metodları:

- `__init__(self, project_id: str, location: str, model_name: str = "gemini-2.5-flash-001")`
    - `project_id` (str): Google Cloud Proje Kimliği.
    - `location` (str): Vertex AI modelinin konuşlandırıldığı konum (örn. `us-central1`).
    - `model_name` (str, isteğe bağlı): Kullanılacak Gemini modelinin adı (varsayılan `gemini-2.5-flash-001`).

- `async generate_layout(self, prompt: str, correlation_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`
    - `prompt` (str): AI modeline gönderilecek komut istemi.
    - `correlation_id` (str): İşlemi izlemek için benzersiz kimlik.
    - `options` (Dict, isteğe bağlı): `generation_config` (örn. `temperature`, `max_output_tokens`) ve `safety_settings` gibi AI modeline özel ayarlar.
    - **Dönüş**: Ham JSON formatında AI yanıtı.
    - **İstisnalar**: `GoogleAPICallError`, genel `Exception`.

- `async analyze_project(self, project_data: Dict[str, Any], correlation_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`
    - `project_data` (Dict): Analiz edilecek proje verileri (henüz uygulanmadı).
    - `correlation_id` (str): İşlemi izlemek için benzersiz kimlik.
    - `options` (Dict, isteğe bağlı): AI modeline özel ayarlar.
    - **Dönüş**: `NotImplementedError` (Henüz uygulanmadığı için).

- `async chat_with_model(self, messages: List[Dict[str, Any]], correlation_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`
    - `messages` (List[Dict[str, Any]]): Çok turlu sohbetin mesaj geçmişi (örn. `[{"role": "user", "text": "Merhaba"}]`).
    - `correlation_id` (str): İşlemi izlemek için benzersiz kimlik.
    - `options` (Dict, isteğe bağlı): `generation_config` ve `safety_settings` gibi AI modeline özel ayarlar.
    - **Dönüş**: Ham JSON formatında AI yanıtı.
    - **İstisnalar**: `GoogleAPICallError`, genel `Exception`.

## Hata Yönetimi
`VertexAIClient`, Google Cloud API çağrıları sırasında oluşabilecek hataları yakalar ve `GoogleAPICallError` istisnasını yükseltir. Ayrıca, JSON ayrıştırma hatalarını ve diğer beklenmedik istisnaları da ele alır. Tüm hatalar `LoggerService` aracılığıyla loglanır ve çağrı yapan servislere yeniden yükseltilir.

- **`GoogleAPICallError`**: Vertex AI API ile ilgili sorunlar (kimlik doğrulama, kota, ağ sorunları).
- **`json.JSONDecodeError`**: AI modelinden gelen yanıtın geçerli bir JSON olmaması durumu.
- **`NotImplementedError`**: Henüz uygulanmamış metodlar çağrıldığında tetiklenir.

## Güvenlik
`VertexAIClient` doğrudan hassas verileri işlemez, ancak AI modellerine gönderilen komut istemlerinin ve alınan yanıtların içeriği hassas olabilir. Bu nedenle:
- **Kimlik Doğrulama**: Google Cloud kimlik bilgileri güvenli bir şekilde yönetilmelidir.
- **Veri Kısıtlamaları**: AI modellerine gönderilen veriler, gizlilik ve güvenlik politikalarına uygun olmalıdır.
- **Çıktı Doğrulama**: AI çıktılarının güvenliği ve uygunluğu için kapsamlı doğrulama ve insan incelemesi gereklidir.

## Konfigürasyon
`VertexAIClient`, `project_id`, `location` ve `model_name` gibi parametreler aracılığıyla başlatılır. Bu değerler genellikle uygulama yapılandırma servisinden (örn. bir `Settings` nesnesi) alınır. `options` parametresi aracılığıyla AI modelinin çalışma zamanı davranışları ayarlanabilir (örn. `temperature`).

## Loglama
`VertexAIClient`, tüm önemli işlemleri (`info`, `error`, `critical` seviyelerinde) `LoggerService` aracılığıyla loglar. Her log mesajı, ilgili işlemin izlenebilirliğini sağlamak için `correlation_id` içerir. Bu, sorun giderme, performans analizi ve güvenlik denetimi için kritik öneme sahiptir.