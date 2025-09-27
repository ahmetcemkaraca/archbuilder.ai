# 🤖 Otomatik Commit Suggestion Sistemi

Bu sistem, Gemini Code Assist ve diğer AI botlarının önerilerini otomatik olarak commit'lere dönüştürür.

## 🎯 Özellikler

### 1. **Automated Security Analysis** 
- **Bandit**: Python security linter
- **Safety**: Dependency vulnerability scanner  
- **Semgrep**: Static analysis for security patterns
- **Custom Patterns**: ArchBuilder.AI-specific security checks

### 2. **Auto-Fix Capabilities**
```yaml
- Missing file validation in upload endpoints
- Security import additions
- Common vulnerability patterns
- Hardcoded secret detection
```

### 3. **GitHub Integration**
- **Issues**: Otomatik security issue oluşturma
- **PR Comments**: Security analysis sonuçları
- **Artifacts**: Detaylı raporları saklama
- **Auto-Commit**: Düzeltmeleri otomatik commit etme

## 🚀 Kullanım

### Manuel Tetikleme
```bash
# GitHub'da Actions sekmesine git
# "Automated Security Suggestions" workflow'unu seç
# "Run workflow" butonuna tıkla
# Scan type seç: full, quick, critical
```

### Otomatik Tetikleme
- **Push to develop/main**: Her push'ta çalışır
- **Pull Request**: PR'larda security analysis
- **Weekly Scan**: Pazar günleri 02:00 UTC
- **Commit Messages**: Gemini bot önerilerini algılar

### Custom Security Patterns
```python
patterns = {
    "missing_file_validation": {
        "pattern": r"UploadFile.*File\(",
        "check": r"validate_upload_file|validate_file_type", 
        "message": "File upload endpoint missing security validation",
        "severity": "HIGH"
    }
}
```

## 📊 Workflow Sonuçları

### Issue Creation
- Security issue otomatik oluşturulur
- Severity'ye göre label'lar eklenir
- Detaylı bulguları markdown formatında sunar

### Auto-Fix Examples
```python
# BEFORE (Vulnerable)
@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    return {"status": "uploaded"}

# AFTER (Secure) - Otomatik eklendi
@router.post("/upload")  
async def upload(file: UploadFile = File(...)):
    # Enhanced security validation
    security_validator = get_enhanced_security()
    validation_result = security_validator.validate_upload_file(
        Path(file.filename), await file.read()
    )
    if not validation_result['is_valid']:
        raise HTTPException(400, "File validation failed")
```

## 🔧 Konfigürasyon

### Secrets (GitHub Repository Settings)
```bash
SEMGREP_APP_TOKEN=xxx  # Semgrep Cloud token (optional)
```

### Workflow Triggers
```yaml
on:
  push: [develop, main]
  pull_request: [develop, main] 
  schedule: '0 2 * * 0'  # Weekly
  workflow_dispatch:     # Manual
```

## 📈 Metrics & Reporting

### Security Report Format  
- **Summary by Severity**: CRITICAL, HIGH, MEDIUM, LOW
- **Detailed Findings**: File, line, code snippet
- **Auto-Fix Suggestions**: Actionable recommendations
- **Trend Analysis**: Weekly security posture

### Artifact Storage
- `security-report.md`: Human readable
- `custom-security-findings.json`: Machine readable  
- `bandit-report.json`: Bandit results
- `safety-report.json`: Dependency vulnerabilities
- `semgrep-report.json`: Static analysis results

## 🎯 Gemini Code Assist Integration

Bu sistem, Gemini'nin önerdiği gibi eksik `_validate_file_type` metodunu:

✅ **Implemented**: Enhanced security validator oluşturduk
✅ **Integrated**: Upload endpoint'lerine validation ekledik  
✅ **Automated**: GitHub Actions ile sürekli monitoring
✅ **Auto-Fixed**: Gelecekteki benzer sorunları otomatik çözer

### Sonraki Adımlar
1. **Test the workflow**: Manual trigger ile test et
2. **Monitor issues**: Oluşturulan security issue'ları incele
3. **Review auto-fixes**: Bot'un yaptığı değişiklikleri kontrol et
4. **Customize patterns**: Proje-specific security rules ekle

Bu sistem sayesinde artık Gemini Code Assist ve diğer AI botlarının önerileri otomatik olarak kod değişikliklerine dönüşecek! 🚀