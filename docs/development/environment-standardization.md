# Geliştirme Ortamı Standardizasyonu Dokumentasyonu

## Genel Bakış
Bu belge, ArchBuilder.AI projesi için geliştirme ortamının standartlaştırılmasına yönelik yönergeleri açıklamaktadır. Amaç, tüm geliştiriciler arasında tutarlı bir kodlama deneyimi sağlamak, kod kalitesini artırmak ve CI/CD süreçlerini kolaylaştırmaktır.

## Temel Prensipler
-   **Tutarlılık**: Tüm kod tabanında aynı kodlama standartları ve biçimlendirme kuralları uygulanır.
-   **Otomasyon**: Mümkün olduğunca çok geliştirme görevi otomatikleştirilir (formatlama, linting, testler).
-   **Verimlilik**: Geliştirme sürecini hızlandıran ve hata oranını düşüren araçlar ve uygulamalar kullanılır.
-   **Ortam İzolasyonu**: Geliştirme ortamları (Python sanal ortamları, Docker) izole edilir.

## Kurulum ve Bağımlılıklar

### Ortak Araçlar
-   **Git**: Sürüm kontrol sistemi.
-   **Docker**: Konteynerizasyon ve ortam izolasyonu için.
-   **Visual Studio Code / Visual Studio**: IDE (tercih edilen).
-   **.NET SDK**: C# projeleri için (net8.0).
-   **Python 3.12**: Python projeleri için (CI ile sabitlenmiş).
-   **pip**: Python paket yöneticisi.
-   **npm / yarn**: Frontend veya JavaScript tabanlı araçlar için (Electron masaüstü uygulaması kullanılıyorsa).

