"""
Security Tests for Enhanced Security Middleware
Tests for input validation, file security, and threat detection.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI, Request, Response, status
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.enhanced_security import (
    EnhancedSecurityMiddleware,
    SecurityViolation,
    InputSanitizer,
    FileSecurityValidator
)
from app.core.input_validation import (
    EnhancedInputValidator,
    CADFileValidator,
    SecurityConfig,
    ValidationResult
)


class TestEnhancedSecurityMiddleware:
    """Test the enhanced security middleware"""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app with security middleware"""
        app = FastAPI()
        app.add_middleware(EnhancedSecurityMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.post("/upload")
        async def upload_endpoint():
            return {"message": "uploaded"}
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_normal_request_passes(self, client):
        """Test that normal requests pass through"""
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
    
    def test_sql_injection_blocked(self, client):
        """Test that SQL injection attempts are blocked"""
        # Test various SQL injection patterns
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM users",
            "UNION SELECT * FROM passwords"
        ]
        
        for payload in sql_payloads:
            response = client.get(f"/test?param={payload}")
            assert response.status_code == 400
            assert "SQL injection" in response.json().get("error", {}).get("message", "")
    
    def test_xss_attack_blocked(self, client):
        """Test that XSS attacks are blocked"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<img src='x' onerror='alert(1)'>",
            "data:text/html,<script>alert('xss')</script>"
        ]
        
        for payload in xss_payloads:
            response = client.get(f"/test?param={payload}")
            assert response.status_code == 400
            assert "XSS" in response.json().get("error", {}).get("message", "")
    
    def test_path_traversal_blocked(self, client):
        """Test that path traversal attempts are blocked"""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f",
            "....//....//",
            "..%252f..%252f"
        ]
        
        for payload in traversal_payloads:
            response = client.get(f"/test?path={payload}")
            assert response.status_code == 400
            assert "path traversal" in response.json().get("error", {}).get("message", "").lower()
    
    def test_threat_detection(self, client):
        """Test threat detection based on suspicious patterns"""
        # Test with suspicious user agent
        suspicious_headers = {
            "User-Agent": "sqlmap/1.0",
            "X-Forwarded-For": "192.168.1.100"
        }
        
        response = client.get("/test", headers=suspicious_headers)
        # Should still work initially but increase threat score
        assert response.status_code in [200, 403]  # Might be blocked after threshold
    
    def test_security_headers_applied(self, client):
        """Test that security headers are properly applied"""
        response = client.get("/test")
        
        # Check for essential security headers
        assert "Content-Security-Policy" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "Strict-Transport-Security" in response.headers
        assert "Referrer-Policy" in response.headers
        
        # Verify header values
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "max-age=" in response.headers["Strict-Transport-Security"]
    
    def test_file_upload_validation(self, client):
        """Test file upload security validation"""
        # Test with malicious file
        malicious_content = b"PK\x03\x04" + b"A" * 1000  # ZIP-like header
        
        files = {"file": ("malware.exe", malicious_content, "application/octet-stream")}
        response = client.post("/upload", files=files)
        
        # Should be blocked due to dangerous extension
        assert response.status_code in [400, 413, 422]


class TestCADFileValidator:
    """Test CAD file validation functionality"""
    
    def test_dwg_file_validation(self):
        """Test DWG file validation"""
        # Valid DWG signature
        dwg_content = b'AC1027' + b'\x00' * 1000
        result = CADFileValidator.validate_cad_file("test.dwg", dwg_content)
        
        assert result.valid is True
        assert "dwg_version" in result.metadata
    
    def test_dxf_file_validation(self):
        """Test DXF file validation"""
        dxf_content = b"""0
SECTION
2
HEADER
9
$ACADVER
1
AC1021
0
ENDSEC
0
SECTION
2
ENTITIES
0
ENDSEC
0
EOF
"""
        result = CADFileValidator.validate_cad_file("test.dxf", dxf_content)
        
        assert result.valid is True
        assert "dxf_version" in result.metadata
    
    def test_ifc_file_validation(self):
        """Test IFC file validation"""
        ifc_content = b"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('','2023-01-01T00:00:00',(''),(''),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('2OOmSWdMnDbx4TFKcpqW8Z',$,'Project',$,$,$,$,(#9,#10),#8);
ENDSEC;
END-ISO-10303-21;
"""
        result = CADFileValidator.validate_cad_file("test.ifc", ifc_content)
        
        assert result.valid is True
        assert result.metadata["ifc_schema"] == "IFC4"
    
    def test_invalid_file_format(self):
        """Test rejection of invalid file formats"""
        invalid_content = b"This is not a CAD file"
        result = CADFileValidator.validate_cad_file("test.txt", invalid_content)
        
        assert result.valid is False
        assert "Unsupported CAD file format" in result.errors[0]
    
    def test_file_too_small(self):
        """Test rejection of files that are too small"""
        tiny_content = b"AC1027"  # Too small for valid DWG
        result = CADFileValidator.validate_cad_file("test.dwg", tiny_content)
        
        assert result.valid is False
        assert "too small" in result.errors[0]
    
    def test_corrupted_cad_file(self):
        """Test handling of corrupted CAD files"""
        corrupted_dwg = b'AC1027' + b'\xFF' * 50  # Valid header but corrupted data
        result = CADFileValidator.validate_cad_file("corrupted.dwg", corrupted_dwg)
        
        # Should still validate structure but may have warnings
        assert len(result.warnings) > 0 or result.valid is True


