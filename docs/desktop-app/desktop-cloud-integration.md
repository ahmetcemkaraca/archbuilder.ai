# Masaüstü-Bulut Entegrasyonu Dokumentasyonu

## Genel Bakış
Bu belge, ArchBuilder.AI masaüstü uygulamasının bulut tabanlı arka uç (`cloud-server`) ile nasıl iletişim kurduğunu açıklamaktadır. Entegrasyon, özellikle `CloudApiClient`, `AuthService`, `FileUploadService`, `ProjectService` ve `SettingsService` gibi hizmetler aracılığıyla gerçekleştirilir. Amaç, güvenli, verimli ve ölçeklenebilir bir client-server iletişimi sağlamaktır.

## Kurulum ve Bağımlılıklar
Masaüstü-bulut entegrasyonu, `src/desktop-app` projesi içinde yer almaktadır ve aşağıdaki temel bağımlılıklara sahiptir:
- .NET 8.0 WPF
- `System.Net.Http` (HTTP istekleri için)
- `Newtonsoft.Json` (JSON serileştirme/deserileştirme için)
- `ArchBuilder.CloudClient` (API istemcisi)
- `ArchBuilder.Services` (Uygulama hizmetleri)

Bağımlılıklar, `src/desktop-app/ArchBuilder.csproj` dosyasında yönetilir ve `App.xaml.cs` dosyasındaki bağımlılık enjeksiyonu (`Microsoft.Extensions.DependencyInjection`) ile çözümlenir.

## Kullanım
### `CloudApiClient` ve `SettingsService` Entegrasyonu
`CloudApiClient`, uygulamanın bulut API'si ile etkileşim kuran temel bileşendir. API'nin temel URL'sini (`BaseAddress`), `SettingsService` aracılığıyla uygulama ayarlarından dinamik olarak alır. Bu, farklı ortamlar (geliştirme, hazırlık, üretim) arasında kolayca geçiş yapmayı sağlar.

**`CloudApiClient` Başlatma:**
```csharp
public class CloudApiClient
{
    private readonly HttpClient _httpClient;
    private readonly LoggerService _loggerService;
    private readonly AuthService _authService;
    private readonly SettingsService _settingsService; 

    public CloudApiClient(AuthService authService, LoggerService loggerService, SettingsService settingsService)
    {
        _authService = authService;
        _loggerService = loggerService;
        _settingsService = settingsService; // SettingsService enjekte edildi

        _httpClient = new HttpClient();
        _httpClient.BaseAddress = new Uri(_settingsService.CurrentSettings.CloudApiBaseUrl); // URL dinamik olarak ayarlandı
        _httpClient.DefaultRequestHeaders.Accept.Clear();
        _httpClient.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
    }
    // ... diğer metodlar
}
```

### Kimlik Doğrulama ve Yetkilendirme (`AuthService`)
`AuthService`, kullanıcıların bulut arka ucuna güvenli bir şekilde giriş yapmasını ve kaydolmasını sağlar. Başarılı bir girişin ardından alınan `AccessToken` ve `ApiKey`, sonraki tüm API isteklerinde `Authorization` başlığı olarak `CloudApiClient` tarafından kullanılır. Bu, kullanıcı oturumlarının ve API erişiminin güvenliğini sağlar.

```csharp
// CloudApiClient içinde Authorization başlığının ayarlanması
private void SetAuthorizationHeader()
{
    if (_authService.CurrentUserSession != null && _authService.CurrentUserSession.IsAuthenticated)
    {
        _httpClient.DefaultRequestHeaders.Authorization = 
            new AuthenticationHeaderValue("Bearer", _authService.CurrentUserSession.AccessToken);
    }
    else
    {
        _httpClient.DefaultRequestHeaders.Authorization = null;
    }
}
```

### Dosya Yükleme (`FileUploadService`)
`FileUploadService`, kullanıcıların DWG/DXF, IFC, PDF gibi dokümanları bulut sunucusuna güvenli ve ilerleme göstergeli bir şekilde yüklemesini sağlar. `ProgressableStreamContent` kullanarak yükleme ilerlemesi gerçek zamanlı olarak takip edilebilir.

