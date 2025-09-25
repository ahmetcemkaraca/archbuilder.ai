# RAGFlow Integration Documentation

Bu dokümantasyon ArchBuilder.AI'nin RAGFlow entegrasyonunu detaylandırır.

## Genel Bakış

RAGFlow, ArchBuilder.AI'nin doküman işleme ve bilgi alma (RAG) altyapısının temel bileşenidir. Bu entegrasyon, mimari dokümanların yüklenmesi, işlenmesi ve sorgulanması için gerekli tüm işlevselliği sağlar.

## Mimari

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Desktop App   │    │  Cloud Server    │    │   RAGFlow API   │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ Revit Plugin│ │◄──►│ │ RAG Service  │ │◄──►│ │ Dataset API │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ File Upload │ │◄──►│ │ Upload Parse │ │◄──►│ │ Document API│ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ AI Queries  │ │◄──►│ │ Query Engine │ │◄──►│ │ Retrieval   │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## API Endpoints

### 1. Dataset Management

#### Dataset Oluşturma
```http
POST /v1/documents/rag/ensure-dataset
Content-Type: application/json
X-API-Key: your-api-key

{
  "owner_id": "user_123",
  "project_id": "project_123", 
  "preferred_name": "project-dataset"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "dataset_id": "dataset_456",
    "name": "project-dataset",
    "created_at": "2025-01-10T10:00:00Z"
  }
}
```

### 2. Document Upload and Processing

#### Senkron Upload ve Parse
```http
POST /v1/documents/rag/{dataset_id}/upload-parse
Content-Type: multipart/form-data
X-API-Key: your-api-key

file: [binary data]
```

**Response:**
```json
{
  "success": true,
  "data": {
    "document_ids": ["doc_1", "doc_2"],
    "uploaded_count": 2,
    "status": "processed"
  }
}
```

#### Asenkron Upload ve Parse
```http
POST /v1/documents/rag/{dataset_id}/upload-parse/async
Content-Type: multipart/form-data
X-API-Key: your-api-key

file: [binary data]
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "parse_job_789",
    "status": "processing",
    "estimated_completion": "2025-01-10T10:05:00Z"
  }
}
```

#### Job Status Kontrolü
```http
GET /v1/documents/rag/jobs/{job_id}
X-API-Key: your-api-key
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "parse_job_789",
    "status": "completed",
    "progress": 100,
    "result": {
      "processed_documents": 5,
      "created_chunks": 25,
      "processing_time_ms": 5000
    }
  }
}
```

### 3. Query and Search

#### Basit RAG Query
```http
POST /v1/rag/query
Content-Type: application/json
X-API-Key: your-api-key

{
  "query": "building codes requirements",
  "dataset_ids": ["dataset_123"],
  "max_results": 5,
  "similarity_threshold": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "content": "Building codes require minimum room heights of 2.4m...",
        "score": 0.95,
        "document_id": "doc_1",
        "chunk_id": "chunk_1",
        "source": "building_codes.pdf"
      }
    ],
    "total_results": 1,
    "query_time_ms": 150
  }
}
```

#### Hybrid Search
```http
POST /v1/rag/hybrid-search
Content-Type: application/json
X-API-Key: your-api-key

{
  "query": "architectural design principles",
  "dataset_ids": ["dataset_123"],
  "max_results": 10,
  "keyword_boost": 0.4,
  "dense_boost": 0.6,
  "filters": {
    "document_types": ["pdf"],
    "languages": ["en", "tr"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "content": "Hybrid search result combining keyword and vector search",
        "score": 0.92,
        "document_id": "doc_3",
        "chunk_id": "chunk_3",
        "source": "hybrid_doc.pdf",
        "keyword_score": 0.8,
        "vector_score": 0.95
      }
    ],
    "total_results": 1,
    "search_time_ms": 200
  }
}
```

### 4. Index Management

#### Index Oluşturma
```http
POST /v1/rag/index/build
Content-Type: application/json
X-API-Key: your-api-key

{
  "dataset_id": "dataset_123",
  "rebuild": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "index_id": "index_456",
    "status": "building",
    "estimated_completion": "2025-01-10T10:10:00Z"
  }
}
```

## RAGFlow Client

### Python Client Kullanımı

```python
from app.ai.ragflow.client import RAGFlowClient

async def example_usage():
    async with RAGFlowClient(
        base_url="http://ragflow:8000",
        api_key="your-api-key"
    ) as client:
        
        # Dataset oluştur
        dataset = await client.create_dataset(
            name="architectural-docs",
            correlation_id="corr_123"
        )
        
        # Doküman yükle
        with open("building_codes.pdf", "rb") as f:
            files = [f.read()]
            filenames = ["building_codes.pdf"]
            
            result = await client.upload_documents(
                dataset_id=dataset["data"]["id"],
                files=files,
                filenames=filenames,
                correlation_id="corr_123"
            )
        
        # Dokümanları parse et
        parse_result = await client.parse_documents(
            dataset_id=dataset["data"]["id"],
            document_ids=result["data"]["document_ids"],
            options={"chunk_size": 1000, "overlap": 200},
            correlation_id="corr_123"
        )
        
        # Sorgu yap
        search_result = await client.retrieval(
            question="What are the minimum room height requirements?",
            dataset_ids=[dataset["data"]["id"]],
            top_k=5,
            vector_similarity_weight=0.7,
            correlation_id="corr_123"
        )
        
        return search_result
```

