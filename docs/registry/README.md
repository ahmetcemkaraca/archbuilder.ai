# Registry Rehberi

Registry; modül/export kimliklerini, API sözleşmelerini ve veri şemalarını tek yerde tutarak tutarlılığı sağlar.

## Dosyalar
- `identifiers.json`
```json
{
  "modules": [
    {
      "name": "user.service",
      "exports": ["createUser", "getUserById"],
      "variables": ["USER_CACHE_TTL"],
      "configKeys": ["USER_SERVICE_URL"]
    }
  ]
}
```
- `endpoints.json`
```json
{
  "endpoints": [
    {
      "name": "CreateUser",
      "method": "POST",
      "path": "/api/users",
      "inputSchema": "CreateUserRequest@v1",
      "outputSchema": "User@v1",
      "auth": "required"
    }
  ]
}
```
- `schemas.json`
```json
{
  "schemas": [
    { "name": "User@v1", "fields": ["id","email","name"] }
  ]
}
```

## Kurallar
- Public API/model/export değişimi → ilgili JSON güncellenecek ve test eklenecek.
- Branch merge öncesi CI `validate-registry.ps1` ile doğrular.

## Sık Yapılan Hatalar
- Export ekleyip `identifiers.json`ı unutmak → CI uyarısı alırsınız.
- Endpoint versiyon değiştirip contract test yazmamak → regresyon riski.
