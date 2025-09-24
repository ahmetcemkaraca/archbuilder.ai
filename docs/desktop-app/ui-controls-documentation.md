# UI Kontrolleri ve Bileşenleri Dokumentasyonu

## Genel Bakış
Bu belge, ArchBuilder.AI masaüstü uygulamasında kullanılan temel UI kontrollerini ve bileşenlerini, özellikle `FileDropZone` ve `ProgressIndicator` gibi özel kontrolleri açıklamaktadır. Amacımız, Apple-vari sade bir arayüz ile kullanıcı deneyimini zenginleştirmek ve yapay zeka destekli süreçlerin şeffaf bir şekilde yönetilmesini sağlamaktır.

## Kurulum ve Bağımlılıklar
UI kontrolleri, ArchBuilder.AI masaüstü uygulaması (`src/desktop-app`) projesi içinde geliştirilmiştir ve aşağıdaki bağımlılıklara sahiptir:
- .NET 8.0 WPF
- `Newtonsoft.Json` (Ayarlar ve diğer veri serileştirme işlemleri için)

Projeye eklemek için `src/desktop-app/ArchBuilder.csproj` dosyasının doğru referansları içerdiğinden emin olun.

## Kullanım
### Colors.xaml
Uygulama genelinde tutarlı bir renk paleti sağlamak için `Styles/Colors.xaml` dosyası kullanılmaktadır. Bu dosya, uygulamanın ana renklerini `SolidColorBrush` kaynakları olarak tanımlar. Kontrollerinizde bu renkleri kullanmak için `StaticResource` veya `DynamicResource` işaretlemelerini kullanabilirsiniz.

```xaml
<UserControl
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Background="{StaticResource BackgroundBrush}">
    <Border BorderBrush="{StaticResource BorderBrush}" BorderThickness="1">
        <TextBlock Text="Merhaba Dünya!" Foreground="{StaticResource ForegroundBrush}" />
    </Border>
</UserControl>
```

### FileDropZone Kontrolü
`FileDropZone` kontrolü, kullanıcının dosya sürükle-bırak yoluyla dosya yüklemesini kolaylaştırmak için tasarlanmıştır. Görsel geri bildirim (sürükle-bırak sırasında arka plan rengi değişimi) ve bırakılan dosyaların işlenmesi için olay işleyicileri içerir.

**XAML Tanımı:**
```xaml
<controls:FileDropZone 
    xmlns:controls="clr-namespace:ArchBuilder.Controls"
    Width="400" Height="200"
    VerticalAlignment="Center" HorizontalAlignment="Center"
    DropText="Dosyaları buraya sürükleyin veya tıklayın"
    Command="{Binding ProcessDroppedFilesCommand}" />
```