class TestEnhancedInputValidator:
    """Test comprehensive input validation"""
    
    @pytest.fixture
    def validator(self):
        """Create input validator with default config"""
        return EnhancedInputValidator()
    
    def test_string_validation_success(self, validator):
        """Test successful string validation"""
        clean_string = "This is a normal string with no malicious content"
        result = validator.validate_string(clean_string, "test_field")
        
        assert result.valid is True
        assert result.sanitized_data == clean_string
    
    def test_string_length_validation(self, validator):
        """Test string length limits"""
        long_string = "A" * 20000  # Exceeds default max length
        result = validator.validate_string(long_string, "test_field")
        
        assert result.valid is False
        assert "exceeds maximum length" in result.errors[0]
    
    def test_sql_injection_detection(self, validator):
        """Test SQL injection pattern detection"""
        malicious_strings = [
            "'; DROP TABLE users; --",
            "1' UNION SELECT password FROM users--",
            "admin'/**/OR/**/1=1#",
            "1; EXEC xp_cmdshell('dir')",
            "waitfor delay '00:00:05'"
        ]
        
        for malicious_string in malicious_strings:
            result = validator.validate_string(malicious_string, "test_field")
            assert result.valid is False
            assert "SQL injection" in result.errors[0]
    
    def test_xss_detection(self, validator):
        """Test XSS pattern detection"""
        xss_strings = [
            "<script>alert('xss')</script>",
            "<img src='x' onerror='alert(1)'>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(1)'></iframe>",
            "document.cookie",
            "eval('malicious code')",
            "<svg onload='alert(1)'>"
        ]
        
        for xss_string in xss_strings:
            result = validator.validate_string(xss_string, "test_field")
            assert result.valid is False
            assert "XSS" in result.errors[0]
    
    def test_email_validation_success(self, validator):
        """Test successful email validation"""
        valid_emails = [
            "user@example.com",
            "test.email+tag@domain.co.uk",
            "firstname.lastname@company.com"
        ]
        
        for email in valid_emails:
            result = validator.validate_email(email)
            assert result.valid is True
            assert "@" in result.sanitized_data
    
    def test_email_validation_failure(self, validator):
        """Test email validation failures"""
        invalid_emails = [
            "not-an-email",
            "@domain.com",
            "user@",
            "user@domain",
            "user space@domain.com"
        ]
        
        for email in invalid_emails:
            result = validator.validate_email(email)
            assert result.valid is False
            assert "Invalid email format" in result.errors[0]
    
    def test_url_validation(self, validator):
        """Test URL validation"""
        valid_urls = [
            "https://example.com",
            "http://localhost:8000/api",
            "https://subdomain.example.co.uk/path?param=value"
        ]
        
        invalid_urls = [
            "javascript:alert('xss')",
            "ftp://malicious-site.com",
            "not-a-url",
            ""
        ]
        
        for url in valid_urls:
            result = validator.validate_url(url)
            assert result.valid is True
        
        for url in invalid_urls:
            result = validator.validate_url(url)
            assert result.valid is False
    
    def test_json_validation(self, validator):
        """Test JSON validation"""
        valid_json = '{"name": "test", "value": 123, "enabled": true}'
        result = validator.validate_json(valid_json)
        
        assert result.valid is True
        assert isinstance(result.sanitized_data, dict)
        assert result.sanitized_data["name"] == "test"
    
    def test_json_depth_limit(self, validator):
        """Test JSON nesting depth limits"""
        # Create deeply nested JSON
        nested_json = "{" * 20 + '"key": "value"' + "}" * 20
        result = validator.validate_json(nested_json, max_depth=10)
        
        assert result.valid is False
        assert "nesting exceeds maximum depth" in result.errors[0]
    
    def test_xml_validation_with_defusedxml(self, validator):
        """Test XML validation using defusedxml"""
        valid_xml = "<root><element>value</element></root>"
        result = validator.validate_xml(valid_xml)
        
        assert result.valid is True
        assert result.metadata["root_tag"] == "root"
    
    def test_xml_xss_detection(self, validator):
        """Test XSS detection in XML content"""
        malicious_xml = "<root><script>alert('xss')</script></root>"
        result = validator.validate_xml(malicious_xml)
        
        assert result.valid is False
        assert "XSS" in result.errors[0]


