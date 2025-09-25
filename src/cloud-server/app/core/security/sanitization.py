"""
Input/Output Sanitization for ArchBuilder.AI

Provides:
- Input validation and sanitization
- Output sanitization for security
- XSS prevention
- SQL injection prevention
- File upload security
"""

from __future__ import annotations

import html
import re
import uuid
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import bleach
import structlog
from pydantic import BaseModel, Field, validator

logger = structlog.get_logger(__name__)


class SanitizationConfig(BaseModel):
    """Sanitization configuration"""
    max_string_length: int = 10000
    max_file_size_mb: int = 100
    allowed_file_types: List[str] = Field(default_factory=lambda: [
        'pdf', 'dwg', 'dxf', 'ifc', 'rvt', 'jpg', 'jpeg', 'png', 'gif', 'txt', 'doc', 'docx'
    ])
    allowed_html_tags: List[str] = Field(default_factory=lambda: [
        'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
    ])
    allowed_html_attributes: List[str] = Field(default_factory=lambda: [
        'class', 'id', 'title'
    ])
    max_url_length: int = 2048
    max_json_depth: int = 10
    max_array_length: int = 1000


class SanitizationResult(BaseModel):
    """Sanitization result model"""
    is_valid: bool
    sanitized_value: Any
    original_value: Any
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    sanitization_applied: List[str] = Field(default_factory=list)


class InputSanitizer:
    """Input sanitization service for ArchBuilder.AI"""
    
    def __init__(self, config: SanitizationConfig):
        self.config = config
        
        # Compile regex patterns for performance
        self._email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self._uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        self._correlation_id_pattern = re.compile(r'^[A-Z]{2,3}_\d{14}_[a-f0-9]{32}$')
        self._sql_injection_pattern = re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)', re.IGNORECASE)
        self._xss_pattern = re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)
        
    def sanitize_string(self, value: str, field_name: str = "string") -> SanitizationResult:
        """Sanitize string input"""
        warnings = []
        errors = []
        sanitization_applied = []
        
        if not isinstance(value, str):
            return SanitizationResult(
                is_valid=False,
                sanitized_value=value,
                original_value=value,
                errors=[f"{field_name} must be a string"]
            )
        
        original_value = value
        sanitized_value = value
        
        # Check length
        if len(value) > self.config.max_string_length:
            errors.append(f"{field_name} exceeds maximum length of {self.config.max_string_length}")
            return SanitizationResult(
                is_valid=False,
                sanitized_value=value,
                original_value=original_value,
                errors=errors
            )
        
        # Remove null bytes
        if '\x00' in value:
            sanitized_value = sanitized_value.replace('\x00', '')
            sanitization_applied.append("null_bytes_removed")
        
        # Check for SQL injection patterns
        if self._sql_injection_pattern.search(value):
            errors.append(f"{field_name} contains potential SQL injection")
            return SanitizationResult(
                is_valid=False,
                sanitized_value=value,
                original_value=original_value,
                errors=errors
            )
        
        # Check for XSS patterns
        if self._xss_pattern.search(value):
            sanitized_value = self._xss_pattern.sub('', sanitized_value)
            sanitization_applied.append("xss_removed")
            warnings.append(f"{field_name} contained potential XSS, content removed")
        
        # HTML encode special characters
        if any(char in value for char in ['<', '>', '&', '"', "'"]):
            sanitized_value = html.escape(sanitized_value)
            sanitization_applied.append("html_encoded")
        
        # Trim whitespace
        if sanitized_value != sanitized_value.strip():
            sanitized_value = sanitized_value.strip()
            sanitization_applied.append("whitespace_trimmed")
        
        return SanitizationResult(
            is_valid=True,
            sanitized_value=sanitized_value,
            original_value=original_value,
            warnings=warnings,
            sanitization_applied=sanitization_applied
        )
    
    def sanitize_email(self, value: str) -> SanitizationResult:
        """Sanitize email input"""
        result = self.sanitize_string(value, "email")
        
        if not result.is_valid:
            return result
        
        # Validate email format
        if not self._email_pattern.match(result.sanitized_value):
            result.is_valid = False
            result.errors.append("Invalid email format")
        
        return result
    
    def sanitize_correlation_id(self, value: str) -> SanitizationResult:
        """Sanitize correlation ID input"""
        result = self.sanitize_string(value, "correlation_id")
        
        if not result.is_valid:
            return result
        
        # Validate correlation ID format
        if not self._correlation_id_pattern.match(result.sanitized_value):
            result.is_valid = False
            result.errors.append("Invalid correlation ID format")
        
        return result
    
    def sanitize_uuid(self, value: str) -> SanitizationResult:
        """Sanitize UUID input"""
        result = self.sanitize_string(value, "uuid")
        
        if not result.is_valid:
            return result
        
        # Validate UUID format
        if not self._uuid_pattern.match(result.sanitized_value):
            result.is_valid = False
            result.errors.append("Invalid UUID format")
        
        return result
    
    def sanitize_url(self, value: str) -> SanitizationResult:
        """Sanitize URL input"""
        result = self.sanitize_string(value, "url")
        
        if not result.is_valid:
            return result
        
        # Check URL length
        if len(result.sanitized_value) > self.config.max_url_length:
            result.is_valid = False
            result.errors.append(f"URL exceeds maximum length of {self.config.max_url_length}")
            return result
        
        # Validate URL format
        try:
            parsed = urlparse(result.sanitized_value)
            if not parsed.scheme or not parsed.netloc:
                result.is_valid = False
                result.errors.append("Invalid URL format")
        except Exception:
            result.is_valid = False
            result.errors.append("Invalid URL format")
        
        return result
    
    def sanitize_html(self, value: str) -> SanitizationResult:
        """Sanitize HTML input"""
        result = self.sanitize_string(value, "html")
        
        if not result.is_valid:
            return result
        
        # Use bleach to sanitize HTML
        try:
            sanitized_html = bleach.clean(
                result.sanitized_value,
                tags=self.config.allowed_html_tags,
                attributes=self.config.allowed_html_attributes,
                strip=True
            )
            
            if sanitized_html != result.sanitized_value:
                result.sanitized_value = sanitized_html
                result.sanitization_applied.append("html_sanitized")
                result.warnings.append("HTML content was sanitized")
            
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"HTML sanitization failed: {str(e)}")
        
        return result
    
    def sanitize_json(self, value: Any, max_depth: int = None) -> SanitizationResult:
        """Sanitize JSON input"""
        max_depth = max_depth or self.config.max_json_depth
        
        def _sanitize_recursive(obj: Any, current_depth: int = 0) -> Any:
            if current_depth > max_depth:
                raise ValueError("JSON depth exceeds maximum allowed depth")
            
            if isinstance(obj, dict):
                return {k: _sanitize_recursive(v, current_depth + 1) for k, v in obj.items()}
            elif isinstance(obj, list):
                if len(obj) > self.config.max_array_length:
                    raise ValueError("Array length exceeds maximum allowed length")
                return [_sanitize_recursive(item, current_depth + 1) for item in obj]
            elif isinstance(obj, str):
                str_result = self.sanitize_string(obj)
                return str_result.sanitized_value if str_result.is_valid else obj
            else:
                return obj
        
        try:
            sanitized_value = _sanitize_recursive(value)
            return SanitizationResult(
                is_valid=True,
                sanitized_value=sanitized_value,
                original_value=value,
                sanitization_applied=["json_sanitized"]
            )
        except Exception as e:
            return SanitizationResult(
                is_valid=False,
                sanitized_value=value,
                original_value=value,
                errors=[f"JSON sanitization failed: {str(e)}"]
            )
    
    def sanitize_file_upload(self, filename: str, file_size: int, content_type: str) -> SanitizationResult:
        """Sanitize file upload parameters"""
        errors = []
        warnings = []
        sanitization_applied = []
        
        # Sanitize filename
        filename_result = self.sanitize_string(filename, "filename")
        if not filename_result.is_valid:
            return filename_result
        
        # Check file extension
        file_extension = filename_result.sanitized_value.split('.')[-1].lower()
        if file_extension not in self.config.allowed_file_types:
            errors.append(f"File type '{file_extension}' not allowed")
        
        # Check file size
        max_size_bytes = self.config.max_file_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            errors.append(f"File size {file_size} bytes exceeds maximum {max_size_bytes} bytes")
        
        # Check content type
        allowed_content_types = [
            'application/pdf',
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
            'text/plain',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/octet-stream'  # For CAD files
        ]
        
        if content_type not in allowed_content_types:
            warnings.append(f"Content type '{content_type}' may not be supported")
        
        # Remove path traversal attempts
        if '..' in filename_result.sanitized_value or '/' in filename_result.sanitized_value:
            sanitized_filename = filename_result.sanitized_value.replace('..', '').replace('/', '_')
            sanitization_applied.append("path_traversal_removed")
            warnings.append("Path traversal characters removed from filename")
        else:
            sanitized_filename = filename_result.sanitized_value
        
        return SanitizationResult(
            is_valid=len(errors) == 0,
            sanitized_value={
                'filename': sanitized_filename,
                'file_size': file_size,
                'content_type': content_type
            },
            original_value={
                'filename': filename,
                'file_size': file_size,
                'content_type': content_type
            },
            warnings=warnings,
            errors=errors,
            sanitization_applied=sanitization_applied
        )


