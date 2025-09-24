# Belge Yükleme Sistemi Dokumentasyonu

## Genel Bakış
Bu belge, ArchBuilder.AI masaüstü uygulamasının kullanıcıların mimari belgeleri (DWG/DXF, IFC, PDF gibi) bulut sunucusuna güvenli ve verimli bir şekilde nasıl yüklediğini açıklamaktadır. Yüklenen belgeler daha sonra AI destekli işleme tabi tutulacaktır.

## Mimari
Belge yükleme sistemi, masaüstü uygulamasından bulut sunucusuna `multipart/form-data` formatında HTTP POST istekleri göndererek çalışır. Yükleme sırasında ilerleme takibi yapılır ve hatalar yönetilir. Yüklenen dosyalar bulut tarafında güvenli bir şekilde depolanır ve işleme kuyruğuna eklenir.

```mermaid
graph LR
    A[Desktop Uygulaması] -- Dosya Seçimi --> B(FileUploadService)
    B -- Yükleme İsteği (HTTP POST) --> C(Cloud Server API)
    C -- Depolama & Kuyruk --> D(Bulut Depolama & İşleme Kuyruğu)
    B -- İlerleme & Durum Güncellemesi --> A
```

## Kurulum ve Bağımlılıklar

### Masaüstü Uygulaması (C#)
- `System.Net.Http`: HTTP istekleri göndermek için.
- `System.IO`: Dosya okuma işlemleri için.
- `ArchBuilder.CloudClient.CloudApiClient`: Bulut API'si ile iletişim için.
- `ArchBuilder.Services.LoggerService`: Loglama için.
- `Newtonsoft.Json`: JSON serileştirme/deserileştirme için.

### Bulut Sunucusu (Python)
- FastAPI
- `python-multipart`: Dosya yüklemelerini işlemek için.
- Bulut depolama entegrasyonu (örn. Google Cloud Storage, AWS S3)
- Arka plan görev kuyruğu (örn. Celery, RQ)

## Kullanım
Dosya yükleme süreci, kullanıcının masaüstü uygulamasında bir veya daha fazla dosya seçmesiyle başlar. `FileUploadService`, seçilen dosyaları okur, bulut API'sine gönderir ve yükleme ilerlemesini izler.

### Örnek: FileUploadService Sınıfı
```csharp
using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using ArchBuilder.CloudClient;
using ArchBuilder.Services;
using Newtonsoft.Json;
using ArchBuilder.Core; // HttpRequestExceptionExtensions için

namespace ArchBuilder.Services
{
    public class FileUploadService
    {
        private readonly CloudApiClient _cloudApiClient;
        private readonly LoggerService _loggerService;

        public event Action<string, long, long> UploadProgressChanged;
        public event Action<string, bool, string> UploadCompleted;

        public FileUploadService(CloudApiClient cloudApiClient, LoggerService loggerService)
        {
            _cloudApiClient = cloudApiClient;
            _loggerService = loggerService;
        }

        public async Task UploadFileAsync(string filePath, string documentType, string projectId = null)
        {
            if (!File.Exists(filePath))
            {
                _loggerService.LogError($"Yükleme başarısız: Dosya bulunamadı - {filePath}");
                UploadCompleted?.Invoke(filePath, false, "Dosya bulunamadı.");
                return;
            }

            try
            {
                using (var fileStream = File.OpenRead(filePath))
                {
                    using (var content = new MultipartFormDataContent())
                    {
                        var fileContent = new StreamContent(fileStream);
                        fileContent.Headers.Add("Content-Type", "application/octet-stream"); // Veya MIME type
                        content.Add(fileContent, "file", Path.GetFileName(filePath));

                        // Metadata ekleme
                        var metadata = new {
                            document_type = documentType,
                            project_id = projectId,
                            file_name = Path.GetFileName(filePath),
                            file_size = fileStream.Length
                        };
                        content.Add(new StringContent(JsonConvert.SerializeObject(metadata)), "metadata");

                        // İlerleme raporlama için özel HttpContent
                        var progressContent = new ProgressableStreamContent(content, (sent, total) =>
                        {
                            UploadProgressChanged?.Invoke(filePath, sent, total);
                        });
                        
                        _loggerService.LogInfo($"Dosya yükleniyor: {filePath}");
                        var response = await _cloudApiClient.PostAsync<ProgressableStreamContent, dynamic>("documents/upload", progressContent);

                        // Yanıtı işleme
                        bool success = response.status == "success";
                        string message = response.message ?? (success ? "Yükleme başarılı." : "Yükleme başarısız.");
                        string documentId = response.document_id;

                        _loggerService.LogInfo($"Dosya yükleme tamamlandı: {filePath}, Başarılı: {success}, Mesaj: {message}");
                        UploadCompleted?.Invoke(filePath, success, message);
                    }
                }
            }
            catch (CloudClientException ccEx)
            {
                _loggerService.LogError($"Bulut istemci hatası ({filePath}): {ccEx.Message}", ccEx);
                UploadCompleted?.Invoke(filePath, false, $"Bulut sunucusu hatası: {ccEx.Message}");
            }
            catch (HttpRequestException httpEx)
            {
                string errorResponse = await httpEx.GetResponseContentAsync();
                _loggerService.LogError($"HTTP isteği hatası ({filePath}): {httpEx.StatusCode} - {errorResponse}", httpEx);
                UploadCompleted?.Invoke(filePath, false, $"Ağ hatası: {GetErrorMessageFromJson(errorResponse)}");
            }
            catch (Exception ex)
            {
                _loggerService.LogCritical($"Dosya yükleme sırasında beklenmedik hata ({filePath}): {ex.Message}", ex);
                UploadCompleted?.Invoke(filePath, false, $"Beklenmedik hata: {ex.Message}");
            }
        }

        private string GetErrorMessageFromJson(string jsonErrorResponse)
        {
            try
            {
                dynamic errorObj = JsonConvert.DeserializeObject(jsonErrorResponse);
                if (errorObj?.detail != null)
                {
                    return errorObj.detail;
                }
                return "Bilinmeyen bir hata oluştu.";
            }
            catch
            {
                return "Yanıt formatı okunamadı.";
            }
        }

        // İlerleme raporlama için özel HttpContent sınıfı (ArchBuilder.Core'a taşınabilir)
        public class ProgressableStreamContent : HttpContent
        {
            private const int DefaultBufferSize = 4096;
            private readonly HttpContent _content;
            private readonly Action<long, long> _progressCallback;

            public ProgressableStreamContent(HttpContent content, Action<long, long> progressCallback)
            {
                _content = content;
                _progressCallback = progressCallback;
                Headers.ContentType = content.Headers.ContentType;
                foreach (var header in content.Headers)
                {
                    Headers.TryAddWithoutValidation(header.Key, header.Value);
                }
            }

            protected override async Task SerializeToStreamAsync(Stream stream, System.Net.TransportContext context)
            {
                var httpStream = await _content.ReadAsStreamAsync();
                var totalLength = _content.Headers.ContentLength ?? -1L;
                var buffer = new byte[DefaultBufferSize];
                var readLength = 0L;
                var length = 0;

                while ((length = await httpStream.ReadAsync(buffer, 0, buffer.Length)) != 0)
                {
                    await stream.WriteAsync(buffer, 0, length);
                    readLength += length;
                    _progressCallback?.Invoke(readLength, totalLength);
                }
            }

            protected override bool TryComputeLength(out long length)
            {
                length = _content.Headers.ContentLength ?? -1L;
                return _content.Headers.ContentLength.HasValue;
            }
        }
    }
}
```

