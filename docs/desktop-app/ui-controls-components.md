# Masaüstü UI Kontrolleri ve Bileşenleri Dokumentasyonu

## Genel Bakış
Bu belge, ArchBuilder.AI masaüstü uygulamasının Apple-vari sade arayüz tasarımını desteklemek için geliştirilen özel UI kontrolleri ve bileşenlerini açıklamaktadır. Amaç, kullanıcı deneyimini zenginleştirmek ve tutarlı bir görsel dil sağlamaktır.

## Tasarım Prensipleri
-   **Sadelik**: Karmaşık olmayan, temiz ve anlaşılır tasarımlar.
-   **Kullanılabilirlik**: Kolay öğrenilebilir ve sezgisel etkileşimler.
-   **Tutarlılık**: Uygulama genelinde aynı görsel ve etkileşimsel kurallar.
-   **Estetik**: Modern ve hoş bir görünüm.
-   **Yanıt Verebilirlik**: Farklı ekran boyutlarına ve DPI ayarlarına uyum sağlayabilen tasarımlar.

## Kurulum ve Bağımlılıklar

### Masaüstü Uygulaması (C# / WPF)
-   WPF XAML:
    -   `ArchBuilder.Controls` namespace'i altında özel kontroller.
    -   `ArchBuilder.Styles` namespace'i altında tema ve stil tanımları.
-   ViewModel ve Hizmet Katmanları ile entegrasyon.

## Kullanım
Özel UI kontrolleri ve bileşenleri, uygulamanın farklı görünümlerinde (views) kullanılarak tutarlı bir kullanıcı deneyimi sağlar. Örneğin, `ProgressIndicator` uzun süren işlemler için geri bildirim sağlarken, `FileDropZone` dosya yükleme işlemlerini kolaylaştırır.

### Örnek: ProgressIndicator Kontrolü
```xml
<UserControl x:Class="ArchBuilder.Controls.ProgressIndicator"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
             xmlns:d="http://schemas.microsoft.com/expression/blend/2008"
             mc:Ignorable="d"
             d:DesignHeight="100" d:DesignWidth="300">
    <Grid>
        <StackPanel Orientation="Horizontal" VerticalAlignment="Center" HorizontalAlignment="Center">
            <ProgressBar IsIndeterminate="True" Style="{DynamicResource ModernProgressBar}" Width="100" Height="10" Margin="0,0,10,0"/>
            <TextBlock Text="Yükleniyor..." Style="{DynamicResource BodyTextStyle}" VerticalAlignment="Center"/>
        </StackPanel>
    </Grid>
</UserControl>
```

### Örnek: FileDropZone Kontrolü
```xml
<UserControl x:Class="ArchBuilder.Controls.FileDropZone"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
             xmlns:d="http://schemas.microsoft.com/expression/blend/2008"
             mc:Ignorable="d"
             d:DesignHeight="150" d:DesignWidth="400"
             AllowDrop="True"
             Drop="FileDropZone_Drop"
             DragEnter="FileDropZone_DragEnter"
             DragLeave="FileDropZone_DragLeave">
    <Border x:Name="DropBorder" BorderBrush="{DynamicResource AccentBrush}" BorderThickness="2" CornerRadius="10" BorderDashArray="4 2">
        <StackPanel VerticalAlignment="Center" HorizontalAlignment="Center">
            <TextBlock Text="Dosyaları Buraya Sürükle Bırak" Style="{DynamicResource SubtitleTextStyle}" TextAlignment="Center" Margin="0,0,0,10"/>
            <TextBlock Text="veya" Style="{DynamicResource BodyTextStyle}" TextAlignment="Center" Margin="0,0,0,10"/>
            <Button Content="Dosya Seç" Style="{DynamicResource SecondaryButton}" Command="{Binding SelectFileCommand}"/>
        </StackPanel>
    </Border>
</UserControl>
```

## API Referansı
Özel kontroller genellikle doğrudan XAML üzerinden kullanılır ve ViewModel'lerden veri bağlama (`Binding`) ile yönetilir. Kontroller, olaylar (`Events`) veya komutlar (`Commands`) aracılığıyla etkileşim sağlar.

## Hata Yönetimi
Kontrol düzeyinde görsel geri bildirimler (örn. `Validation.ErrorTemplate`) veya hata mesajlarının gösterimi için standart mekanizmalar kullanılır.

## Güvenlik
UI kontrolleri doğrudan güvenlik hassasiyetine sahip değildir; ancak veri girişi yapılan kontrollerde (örn. `PasswordBox`), veri güvenliği `ViewModel` ve servis katmanında sağlanmalıdır.

## Konfigürasyon
Kontrollerin görünümü ve davranışı, XAML stilleri, tema kaynakları ve ViewModel'deki özellikler aracılığıyla yapılandırılır.

## Günlük Kaydı (Logging)
UI etkileşimleri veya kontrol durum değişiklikleri gibi önemli olaylar, `LoggerService` kullanılarak kaydedilebilir. Bu, kullanıcı deneyimi sorunlarının teşhis edilmesine yardımcı olur.