class OutputSanitizer:
    """Output sanitization service for ArchBuilder.AI"""
    
    def __init__(self, config: SanitizationConfig):
        self.config = config
    
    def sanitize_response(self, response: Any) -> Any:
        """Sanitize API response output"""
        if isinstance(response, dict):
            return {k: self.sanitize_response(v) for k, v in response.items()}
        elif isinstance(response, list):
            return [self.sanitize_response(item) for item in response]
        elif isinstance(response, str):
            # Remove any potential XSS or malicious content
            sanitized = html.escape(response)
            return sanitized
        else:
            return response
    
    def sanitize_error_message(self, error: str) -> str:
        """Sanitize error messages to prevent information leakage"""
        # Remove sensitive information patterns
        sensitive_patterns = [
            r'password[=:]\s*\S+',
            r'token[=:]\s*\S+',
            r'key[=:]\s*\S+',
            r'secret[=:]\s*\S+',
            r'file://.*',
            r'C:\\\\.*',
            r'/etc/.*',
            r'/home/.*'
        ]
        
        sanitized_error = error
        for pattern in sensitive_patterns:
            sanitized_error = re.sub(pattern, '[REDACTED]', sanitized_error, flags=re.IGNORECASE)
        
        return sanitized_error


# Global sanitizer instances
_input_sanitizer: Optional[InputSanitizer] = None
_output_sanitizer: Optional[OutputSanitizer] = None


def initialize_sanitizers(config: SanitizationConfig) -> None:
    """Initialize global sanitizer instances"""
    global _input_sanitizer, _output_sanitizer
    
    _input_sanitizer = InputSanitizer(config)
    _output_sanitizer = OutputSanitizer(config)


def get_input_sanitizer() -> InputSanitizer:
    """Get global input sanitizer instance"""
    if _input_sanitizer is None:
        raise RuntimeError("Input sanitizer not initialized")
    return _input_sanitizer


def get_output_sanitizer() -> OutputSanitizer:
    """Get global output sanitizer instance"""
    if _output_sanitizer is None:
        raise RuntimeError("Output sanitizer not initialized")
    return _output_sanitizer