```csharp
// FileUploadService içinde dosya yükleme örneği
public async Task UploadFileAsync(string filePath, string documentType, string projectId = null)
{
    // ... dosya akışı ve metadata oluşturma
    var progressContent = new ProgressableStreamContent(content, (sent, total) =>
    {
        UploadProgressChanged?.Invoke(filePath, sent, total); // İlerleme raporlama
    });
    
    var response = await _cloudApiClient.PostAsync<ProgressableStreamContent, dynamic>("documents/upload", progressContent);
    // ... yanıt işleme
}
```

### Proje Yönetimi (`ProjectService`)
`ProjectService`, bulut arka ucundaki proje yönetimi API'leri ile etkileşim kurarak proje oluşturma, listeleme ve detaylarını getirme gibi işlemleri gerçekleştirir. Bu servis de `CloudApiClient` üzerinden tüm HTTP iletişimini yönetir.

```csharp
// ProjectService içinde proje oluşturma örneği
public async Task<Project> CreateProjectAsync(string name, string description, Guid templateId)
{
    var createRequest = new { name = name, description = description, template_id = templateId };
    var response = await _cloudApiClient.PostAsync<object, Project>("projects/create", createRequest);
    return response;
}
```

## API Referansı
- **`ArchBuilder.CloudClient.CloudApiClient`**: Temel API iletişimini sağlayan HTTP istemcisi.
- **`ArchBuilder.Services.AuthService`**: Kullanıcı kimlik doğrulama ve oturum yönetimi.
- **`ArchBuilder.Services.FileUploadService`**: Dosya yükleme işlemleri ve ilerleme takibi.
- **`ArchBuilder.Services.ProjectService`**: Proje oluşturma, listeleme ve detaylarını yönetme.
- **`ArchBuilder.Services.SettingsService`**: Uygulama ayarlarını (API URL'si dahil) yönetme.

## Hata Yönetimi
Bulut entegrasyonundaki hatalar, `CloudClientException` gibi özel istisnalar aracılığıyla ele alınır ve `LoggerService` kullanılarak loglanır. Ağ hataları, API tarafından döndürülen özel hata mesajları ve diğer beklenmedik durumlar bu istisna mekanizması ile yönetilir. Kullanıcıya dostça hata mesajları gösterilir.

```csharp
catch (CloudClientException ccEx)
{
    _loggerService.LogError($"Bulut istemci hatası: {ccEx.Message}", ccEx);
    // Kullanıcıya hata mesajı gösterme
}
catch (HttpRequestException httpEx)
{
    // HTTP spesifik hataları ele alma
}
```

## Güvenlik
- **Token Tabanlı Kimlik Doğrulama**: Kullanıcı oturumları `Bearer Token` ve `API Key` ile güvence altına alınır.
- **HTTPS İletişimi**: Üretim ortamlarında `_httpClient.BaseAddress` HTTPS kullanacak şekilde yapılandırılır.
- **Veri Doğrulama**: Tüm API çağrılarında sunucu tarafında giriş verisi doğrulama (`input validation`) uygulanır.
- **Sızdırmazlık**: Hassas veriler doğrudan UI kontrollerinde tutulmaz; güvenli servisler aracılığıyla yönetilir.

## Konfigürasyon
Bulut API'sinin temel URL'si `SettingsService` aracılığıyla `appsettings.json` dosyasından veya çalışma zamanında ayarlanabilir. Bu, farklı dağıtım ortamları için kolayca yapılandırma yapılmasını sağlar.

```csharp
// AppSettings modelinde örnek konfigürasyon
public class AppSettings
{
    public string CloudApiBaseUrl { get; set; } = "http://localhost:8000/api/";
    // ... diğer ayarlar
}
```

## Loglama
`CloudApiClient`, `AuthService`, `FileUploadService` ve `ProjectService` gibi tüm entegrasyon servisleri, işlemlerin gidişatını, hataları ve önemli olayları `LoggerService` aracılığıyla detaylı bir şekilde loglar. Bu, sorun giderme ve sistem izleme için kritik öneme sahiptir.

```csharp
_loggerService.LogInfo($"GET isteği gönderiliyor: {requestUri}");
_loggerService.LogError($"Bulut istemci hatası (Proje oluşturma): {ccEx.Message}", ccEx);
```
