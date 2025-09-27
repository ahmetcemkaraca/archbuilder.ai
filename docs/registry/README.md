# Registry Rehberi

Registry; modül/export kimliklerini, API sözleşmelerini ve veri şemalarını tek yerde tutarak tutarlılığı sağlar.

## Dosyalar

### `identifiers.json`
Modüllerin export ettiği fonksiyon, sınıf ve değişkenleri listeler.

```json
{
  "modules": [
    {
      "name": "app.services.rag_service",
      "exports": ["RAGService"]
    },
    {
      "name": "app.routers.v1.rag",
      "exports": ["router", "RAGQueryRequest", "RAGQueryResponse"]
    },
    {
      "name": "app.database.models.user",
      "exports": ["User"]
    }
  ]
}
```

### `endpoints.json`
HTTP API endpoint'lerinin sözleşmelerini tanımlar.

```json
{
  "endpoints": [
    {
      "method": "POST",
      "path": "/v1/ai/commands",
      "auth": "api_key|jwt",
      "request_schema_ref": "AICommandCreateRequest",
      "response_schema_ref": "AICommandResponse",
      "headers": {
        "request": ["X-Correlation-ID?"],
        "response": ["X-Correlation-ID", "X-Request-ID"]
      }
    },
    {
      "method": "WebSocket",
      "path": "/v1/ws",
      "auth": "none",
      "request_schema_ref": null,
      "response_schema_ref": "WebSocketMessage",
      "description": "WebSocket endpoint for real-time communication"
    }
  ]
}
```

### `schemas.json`
Veri modellerini ve veritabanı tablolarını tanımlar.

```json
{
  "schemas": [
    {
      "name": "DB.users",
      "type": "table",
      "columns": {
        "id": {"type": "string", "length": 36, "primary_key": true},
        "email": {"type": "string", "length": 256, "unique": true},
        "role": {"type": "string", "length": 32},
        "created_at": {"type": "datetime"}
      },
      "indexes": [
        {"name": "ix_users_email", "columns": ["email"]}
      ]
    },
    {
      "name": "AICommandResponse",
      "type": "object",
      "properties": {
        "success": {"type": "boolean"},
        "data": {"type": "object"}
      },
      "required": ["success", "data"]
    }
  ]
}
```

## Kurallar

### Registry Güncelleme Kuralları
1. **Public API/model/export değişimi** → ilgili JSON dosyası güncellenecek ve test eklenecek
2. **Branch merge öncesi** CI `validate-registry.ps1` ile doğrular
3. **Yeni endpoint ekleme** → `endpoints.json`a ekle, header requirements belirt
4. **Yeni veritabanı tablosu** → `schemas.json`a ekle, foreign key'leri belirt
5. **Yeni modül export** → `identifiers.json`a ekle

### Validation Süreci
```bash
# Registry doğrulama
pwsh -File scripts/validate-registry.ps1

# Registry contract testleri
cd src/cloud-server
python -m pytest app/tests/test_registry_contracts.py -v
```

### Naming Conventions
- **Database Tables**: `DB.table_name` formatında
- **API Schemas**: `RequestType` / `ResponseType` formatında  
- **Modules**: Tam Python modül yolu
- **Endpoints**: HTTP method + tam path

## Sık Yapılan Hatalar

### 1. Export Ekleme Unutma
❌ **Yanlış**: Yeni bir service sınıfı yaratıp `identifiers.json`ı güncellememek
```python
# app/services/new_service.py
class NewService:
    def process(self): pass
```

✅ **Doğru**: `identifiers.json`a entry eklemek
```json
{
  "name": "app.services.new_service",
  "exports": ["NewService"]
}
```

### 2. Endpoint Header Eksikliği
❌ **Yanlış**: Header requirements belirtmemek
```json
{
  "method": "POST",
  "path": "/v1/api/endpoint",
  "auth": "api_key"
}
```

✅ **Doğru**: Correlation ID header'ları belirtmek
```json
{
  "method": "POST", 
  "path": "/v1/api/endpoint",
  "auth": "api_key",
  "headers": {
    "request": ["X-Correlation-ID?"],
    "response": ["X-Correlation-ID", "X-Request-ID"]
  }
}
```

### 3. Database Schema Eksikliği
❌ **Yanlış**: Yeni tablo oluşturup schema'da belirtmemek

✅ **Doğru**: Tüm tabloları `DB.table_name` formatında belirtmek
```json
{
  "name": "DB.projects",
  "type": "table",
  "columns": {
    "id": {"type": "string", "length": 36, "primary_key": true},
    "owner_id": {"type": "string", "length": 36, "fk": "users.id"}
  }
}
```

### 4. Endpoint Versiyon Değişikliği
❌ **Yanlış**: Endpoint değiştirip contract test yazmamak

✅ **Doğru**: Test ekleme ve backward compatibility kontrolü
```python
def test_endpoints_document_headers():
    # Contract test örneği
    paths = {e["path"]: e for e in endpoints["endpoints"]}
    assert "/v1/rag/query" in paths
    assert "headers" in paths["/v1/rag/query"]
```

## Best Practices

### Registry-First Development
1. **Önce Registry Güncelle**: Kod yazmadan önce registry dosyalarını güncelle
2. **Test Yaz**: Registry değişikliği için test ekle
3. **Kodu Yaz**: Registry'ye uygun kodu implementasyonu
4. **Validate Et**: Registry validation script'ini çalıştır

### Correlation ID Tracking
Tüm endpoint'ler correlation ID desteği sağlamalı:
```json
{
  "headers": {
    "request": ["X-Correlation-ID?"],  // Optional in request
    "response": ["X-Correlation-ID", "X-Request-ID"]  // Required in response
  }
}
```

### Schema Evolution
- **Breaking Changes**: MAJOR version bump gerektirir
- **Additive Changes**: MINOR version bump
- **Bug Fixes**: PATCH version bump

### Database Schema Management
- **Foreign Key'ler**: `"fk": "parent_table.column"` formatında belirt
- **Index'ler**: Performance için kritik column'ları index'le
- **Nullable Fields**: `"nullable": true` ile açıkça belirt

## Troubleshooting

### Registry Validation Hataları
```bash
# Hata kodu 2: Registry dosyaları eksik
ls docs/registry/  # identifiers.json, endpoints.json, schemas.json olmalı

# Hata kodu 3: JSON geçersiz  
cat docs/registry/identifiers.json | python -m json.tool

# Hata kodu 4: API değişimi var ama endpoints.json boş
git status  # API klasörlerinde değişiklik var mı kontrol et
```

### Test Hataları
```bash
# Contract test başarısız
python -m pytest app/tests/test_registry_contracts.py -v -s

# Missing schema hatası
grep -r "class.*Base" src/  # Yeni model var mı kontrol et
```

## Development Workflow

### Yeni Feature Ekleme
1. **Registry Güncelle**: İlgili JSON dosyalarını güncelle
2. **Test Yaz**: Registry contract testlerini güncelle  
3. **Implement**: Kod implementasyonunu yap
4. **Validate**: Registry validation + testleri çalıştır
5. **Commit**: Registry + kod değişikliklerini birlikte commit et

### Bug Fix Workflow
1. **Kontrol**: Registry değişikliği gerekiyor mu?
2. **Güncelle**: Gerekirse registry'yi güncelle
3. **Fix**: Bug'ı düzelt
4. **Test**: Hem unit hem registry testlerini çalıştır
5. **Validate**: Registry validation geç

Bu rehber sayesinde registry sistemini doğru kullanarak tutarlı ve sürdürülebilir API geliştirme sürdürülebilir.