### Proje Bazlı Araçlar
-   **Python Linting & Formatting**: `ruff`, `black`, `isort`.
-   **C# Linting & Formatting**: `.editorconfig` ve Visual Studio/Rider Code Cleanup ayarları.
-   **Veritabanı Yönetimi**: `Alembic` (Python için veritabanı migration'ları).
-   **Test Frameworkleri**: `pytest` (Python), `xUnit` (C#).

## Kod Kalitesi ve Standardizasyon

### Kod Formatlama
-   **Python**: `black` otomatik formatlayıcı ve `isort` import sıralayıcı kullanılır. Commit öncesi bu araçların çalıştırılması zorunludur.
    ```bash
    # Python projesinin kök dizininde
    black .
    isort .
    ```
-   **C#**: `.editorconfig` dosyası kullanılarak kodlama stili ve formatlama kuralları belirlenir. Visual Studio Code Cleanup özelliği bu kurallara göre kodu biçimlendirmek için kullanılmalıdır.

### Linting
-   **Python**: `ruff` statik kod analiz aracı kullanılır. Hatalar ve uyarılar CI/CD sürecinde kontrol edilir.
    ```bash
    # Python projesinin kök dizininde
    ruff check .
    ```
-   **C#**: Visual Studio'nun yerleşik kod analiz araçları ve Roslyn analizörleri kullanılır. `.editorconfig` üzerinden kurallar yapılandırılır.

### `.editorconfig` Örneği (`src/desktop-app/.editorconfig`)
```editorconfig
# top-most EditorConfig file
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.cs]
csharp_new_line_before_open_brace = all
csharp_new_line_before_else = true
csharp_new_line_before_catch = true
csharp_new_line_before_finally = true
csharp_new_line_before_members_in_object_initializers = true
csharp_new_line_before_members_in_anonymous_types = true
csharp_space_after_cast = false
csharp_space_before_colon_in_base_type_list = true
csharp_space_after_colon_in_base_type_list = true
csharp_space_before_comma = false
csharp_space_after_comma = true
csharp_space_before_dot = false
csharp_space_after_dot = false
csharp_space_before_semicolon = false
csharp_space_after_semicolon_in_for_statement = true
csharp_space_before_semicolon_in_for_statement = false
csharp_preserve_single_line_blocks = true
csharp_preserve_single_line_statements = true
csharp_indent_switch_case = true
csharp_prefer_braces = true
csharp_using_directive_placement = outside_namespace

dotnet_sort_system_directives_first = true

# IDE Code Style
dotnet_style_qualification_for_field = false:suggestion
dotnet_style_qualification_for_property = false:suggestion
dotnet_style_qualification_for_method = false:suggestion
dotnet_style_qualification_for_event = false:suggestion

csharp_style_var_for_built_in_types = false:suggestion
csharp_style_var_when_type_is_apparent = true:suggestion
csharp_style_var_elsewhere = false:suggestion

csharp_style_pattern_matching_over_as_with_null_check = true:suggestion
csharp_style_prefer_compound_assignment = true:suggestion
```

## Bağımlılık Yönetimi
-   **Python**: `requirements.txt` dosyası kullanılır. Yeni bir bağımlılık eklendiğinde veya mevcut bir bağımlılık güncellendiğinde bu dosya manuel olarak güncellenmelidir.
    ```bash
    # Yeni paketleri yükledikten sonra
    pip freeze > requirements.txt
    ```
-   **C#**: `csproj` dosyasındaki `PackageReference` öğeleri kullanılır. NuGet paketleri `dotnet add package` komutuyla yönetilir.

## CI/CD Entegrasyonu
Proje, GitHub Actions kullanılarak CI/CD süreçleriyle entegre edilecektir. Her commit veya pull request, otomatik olarak build, lint ve test adımlarını tetikleyecektir.

### Temel CI/CD Adımları
1.  **Kod Kontrolü**: Linting ve formatlama kontrolleri.
2.  **Bağımlılık Yükleme**: Proje bağımlılıklarını yükleme.
3.  **Build**: C# ve Python projelerini derleme.
4.  **Test**: Birim ve entegrasyon testlerini çalıştırma.
5.  **Kod Kapsamı**: Test kapsamını ölçme ve raporlama.
6.  **Güvenlik Taraması**: Statik kod analizi ve bağımlılık güvenlik taramaları (opsiyonel).
7.  **Dağıtım**: Başarılı build ve testlerden sonra üretim ortamına otomatik dağıtım (daha sonra).

## Geliştirme Araçları
-   **Visual Studio Code Uzantıları**: C# (Microsoft), Python (Microsoft), Docker, GitLens.
-   **Docker Compose**: Yerel geliştirme ortamını tek bir komutla başlatmak için.
    ```bash
    docker-compose up --build
    ```

## Hata Yönetimi ve Loglama
Proje genelinde tutarlı bir hata yönetimi ve loglama stratejisi uygulanır. Geliştirme sırasında hatalar okunabilir ve izlenebilir olmalıdır.
-   **Python**: `structlog` ile yapılandırılmış loglama.
-   **C#**: `Serilog` ile yapılandırılmış loglama.

## Dökümantasyon
Her yeni modül, servis veya önemli özellik için Türkçe olarak dökümantasyon oluşturulması zorunludur. Dökümantasyon, `docs/` klasörü altında ilgili alt dizinlerde saklanmalıdır.

---

## Tamamlanma Kontrol Listesi (Geliştirici İçin)
-   [ ] `black` ve `isort` her Python değişikliğinden sonra çalıştırıldı mı?
-   [ ] `.editorconfig` kurallarına C# kodu uyuyor mu?
-   [ ] Yeni bağımlılıklar `requirements.txt` veya `csproj`'a eklendi mi?
-   [ ] Tüm yeni kodlar için birim testleri yazıldı mı?
-   [ ] Yeni özellikler için entegrasyon testleri yazıldı mı?
-   [ ] Yeni modüller veya servisler için dökümantasyon oluşturuldu mu?
-   [ ] Commit mesajları anlamlı ve açıklayıcı mı?
-   [ ] Tüm loglama çağrıları `LoggerService` veya `structlog` ile tutarlı mı?