## API Referansı (Bulut Sunucusu)

### Belge Yükleme Endpoint'i
- `POST /api/documents/upload`: Yeni bir belgeyi yükler ve işleme kuyruğuna ekler.
  - **İstek Başlıkları**: `Authorization: Bearer <token>`
  - **İstek Gövdesi**: `multipart/form-data`
    - `file`: Yüklenecek dosya içeriği.
    - `metadata`: Dosya türü (`document_type`), proje ID'si (`project_id`), dosya adı (`file_name`) gibi JSON formatında metadata.
  - **Yanıt**: 
    ```json
    {
      "status": "success",
      "message": "Dosya başarıyla yüklendi ve işleme alındı.",
      "document_id": "[UUID]",
      "file_name": "example.pdf",
      "upload_time": "[ISO Format Tarih]"
    }
    ```

## Hata Yönetimi
- **Ağ Hataları**: Bağlantı kopmaları, sunucu erişim sorunları `HttpRequestException` ile yakalanır.
- **API Hataları**: Bulut sunucusundan gelen uygulama düzeyindeki hatalar `CloudClientException` olarak işlenir.
- **Dosya Hataları**: Dosya bulunamadı, erişim reddedildi gibi yerel dosya hataları.

Tüm hatalar `LoggerService` kullanılarak kaydedilir ve kullanıcıya yönelik anlaşılır mesajlar sağlanır.

## Güvenlik
- **Kimlik Doğrulama**: Tüm yükleme istekleri JWT veya API anahtarı ile doğrulanır.
- **HTTPS**: Güvenli iletişim için HTTPS kullanılır.
- **Dosya Doğrulama**: Bulut sunucusu, yüklenen dosyaların türünü, boyutunu ve güvenliğini (virüs taraması gibi) doğrular.

## Konfigürasyon
Bulut sunucusunun `documents/upload` endpoint'i ve dosya boyut limitleri gibi ayarlar, masaüstü uygulamasının `appsettings.json` dosyasında yapılandırılmalıdır.

## Günlük Kaydı (Logging)
Dosya yükleme başlangıcı, ilerlemesi, tamamlanması veya başarısız olması durumları `LoggerService` kullanılarak detaylı bir şekilde loglanır. Bu, sorun giderme ve yükleme süreçlerini izleme için esastır.