**Özellikler (Properties):**
- `DropText`: Sürükle-bırak alanı içinde gösterilecek metin.
- `Command`: Dosyalar bırakıldığında çalıştırılacak `ICommand` (genellikle bir ViewModel'den).
- `CommandParameter`: `Command`'e iletilecek parametre.

**Olaylar (Events) [Code-behind]:**
- `DragEnter`: Bir dosya sürüklenirken kontrol alanına girdiğinde tetiklenir.
- `DragLeave`: Bir dosya sürüklenirken kontrol alanından çıktığında tetiklenir.
- `Drop`: Bir dosya kontrol alanına bırakıldığında tetiklenir.

### ProgressIndicator Kontrolü
`ProgressIndicator` kontrolü, uzun süreli işlemler (özellikle AI işlemleri) sırasında kullanıcıya görsel geri bildirim sağlamak için kullanılır. Gerçekçi zamanlamalar ve adım adım ilerleme göstergeleri ile kullanıcı deneyimini iyileştirmeyi hedefler.

**XAML Tanımı:**
```xaml
<controls:ProgressIndicator 
    xmlns:controls="clr-namespace:ArchBuilder.Controls"
    Width="300" Height="100"
    CurrentStageText="Gereksinimler Analiz Ediliyor..."
    OverallProgressValue="30" />
```

**Özellikler (Properties):**
- `CurrentStageText`: Mevcut ilerleme adımını açıklayan metin.
- `OverallProgressValue`: Genel ilerleme yüzdesi (0-100 arası).

## API Referansı
### `ArchBuilder.Controls.FileDropZone`
`FileDropZone` kontrolünün halka açık (public) API'ları ve üyeleri.

```csharp
public partial class FileDropZone : UserControl
{
    // Dependency Properties
    public static readonly DependencyProperty DropTextProperty;
    public static readonly DependencyProperty CommandProperty;
    public static readonly DependencyProperty CommandParameterProperty;

    // Public Properties
    public string DropText { get; set; }
    public ICommand Command { get; set; }
    public object CommandParameter { get; set; }

    // Constructor
    public FileDropZone();

    // Event Handlers (internal to control's logic, can be exposed via custom events if needed)
    protected void FileDropZone_DragEnter(object sender, DragEventArgs e);
    protected void FileDropZone_DragLeave(object sender, DragEventArgs e);
    protected void FileDropZone_Drop(object sender, DragEventArgs e);
}
```

### `ArchBuilder.Controls.ProgressIndicator`
`ProgressIndicator` kontrolünün halka açık (public) API'ları ve üyeleri.

```csharp
public partial class ProgressIndicator : UserControl
{
    // Dependency Properties
    public static readonly DependencyProperty CurrentStageTextProperty;
    public static readonly DependencyProperty OverallProgressValueProperty;

    // Public Properties
    public string CurrentStageText { get; set; }
    public double OverallProgressValue { get; set; }

    // Constructor
    public ProgressIndicator();
}
```

## Hata Yönetimi
UI kontrollerindeki hatalar genellikle uygulama düzeyinde yakalanır ve `LoggerService` aracılığıyla loglanır. Özellikle `FileDropZone` gibi dosya işlemleri içeren kontrollerde, dosya erişim hataları veya geçersiz dosya formatları gibi durumlar uygun şekilde ele alınmalı ve kullanıcıya geri bildirim sağlanmalıdır.

- **Dosya İşleme Hataları**: `FileDropZone` içinde tetiklenen `Command`'in işleyicisinde (ViewModel tarafında), dosya işleme sırasında oluşabilecek hatalar (`IOException`, `UnauthorizedAccessException` vb.) yakalanmalı ve kullanıcıya `ErrorMessage` aracılığıyla bilgi verilmelidir.
- **UI Güncelleme Hataları**: `ProgressIndicator` gibi kontrollerde veri bağlama veya UI güncellemeleri sırasında oluşabilecek hatalar, ViewModel tarafından ele alınmalı ve loglanmalıdır. Genellikle `Dispatcher.Invoke` kullanılarak UI thread'inde güvenli güncellemeler yapılmalıdır.

## Güvenlik
UI kontrolleri doğrudan hassas verilerle etkileşime girmez. Ancak, `FileDropZone` gibi kontroller aracılığıyla yüklenen dosyaların güvenli bir şekilde işlenmesi ve `CloudApiClient` üzerinden bulut sunucusuna gönderilmesi `FileUploadService` tarafından sağlanır. Güvenlik, genel uygulama mimarisinin bir parçasıdır ve UI katmanı sadece güvenli servislerle etkileşim kurar.

## Konfigürasyon
UI kontrollerinin görünümü ve davranışı genellikle `Styles/Colors.xaml` ve `Styles/AppleTheme.xaml` gibi XAML kaynakları aracılığıyla yapılandırılır. Dinamik değerler için ViewModel'ler aracılığıyla veri bağlama kullanılır.

## Loglama
UI kontrolleri, uygulama içinde meydana gelen önemli olayları (örn. dosya bırakma, ilerleme güncellemeleri) `LoggerService` aracılığıyla loglayabilir. Bu, hata ayıklama ve kullanıcı davranışını izleme açısından önemlidir.

```csharp
// Örnek loglama kullanımı (FileDropZone.xaml.cs içinde)
Services.LoggerService.Instance.LogInfo($"{files.Length} dosya bırakıldı.");
```

