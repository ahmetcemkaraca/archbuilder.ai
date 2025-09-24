# Masaüstü Uygulaması Test Çerçevesi Kurulumu Dokumentasyonu

## Genel Bakış
Bu belge, ArchBuilder.AI masaüstü uygulamasının (WPF) test çerçevesinin nasıl kurulduğunu ve test stratejilerini açıklamaktadır. Amaç, uygulamanın kalitesini, güvenilirliğini ve performansını sağlamak için kapsamlı bir test ortamı oluşturmaktır.

## Test Stratejisi
Masaüstü uygulaması için aşağıdaki test türleri uygulanacaktır:
-   **Birim Testleri (Unit Tests)**: Her bir sınıfın veya metodun izole bir şekilde doğru çalışıp çalışmadığını doğrular.
-   **Entegrasyon Testleri (Integration Tests)**: Farklı bileşenlerin (örn. ViewModel ile Service) birbiriyle doğru etkileşimde bulunup bulunmadığını kontrol eder.
-   **UI Testleri (UI Tests - Opsiyonel)**: Kullanıcı arayüzü bileşenlerinin görsel ve etkileşimsel doğruluğunu test eder (öncelik daha düşük olabilir).

## Kurulum ve Bağımlılıklar

### Test Projesi (`src/desktop-app.Tests/`)
-   **Test Framework**: `xUnit` (önerilir)
-   **Mocking Kütüphanesi**: `Moq` (önerilir)
-   **Diğer Bağımlılıklar**:
    -   `Microsoft.NET.Test.Sdk`
    -   `ArchBuilder.Desktop` (ana uygulama projesine referans)
    -   `Microsoft.Extensions.DependencyInjection` (DI testleri için)
    -   `Microsoft.Reactive.Testing` (Reaktif UI testleri için - opsiyonel)

### Örnek `csproj` Yapılandırması
```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWPF>true</UseWPF>
    <IsPackable>false</IsPackable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
    <PackageReference Include="xunit" Version="2.6.4" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.5.6">
      <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
      <PrivateAssets>all</PrivateAssets>
    </PackageReference>
    <PackageReference Include="Moq" Version="4.20.70" />
    <PackageReference Include="Microsoft.Extensions.DependencyInjection" Version="8.0.0" />
    <!-- Diğer test bağımlılıkları buraya eklenecek -->
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\desktop-app\ArchBuilder.csproj" />
  </ItemGroup>

</Project>
```

## Kullanım
Testler `xUnit` framework'ü kullanılarak yazılacak ve `dotnet test` komutu veya Visual Studio Test Explorer aracılığıyla çalıştırılacaktır. `Moq`, servis bağımlılıklarını izole etmek ve test edilecek birimi taklit etmek için kullanılacaktır.

### Örnek: AuthService Birim Testi
```csharp
using Xunit;
using Moq;
using System.Security;
using System.Threading.Tasks;
using ArchBuilder.Services;
using ArchBuilder.CloudClient;
using ArchBuilder.Models;

public class AuthServiceTests
{
    private readonly Mock<CloudApiClient> _mockCloudApiClient;
    private readonly Mock<LoggerService> _mockLoggerService;
    private readonly AuthService _authService;

    public AuthServiceTests()
    {
        _mockCloudApiClient = new Mock<CloudApiClient>();
        _mockLoggerService = new Mock<LoggerService>();
        _authService = new AuthService(_mockCloudApiClient.Object, _mockLoggerService.Object);
    }

    [Fact]
    public async Task LoginAsync_ValidCredentials_ReturnsSuccess()
    {
        // Arrange
        var email = "test@example.com";
        var password = new SecureString();
        password.AppendChar('p'); // ... fill password ...

        _mockCloudApiClient.Setup(client => client.PostAsync<object, AuthService.TokenResponse>(
            "auth/login", It.IsAny<object>()))
            .ReturnsAsync(new AuthService.TokenResponse
            {
                AccessToken = "fake_token",
                ApiKey = "fake_api_key",
                SubscriptionTier = "Free",
                UsageRemaining = 100,
                UserId = Guid.NewGuid(),
                FirstName = "Test",
                LastName = "User"
            });

        // Act
        var result = await _authService.LoginAsync(email, password);

        // Assert
        Assert.True(result.Success);
        Assert.NotNull(_authService.CurrentUserSession);
        Assert.Equal(email, _authService.CurrentUserSession.Email);
    }

    [Fact]
    public async Task RegisterAsync_ExistingEmail_ReturnsFail()
    {
        // Arrange
        var firstName = "Test";
        var lastName = "User";
        var email = "existing@example.com";
        var password = new SecureString();
        password.AppendChar('p'); // ... fill password ...

        _mockCloudApiClient.Setup(client => client.PostAsync<object, ArchBuilder.Services.AuthService.UserResponse>(
            "auth/register", It.IsAny<object>()))
            .ThrowsAsync(new CloudClientException("Bu e-posta zaten kayıtlı."));

        // Act
        var result = await _authService.RegisterAsync(firstName, lastName, email, password);

        // Assert
        Assert.False(result.Success);
        Assert.Contains("Bu e-posta zaten kayıtlı.", result.Message);
    }
}
```

## Testleri Çalıştırma

### Komut Satırı Üzerinden
Test projesinin kök dizininde (`src/desktop-app.Tests/`):
```bash
dotnet test
```

### Visual Studio Üzerinden
Visual Studio Test Explorer'ı kullanarak testleri çalıştırabilirsiniz (`Test > Test Explorer`).

## Hata Yönetimi ve Raporlama
Testler sırasında oluşan hatalar, test framework'ü tarafından raporlanır. CI/CD süreçlerine entegre edildiğinde, test başarısızlıkları yapılandırma sorunlarını otomatik olarak tetikleyecektir.

## Kod Kapsamı (Code Coverage)
Testlerin kod kapsamını ölçmek için `dotnet test --collect:"XPlat Code Coverage"` komutu kullanılabilir. %70 üzeri kod kapsamı hedeflemek, testlerin kalitesini artıracaktır.
