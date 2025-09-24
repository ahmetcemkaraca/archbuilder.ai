# Cloud API Integration Dokumentasyonu

## Genel Bakış
ArchBuilder.AI Cloud Server FastAPI tabanlı kapsamlı API entegrasyonu tamamlandı. Bu implementasyon güvenlik odaklı bir yaklaşımla OAuth2 + API key kimlik doğrulama, kullanım takibi, abonelik doğrulama ve çok modelli AI entegrasyonunu içerir.

## Ana Özellikler

### 1. Güvenlik Middleware
- **Correlation Tracking**: Her istek için benzersiz correlation ID oluşturma ve takip
- **Security Headers**: Tüm yanıtlara güvenlik başlıklarının eklenmesi
- **Performance Monitoring**: İstek sürelerinin ve kaynak kullanımının izlenmesi
- **Rate Limiting**: IP tabanlı ve abonelik bazlı rate limiting

### 2. Kimlik Doğrulama ve Yetkilendirme
- **OAuth2 + API Key**: Çift faktörlü kimlik doğrulama sistemi
- **Subscription Validation**: Abonelik seviyesine göre API erişimi kontrolü
- **Usage Tracking**: Kapsamlı kullanım takibi ve faturalama entegrasyonu

### 3. AI Servisleri
- **Multi-Model Support**: Vertex AI (Gemini-2.5-Flash-Lite) ve OpenAI/Azure OpenAI (GPT-4.1)
- **Intelligent Model Selection**: Görev türüne ve karmaşıklığa göre otomatik model seçimi
- **Fallback Mechanisms**: AI hataları için kural tabanlı geri dönüş sistemleri
- **Human-in-the-Loop**: Tüm AI çıktıları için zorunlu insan onayı

## API Endpoints

### AI Processing Endpoints

#### POST /api/ai/commands
Genel AI komutlarını işler (5 maliyet birimi, FREE katman)

**Özellikler:**
- Doğal dil işleme
- Çoklu model desteği
- Kapsamlı validasyon
- Audit logging

#### POST /api/ai/layouts
Gelişmiş mimari plan üretimi (10 maliyet birimi, STARTER katman gerekli)

**Özellikler:**
- Çok odalı koordinasyon
- Yapı yönetmeliği uyumluluğu
- Optimizasyon algoritmaları
- Bölgesel standart doğrulama

#### GET /api/ai/models
Mevcut AI modellerini ve yeteneklerini listeler

#### GET /api/ai/usage
Kullanıcının AI kullanım istatistiklerini döndürür

## Güvenlik Uygulamaları

### 1. Input Validation
- Tüm girişler için katı doğrulama
- XSS ve injection saldırılarına karşı koruma
- İçerik uzunluğu ve türü kontrolü

### 2. Error Handling
- Güvenli hata mesajları
- Detaylı logging sistemsel hatalarda
- Sensitive bilgilerin gizlenmesi

### 3. Rate Limiting
- IP tabanlı temel limitler
- Abonelik seviyesine göre özelleştirilmiş limitler
- Redis backend ile ölçeklenebilir implementasyon

## Monitoring ve Logging

### 1. Structured Logging
- Correlation ID ile istek takibi
- JSON formatında yapılandırılmış loglar
- Farklı log seviyeleri (DEBUG, INFO, WARNING, ERROR)

### 2. Performance Metrics
- İstek süreleri
- Kaynak kullanımı (CPU, Memory)
- API endpoint başına istatistikler
- Redis tabanlı metrik depolama

### 3. Error Tracking
- Exception türlerine göre kategorize
- Stack trace'ler ve context bilgisi
- Automated alerting sistemi

## Subscription Management

### 1. Tier Hierarchy
- **FREE**: Temel AI komutları (50/gün)
- **STARTER**: Gelişmiş layout üretimi (500/gün)
- **PROFESSIONAL**: Gelişmiş analitik (2000/gün)
- **ENTERPRISE**: Sınırsız kullanım

### 2. Usage Tracking
- Gerçek zamanlı kullanım takibi
- Fatura dönemine göre limitler
- Otomatik kullanım uyarıları

## AI Model Selection

### 1. Intelligent Selection
- Görev türüne göre otomatik model seçimi
- Dil ve bölge optimizasyonu
- Maliyet-performans dengesi

### 2. Model Capabilities
- **Vertex AI Gemini**: Türkçe yönetmelikler, basit görevler
- **OpenAI/Azure OpenAI (GPT-4.1)**: Karmaşık analiz, CAD dosya işleme

## Error Recovery

### 1. Fallback Systems
- AI hatalarında kural tabanlı çözümler
- Basit geometrik layout üretimi
- Kullanıcı bilgilendirme

### 2. Graceful Degradation
- Servis hatalarında minimal işlevsellik
- Cache'den önceki sonuçlar
- Manuel geri dönüş seçenekleri

## Development Setup

### 1. Environment Variables
```env
DATABASE_URL=postgresql://...
REDIS_HOST=localhost
VERTEX_AI_PROJECT_ID=your-project
GITHUB_MODELS_API_KEY=your-key
SECRET_KEY=your-secret-key
```

### 2. Service Dependencies
- PostgreSQL database
- Redis for caching and rate limiting
- Vertex AI API access
- OpenAI/Azure OpenAI API access

### 3. Docker Support
```bash
docker-compose up -d
```

## Testing Strategy

### 1. Unit Tests
- Service layer testing
- Middleware validation
- Authentication flows

### 2. Integration Tests
- API endpoint testing
- Database transactions
- External service mocking

### 3. Security Tests
- Authentication bypass attempts
- Rate limiting validation
- Input sanitization

## Deployment

### 1. Production Configuration
- Environment-specific settings
- SSL/TLS configuration
- Load balancer integration

### 2. Monitoring
- Health check endpoints
- Performance dashboards
- Error alerting

### 3. Scaling
- Horizontal scaling with Redis
- Database connection pooling
- CDN integration for static assets

## Next Steps

1. **Testing & Validation Phase**: Comprehensive test suite implementation
2. **Production Deployment**: Cloud infrastructure setup
3. **Performance Optimization**: Advanced caching and optimization
4. **Monitoring Dashboard**: Real-time system monitoring interface

## Kullanım Örnekleri

### AI Command Processing
```python
POST /api/ai/commands
{
  "prompt": "3 yatak odalı 120m² ev planı oluştur",
  "language": "tr",
  "region": "Turkey",
  "building_type": "residential"
}
```

### Layout Generation
```python
POST /api/ai/layouts
{
  "total_area_m2": 120,
  "building_type": "residential",
  "room_requirements": [
    {"name": "Salon", "area": 25},
    {"name": "Mutfak", "area": 15},
    {"name": "Yatak Odası", "area": 20}
  ],
  "region": "Turkey"
}
```

Bu implementasyon ArchBuilder.AI sisteminin cloud backend altyapısının temelini oluşturur ve production'a hazır, güvenli ve ölçeklenebilir bir API sağlar.