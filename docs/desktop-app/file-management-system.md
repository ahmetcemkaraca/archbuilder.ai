# Dosya Yönetim Sistemi Dokumentasyonu

## Genel Bakış
Bu belge, ArchBuilder.AI masaüstü uygulamasının yerel dosya sistemiyle etkileşimini yöneten `FileManagementService`'i açıklamaktadır. Servis, dosya ve dizinleri listeleme, dosya içeriği okuma, dosya ve dizin yolları üzerinde işlemler yapma gibi temel işlevleri sağlar. Amacımız, uygulamanın dosya sistemi üzerinde güvenli ve verimli bir şekilde çalışmasını sağlamaktır.

## Kurulum ve Bağımlılıklar
`FileManagementService`, `src/desktop-app` projesi içinde yer almaktadır ve aşağıdaki temel bağımlılıklara sahiptir:
- .NET 8.0 WPF
- `System.IO` (Dosya sistemi işlemleri için)
- `ArchBuilder.Services.LoggerService` (Loglama için)

Servis, `App.xaml.cs` dosyasındaki bağımlılık enjeksiyonu (`Microsoft.Extensions.DependencyInjection`) ile tekil (`Singleton`) olarak kaydedilir.

**`App.xaml.cs`'de Kayıt:**
```csharp
services.AddSingleton<FileManagementService>();
```

## Kullanım
`FileManagementService`, uygulamanın herhangi bir yerinden yerel dosya sistemi işlemleri yapmak için kullanılabilir. Bir ViewModel veya başka bir servis içinde bağımlılık enjeksiyonu aracılığıyla elde edilebilir.

**Örnek Kullanım:**
```csharp
public class MyViewModel : ObservableObject
{
    private readonly FileManagementService _fileManagementService;
    private readonly LoggerService _loggerService;

    public MyViewModel(FileManagementService fileManagementService, LoggerService loggerService)
    {
        _fileManagementService = fileManagementService;
        _loggerService = loggerService;
    }

    public async Task LoadFilesFromDirectory(string directoryPath)
    {
        try
        {
            var contents = await _fileManagementService.ListDirectoryContentsAsync(directoryPath);
            foreach (var item in contents)
            {
                _loggerService.LogInfo($"Dizin İçeriği: {item}");
            }

            string filePath = Path.Combine(directoryPath, "example.txt");
            string fileContent = await _fileManagementService.ReadFileContentAsync(filePath);
            _loggerService.LogInfo($"Dosya İçeriği ({filePath}):\n{fileContent}");
        }
        catch (FileManagementService.FileManagementException ex)
        {
            _loggerService.LogError($"Dosya yönetimi hatası: {ex.Message}");
        }
        catch (Exception ex)
        {
            _loggerService.LogCritical($"Beklenmedik hata: {ex.Message}");
        }
    }
}
```

## API Referansı
### `ArchBuilder.Services.FileManagementService`
`FileManagementService` sınıfının halka açık (public) API'ları ve üyeleri.

```csharp
public class FileManagementService
{
    public FileManagementService(LoggerService loggerService);

    // Metodlar
    public Task<List<string>> ListDirectoryContentsAsync(string path);
    public Task<string> ReadFileContentAsync(string filePath);
    public string GetFileExtension(string filePath);
    public string GetFileName(string filePath);
    public string GetDirectoryName(string filePath);
    public string GetCurrentDirectory();

    // İç içe istisna sınıfı
    public class FileManagementException : Exception
    {
        public FileManagementException(string message) : base(message) { }
        public FileManagementException(string message, Exception innerException) : base(message, innerException) { }
    }
}
```

## Hata Yönetimi
`FileManagementService`, dosya sistemi işlemleri sırasında oluşabilecek hataları yakalar ve `FileManagementException` özel istisna sınıfı aracılığıyla iletir. `UnauthorizedAccessException`, `DirectoryNotFoundException`, `FileNotFoundException` gibi yaygın dosya sistemi hataları yakalanır ve loglanır. Bu, uygulamanın dosya sistemi sorunlarına karşı daha sağlam olmasını sağlar.

```csharp
catch (UnauthorizedAccessException ex)
{
    _loggerService.LogError($"Dizin erişim hatası ({path}): {ex.Message}", ex);
    throw new FileManagementException($"Dizin erişim izni yok: {path}", ex);
}
```

## Güvenlik
`FileManagementService` doğrudan kullanıcı girdisi almaz veya hassas verileri işlemez. Ancak, dosya sistemi erişim izinleri ve uygulamanın çalıştığı ortamın güvenlik yapılandırması önemlidir. Uygulama, kullanıcının erişim yetkisi olmayan dosyalara erişmeye çalışmamalı ve güvenlik açıklarına yol açabilecek kötü niyetli dosya yollarına karşı dikkatli olmalıdır. Tüm dosya işlemleri, işletim sisteminin güvenlik politikaları dahilinde gerçekleştirilir.

## Konfigürasyon
`FileManagementService`'in doğrudan bir konfigürasyonu yoktur. Davranışı, çağrıldığı metodlara iletilen dosya yolları ve parametreler aracılığıyla belirlenir.

## Loglama
Tüm `FileManagementService` işlemleri, `LoggerService` aracılığıyla detaylı bir şekilde loglanır. Başarılı işlemler `LogInfo`, uyarılar `LogWarning` ve hatalar `LogError` veya `LogCritical` ile kaydedilir. Bu, dosya sistemi etkileşimlerini izlemek ve sorun gidermek için kritik öneme sahiptir.

```csharp
_loggerService.LogInfo($"Dizin içeriği listelendi: {path}");
_loggerService.LogWarning($"Dosya bulunamadı: {filePath}");
_loggerService.LogCritical($"Dosya okuma sırasında beklenmedik hata ({filePath}): {ex.Message}", ex);
```