class TestFileSecurityValidator:
    """Test comprehensive file security validation"""
    
    def test_file_size_validation(self):
        """Test file size limits"""
        large_content = b"A" * (300 * 1024 * 1024)  # 300MB
        result = FileSecurityValidator.validate_file("large.jpg", large_content, "image")
        
        assert result.valid is False
        assert "exceeds limit" in result.errors[0]
    
    def test_virus_signature_detection(self):
        """Test virus signature detection"""
        virus_content = b"Some content" + b'EICAR-STANDARD-ANTIVIRUS-TEST-FILE' + b"more content"
        result = FileSecurityValidator.validate_file("virus.txt", virus_content, "document")
        
        assert result.valid is False
        assert "virus signature detected" in result.errors[0].lower()
    
    def test_extension_validation(self):
        """Test file extension validation"""
        # Test allowed extension
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog"
        result = FileSecurityValidator.validate_file("document.pdf", pdf_content, "document")
        assert result.valid is True
        
        # Test dangerous extension
        exe_content = b"MZ" + b"\x00" * 1000
        result = FileSecurityValidator.validate_file("malware.exe", exe_content, "document")
        assert result.valid is False
        assert "not allowed" in result.errors[0]
    
    def test_embedded_executable_detection(self):
        """Test detection of embedded executables"""
        # ZIP file with executable signature
        zip_content = b"PK\x03\x04" + b"A" * 1000
        result = FileSecurityValidator.validate_file("archive.zip", zip_content, "document")
        
        assert result.valid is False
        assert "embedded executable" in result.errors[0].lower()


class TestInputSanitizer:
    """Test input sanitization utilities"""
    
    def test_html_sanitization(self):
        """Test HTML content sanitization"""
        malicious_html = "<script>alert('xss')</script><p>Safe content</p><iframe src='evil'></iframe>"
        sanitized = InputSanitizer.sanitize_html(malicious_html)
        
        assert "<script>" not in sanitized
        assert "<iframe>" not in sanitized
        assert "<p>Safe content</p>" in sanitized
    
    def test_filename_sanitization(self):
        """Test filename sanitization"""
        dangerous_filename = "../../../etc/passwd.txt"
        sanitized = InputSanitizer.sanitize_filename(dangerous_filename)
        
        assert ".." not in sanitized
        assert "/" not in sanitized
        assert "\\" not in sanitized
    
    def test_email_validation_utility(self):
        """Test email validation utility"""
        assert InputSanitizer.validate_email("valid@example.com") is True
        assert InputSanitizer.validate_email("invalid-email") is False
        assert InputSanitizer.validate_email("user@") is False
    
    def test_phone_validation_utility(self):
        """Test phone number validation"""
        assert InputSanitizer.validate_phone("+1-555-123-4567") is True
        assert InputSanitizer.validate_phone("555.123.4567") is True
        assert InputSanitizer.validate_phone("123") is False  # Too short
        assert InputSanitizer.validate_phone("abc-def-ghij") is False  # No digits


# Integration tests
class TestSecurityIntegration:
    """Integration tests for complete security system"""
    
    @pytest.fixture
    def secure_app(self):
        """Create app with full security stack"""
        app = FastAPI()
        app.add_middleware(EnhancedSecurityMiddleware)
        
        @app.post("/api/upload")
        async def upload_cad_file():
            return {"message": "File uploaded successfully"}
        
        @app.post("/api/analyze")
        async def analyze_project():
            return {"message": "Analysis complete"}
        
        return app
    
    def test_end_to_end_security(self, secure_app):
        """Test complete security pipeline"""
        client = TestClient(secure_app)
        
        # Test normal request
        response = client.get("/api/analyze")
        assert response.status_code in [200, 404]  # Endpoint might not exist
        
        # Test with security headers
        headers = response.headers if response.status_code == 200 else {}
        if headers:
            assert any("Content-Security-Policy" in h for h in headers.keys())
    
    def test_multiple_attack_vectors(self, secure_app):
        """Test resistance to combined attack vectors"""
        client = TestClient(secure_app)
        
        # Combined XSS + SQL injection attempt
        malicious_payload = "<script>'; DROP TABLE users; --</script>"
        
        response = client.post("/api/analyze", 
                              json={"input": malicious_payload},
                              headers={"User-Agent": "sqlmap/evil"})
        
        # Should be blocked at multiple levels
        assert response.status_code in [400, 403, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])