### C# Client Kullanımı

```csharp
public class RAGFlowApiClient
{
    private readonly HttpClient _httpClient;
    private readonly string _apiKey;
    
    public async Task<DatasetResponse> CreateDatasetAsync(string name, string correlationId)
    {
        var request = new
        {
            name = name
        };
        
        var json = JsonSerializer.Serialize(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        content.Headers.Add("X-Correlation-ID", correlationId);
        
        var response = await _httpClient.PostAsync("/api/v1/datasets", content);
        response.EnsureSuccessStatusCode();
        
        var responseJson = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<DatasetResponse>(responseJson);
    }
    
    public async Task<RetrievalResponse> QueryAsync(
        string question, 
        string[] datasetIds, 
        int topK = 5,
        string correlationId = null)
    {
        var request = new
        {
            question = question,
            dataset_ids = datasetIds,
            top_k = topK
        };
        
        var json = JsonSerializer.Serialize(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        if (!string.IsNullOrEmpty(correlationId))
        {
            content.Headers.Add("X-Correlation-ID", correlationId);
        }
        
        var response = await _httpClient.PostAsync("/api/v1/retrieval", content);
        response.EnsureSuccessStatusCode();
        
        var responseJson = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<RetrievalResponse>(responseJson);
    }
}
```

## Hata Yönetimi

### Yaygın Hata Kodları

| HTTP Status | Hata Kodu | Açıklama | Çözüm |
|-------------|-----------|----------|-------|
| 400 | INVALID_REQUEST | Geçersiz request parametreleri | Request formatını kontrol edin |
| 401 | UNAUTHORIZED | Geçersiz API key | API key'i kontrol edin |
| 404 | DATASET_NOT_FOUND | Dataset bulunamadı | Dataset ID'sini kontrol edin |
| 429 | RATE_LIMIT_EXCEEDED | Rate limit aşıldı | İstekleri azaltın |
| 500 | INTERNAL_ERROR | RAGFlow sunucu hatası | Tekrar deneyin |
| 502 | UPSTREAM_ERROR | RAGFlow bağlantı hatası | Bağlantıyı kontrol edin |

### Retry Mekanizması

```python
async def retry_with_backoff(func, max_retries=3, base_delay=1.0):
    """Exponential backoff ile retry mekanizması"""
    for attempt in range(max_retries):
        try:
            return await func()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 503) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                continue
            raise
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                continue
            raise
```

## Performans Optimizasyonu

### 1. Chunking Stratejileri

```python
# Optimal chunking parametreleri
chunking_config = {
    "max_chars": 1000,      # Maksimum karakter sayısı
    "overlap": 200,         # Chunk'lar arası overlap
    "min_chars": 100,       # Minimum karakter sayısı
    "split_by": "sentence"  # Cümle bazında bölme
}
```

### 2. Caching Stratejileri

```python
# Redis cache kullanımı
import redis
import json

class RAGCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 saat
    
    async def get_cached_result(self, query_hash):
        cached = await self.redis.get(f"rag:query:{query_hash}")
        if cached:
            return json.loads(cached)
        return None
    
    async def cache_result(self, query_hash, result):
        await self.redis.setex(
            f"rag:query:{query_hash}",
            self.ttl,
            json.dumps(result)
        )
```

### 3. Batch Processing

```python
# Toplu işlem için batch API
async def batch_upload_documents(dataset_id, documents):
    """Çoklu doküman yükleme"""
    batch_size = 10
    results = []
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        result = await client.upload_documents(
            dataset_id=dataset_id,
            files=[doc.content for doc in batch],
            filenames=[doc.filename for doc in batch]
        )
        results.append(result)
    
    return results
```

## Monitoring ve Logging

### Metrikler

```python
# Prometheus metrikleri
from prometheus_client import Counter, Histogram, Gauge

# RAG query metrikleri
rag_queries_total = Counter('rag_queries_total', 'Total RAG queries', ['status'])
rag_query_duration = Histogram('rag_query_duration_seconds', 'RAG query duration')
rag_active_connections = Gauge('rag_active_connections', 'Active RAG connections')

# Kullanım
rag_queries_total.labels(status='success').inc()
rag_query_duration.observe(duration)
```

### Logging

```python
import structlog

logger = structlog.get_logger(__name__)

async def rag_query_with_logging(query, dataset_ids, correlation_id):
    logger.info(
        "RAG query started",
        query=query[:100],  # İlk 100 karakter
        dataset_ids=dataset_ids,
        correlation_id=correlation_id
    )
    
    try:
        result = await client.retrieval(
            question=query,
            dataset_ids=dataset_ids,
            correlation_id=correlation_id
        )
        
        logger.info(
            "RAG query completed",
            correlation_id=correlation_id,
            result_count=len(result["data"]["results"]),
            query_time_ms=result["data"].get("query_time_ms", 0)
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "RAG query failed",
            correlation_id=correlation_id,
            error=str(e),
            exc_info=True
        )
        raise
```

## Test Stratejileri

### 1. Unit Tests

```python
# RAGFlow client unit testleri
@pytest.mark.asyncio
async def test_ragflow_client_creation():
    client = RAGFlowClient(
        base_url="http://test-ragflow",
        api_key="test-key"
    )
    assert client._base_url == "http://test-ragflow"
    assert client._api_key == "test-key"
```

### 2. Integration Tests

```python
# RAGFlow entegrasyon testleri
@respx.mock
async def test_ragflow_integration():
    # Mock RAGFlow API
    respx.post("http://ragflow:8000/api/v1/retrieval").mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "data": {"results": [], "total_results": 0}
        })
    )
    
    async with RAGFlowClient("http://ragflow:8000") as client:
        result = await client.retrieval("test query")
        assert result["success"] is True
```

### 3. Load Tests

```python
# RAGFlow load testleri
async def test_ragflow_load():
    """Eşzamanlı RAG query testi"""
    tasks = []
    for i in range(100):  # 100 eşzamanlı query
        task = client.retrieval(f"load test query {i}")
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Başarı oranı %95'ten yüksek olmalı
    success_rate = sum(1 for r in results if not isinstance(r, Exception)) / len(results)
    assert success_rate >= 0.95
```

## Güvenlik

### 1. API Key Yönetimi

```python
# API key rotasyonu
class APIKeyManager:
    def __init__(self):
        self.current_key = None
        self.backup_key = None
    
    async def rotate_api_key(self):
        """API key rotasyonu"""
        if self.backup_key:
            self.current_key = self.backup_key
            self.backup_key = await self.generate_new_key()
        else:
            self.current_key = await self.generate_new_key()
            self.backup_key = await self.generate_new_key()
```

### 2. Rate Limiting

```python
# Rate limiting implementasyonu
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/v1/rag/query")
@limiter.limit("10/minute")  # Dakikada 10 query
async def rag_query(request: Request, query_data: RAGQueryRequest):
    # RAG query implementation
    pass
```

### 3. Input Validation

```python
# RAG query input validation
from pydantic import BaseModel, validator

class RAGQueryRequest(BaseModel):
    query: str
    dataset_ids: List[str]
    max_results: int = 10
    
    @validator('query')
    def validate_query(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Query must be at least 3 characters')
        if len(v) > 1000:
            raise ValueError('Query too long')
        return v.strip()
    
    @validator('max_results')
    def validate_max_results(cls, v):
        if v < 1 or v > 100:
            raise ValueError('max_results must be between 1 and 100')
        return v
```

## Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  ragflow:
    image: infiniflow/ragflow:latest
    ports:
      - "8000:8000"
    environment:
      - RAGFLOW_API_KEY=your-api-key
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - postgres
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=ragflow
      - POSTGRES_USER=ragflow
      - POSTGRES_PASSWORD=ragflow
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ragflow
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ragflow
  template:
    metadata:
      labels:
        app: ragflow
    spec:
      containers:
      - name: ragflow
        image: infiniflow/ragflow:latest
        ports:
        - containerPort: 8000
        env:
        - name: RAGFLOW_API_KEY
          valueFrom:
            secretKeyRef:
              name: ragflow-secrets
              key: api-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

## Troubleshooting

### Yaygın Sorunlar

1. **Connection Timeout**
   ```bash
   # RAGFlow bağlantısını test et
   curl -X GET http://ragflow:8000/health
   ```

2. **API Key Hatası**
   ```bash
   # API key'i kontrol et
   curl -H "Authorization: Bearer your-api-key" \
        http://ragflow:8000/api/v1/datasets
   ```

3. **Memory Issues**
   ```bash
   # RAGFlow memory kullanımını kontrol et
   docker stats ragflow-container
   ```

### Debug Logging

```python
# Debug logging aktifleştir
import logging
logging.getLogger("app.ai.ragflow").setLevel(logging.DEBUG)

# RAGFlow client debug
client = RAGFlowClient(
    base_url="http://ragflow:8000",
    api_key="your-api-key",
    timeout_seconds=60
)
```

## Changelog

### v1.0.0 (2025-01-10)
- İlk RAGFlow entegrasyonu
- Dataset yönetimi
- Doküman yükleme ve parse
- RAG query ve hybrid search
- Temel hata yönetimi

### v1.1.0 (2025-01-15)
- Performans optimizasyonları
- Caching implementasyonu
- Batch processing
- Monitoring ve logging

### v1.2.0 (2025-01-20)
- Advanced filtering
- Pagination support
- Rate limiting
- Security improvements
