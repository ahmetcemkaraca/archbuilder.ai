"""
Enhanced Security Middleware for ArchBuilder.AI
Provides comprehensive security hardening including CSP, HSTS, input validation, and threat detection.
"""
from __future__ import annotations

import hashlib
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import quote

import bleach
import magic
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger

logger = get_logger(__name__)


class EnhancedSecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware that provides multiple layers of protection:
    - Advanced security headers with nonce support
    - Request/response sanitization  
    - File upload security validation
    - SQL injection and XSS prevention
    - Threat detection and rate limiting
    """
    
    # Dangerous file extensions that should never be allowed
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js', '.jar',
        '.sh', '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl'
    }
    
    # Allowed CAD file extensions for ArchBuilder.AI
    ALLOWED_CAD_EXTENSIONS = {
        '.dwg', '.dxf', '.ifc', '.rvt', '.3dm', '.step', '.stp', '.iges', '.igs',
        '.obj', '.stl', '.ply', '.fbx', '.dae', '.3ds', '.max', '.blend'
    }
    
    # Allowed document extensions
    ALLOWED_DOC_EXTENSIONS = {
        '.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.odt', '.ods', '.odp', '.rtf'
    }
    
    # Allowed image extensions
    ALLOWED_IMAGE_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.webp'
    }
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\s*(union|select|insert|delete|update|drop|create|alter|exec|execute)\s+)",
        r"(\s*(or|and)\s+\d+\s*=\s*\d+)",
        r"(\s*;\s*(drop|delete|truncate)\s+)",
        r"(\s*--\s*)",
        r"(\s*/\*.*\*/\s*)",
        r"(\s*'\s*(or|and)\s*'[^']*'\s*=\s*')",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<\s*script[^>]*>.*?</\s*script\s*>",
        r"<\s*iframe[^>]*>.*?</\s*iframe\s*>",
        r"<\s*object[^>]*>.*?</\s*object\s*>",
        r"<\s*embed[^>]*>.*?</\s*embed\s*>",
        r"javascript\s*:",
        r"vbscript\s*:",
        r"data\s*:.*base64",
        r"on\w+\s*=",
    ]
    
    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(app)
        self.config = config or {}
        
        # Compile regex patterns for performance
        self.sql_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SQL_INJECTION_PATTERNS]
        self.xss_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.XSS_PATTERNS]
        
        # Initialize file type detector
        self.file_magic = magic.Magic(mime=True)
        
        # Initialize threat detection
        self.threat_scores: Dict[str, float] = {}
        self.blocked_ips: Set[str] = set()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Main security middleware dispatch"""
        
        # Generate nonce for CSP
        nonce = self._generate_nonce()
        request.state.csp_nonce = nonce
        
        # Extract client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return self._security_error_response(
                "Access denied", 
                status.HTTP_403_FORBIDDEN,
                request.state.get("correlation_id", str(uuid.uuid4()))
            )
        
        # Threat detection
        threat_score = await self._calculate_threat_score(request, client_ip, user_agent)
        if threat_score > 0.8:  # High threat threshold
            logger.warning(f"High threat score detected: {threat_score} from {client_ip}")
            self.blocked_ips.add(client_ip)
            return self._security_error_response(
                "Security threat detected", 
                status.HTTP_403_FORBIDDEN,
                request.state.get("correlation_id", str(uuid.uuid4()))
            )
        
        # Input validation and sanitization
        try:
            await self._validate_request_input(request)
        except SecurityViolation as e:
            logger.warning(f"Security violation: {e.message} from {client_ip}")
            return self._security_error_response(
                e.message, 
                e.status_code,
                request.state.get("correlation_id", str(uuid.uuid4()))
            )
        
        # File upload validation (if applicable)
        if request.method == "POST" and "multipart/form-data" in request.headers.get("content-type", ""):
            try:
                await self._validate_file_uploads(request)
            except SecurityViolation as e:
                logger.warning(f"File upload violation: {e.message} from {client_ip}")
                return self._security_error_response(
                    e.message, 
                    e.status_code,
                    request.state.get("correlation_id", str(uuid.uuid4()))
                )
        
        # Process request
        response = await call_next(request)
        
        # Apply security headers
        self._apply_security_headers(response, nonce)
        
        # Sanitize response if needed
        await self._sanitize_response(response)
        
        return response
    
    def _generate_nonce(self) -> str:
        """Generate cryptographically secure nonce for CSP"""
        return hashlib.sha256(f"{time.time()}{uuid.uuid4()}".encode()).hexdigest()[:16]
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP address"""
        # Check various headers in order of trustworthiness
        for header in ["X-Forwarded-For", "X-Real-IP", "CF-Connecting-IP"]:
            value = request.headers.get(header)
            if value:
                # Take first IP if comma-separated
                ip = value.split(",")[0].strip()
                if self._is_valid_ip(ip):
                    return ip
        
        # Fallback to direct connection
        if request.client and request.client.host:
            return request.client.host
        
        return "unknown"
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Basic IP address validation"""
        try:
            parts = ip.split(".")
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            return False
    
    async def _calculate_threat_score(self, request: Request, client_ip: str, user_agent: str) -> float:
        """Calculate threat score based on various factors"""
        score = 0.0
        
        # Suspicious user agents
        suspicious_agents = ["sqlmap", "nikto", "nmap", "masscan", "zap", "burp"]
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            score += 0.5
        
        # Empty or missing user agent
        if not user_agent or len(user_agent.strip()) < 10:
            score += 0.2
        
        # Rapid requests from same IP
        current_time = time.time()
        ip_key = f"requests:{client_ip}"
        
        # Simulate rate tracking (in production, use Redis)
        if client_ip not in self.threat_scores:
            self.threat_scores[client_ip] = current_time
        else:
            last_request = self.threat_scores[client_ip]
            if current_time - last_request < 1.0:  # Less than 1 second between requests
                score += 0.3
            self.threat_scores[client_ip] = current_time
        
        # Suspicious paths
        suspicious_paths = ["/admin", "/.env", "/config", "/backup", "/wp-admin", "/phpmyadmin"]
        if any(path in request.url.path.lower() for path in suspicious_paths):
            score += 0.4
        
        # Multiple security headers missing or suspicious
        security_headers = ["User-Agent", "Accept", "Accept-Language"]
        missing_headers = sum(1 for header in security_headers if not request.headers.get(header))
        score += missing_headers * 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    async def _validate_request_input(self, request: Request) -> None:
        """Validate and sanitize request input for security threats"""
        
        # Check URL path for injection attempts
        self._check_sql_injection(request.url.path)
        self._check_xss_patterns(request.url.path)
        
        # Check query parameters
        for key, value in request.query_params.items():
            self._check_sql_injection(f"{key}={value}")
            self._check_xss_patterns(f"{key}={value}")
        
        # Check headers for suspicious content
        for header_name, header_value in request.headers.items():
            if header_name.lower() not in ["authorization", "cookie"]:  # Skip sensitive headers
                self._check_xss_patterns(header_value)
    
    def _check_sql_injection(self, text: str) -> None:
        """Check text for SQL injection patterns"""
        for pattern in self.sql_patterns:
            if pattern.search(text):
                raise SecurityViolation(
                    "Potential SQL injection detected",
                    status.HTTP_400_BAD_REQUEST
                )
    
    def _check_xss_patterns(self, text: str) -> None:
        """Check text for XSS patterns"""
        for pattern in self.xss_patterns:
            if pattern.search(text):
                raise SecurityViolation(
                    "Potential XSS attack detected",
                    status.HTTP_400_BAD_REQUEST
                )
    
    async def _validate_file_uploads(self, request: Request) -> None:
        """Validate uploaded files for security"""
        # This is a simplified check - in reality, you'd need to parse multipart data
        content_type = request.headers.get("content-type", "")
        
        # Check content type
        if "multipart/form-data" not in content_type:
            return
        
        # Get content length
        content_length = request.headers.get("content-length")
        if content_length:
            size = int(content_length)
            max_size = self.config.get("max_file_size", 100 * 1024 * 1024)  # 100MB default
            if size > max_size:
                raise SecurityViolation(
                    f"File size exceeds maximum allowed ({max_size} bytes)",
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                )
    
    def _validate_file_type(self, file_path: Path, content: bytes) -> bool:
        """Validate file type using magic numbers and extension"""
        
        # Check extension
        extension = file_path.suffix.lower()
        
        # Block dangerous extensions
        if extension in self.DANGEROUS_EXTENSIONS:
            return False
        
        # Check if extension is in allowed lists
        allowed_extensions = (
            self.ALLOWED_CAD_EXTENSIONS | 
            self.ALLOWED_DOC_EXTENSIONS | 
            self.ALLOWED_IMAGE_EXTENSIONS
        )
        
        if extension not in allowed_extensions:
            return False
        
        # Validate MIME type matches extension
        try:
            detected_mime = self.file_magic.from_buffer(content[:2048])  # Check first 2KB
            
            # Basic MIME type validation
            mime_mapping = {
                '.pdf': 'application/pdf',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg', 
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.txt': 'text/plain',
                '.dwg': 'application/octet-stream',  # CAD files often show as binary
                '.dxf': 'application/dxf',
                '.ifc': 'application/x-ifc',
            }
            
            expected_mime = mime_mapping.get(extension)
            if expected_mime and expected_mime not in detected_mime:
                logger.warning(f"MIME type mismatch: expected {expected_mime}, got {detected_mime}")
                # For CAD files, be more lenient as they might not have specific MIME types
                if extension not in self.ALLOWED_CAD_EXTENSIONS:
                    return False
            
        except Exception as e:
            logger.warning(f"File type detection failed: {e}")
            return False
        
        return True
    
    def _apply_security_headers(self, response: Response, nonce: str) -> None:
        """Apply comprehensive security headers"""
        
        # Content Security Policy with nonce
        csp_policy = (
            f"default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' 'strict-dynamic'; "
            f"style-src 'self' 'unsafe-inline'; "
            f"img-src 'self' data: https:; "
            f"font-src 'self' https:; "
            f"connect-src 'self' https:; "
            f"media-src 'self'; "
            f"object-src 'none'; "
            f"frame-src 'none'; "
            f"base-uri 'self'; "
            f"form-action 'self'; "
            f"upgrade-insecure-requests"
        )
        
        security_headers = {
            # CSP and frame protection
            "Content-Security-Policy": csp_policy,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            
            # HSTS (HTTP Strict Transport Security)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permission policy (formerly Feature Policy)
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            ),
            
            # Additional security headers
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }
        
        # Apply all security headers
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value
    
    async def _sanitize_response(self, response: Response) -> None:
        """Sanitize response content if needed"""
        
        # Only sanitize HTML content types
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type and hasattr(response, 'body'):
            try:
                # Use bleach to sanitize HTML content
                if isinstance(response.body, bytes):
                    content = response.body.decode('utf-8')
                else:
                    content = str(response.body)
                
                sanitized = bleach.clean(
                    content,
                    tags=['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3'],
                    attributes={},
                    strip=True
                )
                
                response.body = sanitized.encode('utf-8')
                
            except Exception as e:
                logger.warning(f"Response sanitization failed: {e}")
    
    def _security_error_response(self, message: str, status_code: int, correlation_id: str) -> JSONResponse:
        """Generate standardized security error response"""
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": {
                    "message": message,
                    "correlation_id": correlation_id,
                    "timestamp": int(time.time())
                }
            },
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Security-Event": "blocked"
            }
        )


class SecurityViolation(Exception):
    """Custom exception for security violations"""
    
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InputSanitizer:
    """Utility class for input sanitization"""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitize HTML content"""
        return bleach.clean(
            text,
            tags=['p', 'br', 'strong', 'em', 'ul', 'ol', 'li'],
            attributes={},
            strip=True
        )
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Remove or replace dangerous characters
        dangerous_chars = '<>:"|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # URL encode special characters
        filename = quote(filename, safe='.-_')
        
        # Limit length
        max_length = 255
        if len(filename) > max_length:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            name = name[:max_length - len(ext) - 1]
            filename = f"{name}.{ext}" if ext else name
        
        return filename
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        # Check if it's a reasonable length
        return 10 <= len(digits) <= 15


class FileSecurityValidator:
    """Comprehensive file security validation"""
    
    # Maximum file sizes by category (in bytes)
    MAX_SIZES = {
        'image': 10 * 1024 * 1024,  # 10MB
        'document': 50 * 1024 * 1024,  # 50MB
        'cad': 200 * 1024 * 1024,  # 200MB
    }
    
    # Virus signature patterns (simplified)
    VIRUS_SIGNATURES = [
        b'EICAR-STANDARD-ANTIVIRUS-TEST-FILE',  # EICAR test file
        b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR',  # EICAR variants
    ]
    
    @classmethod
    def validate_file(cls, filename: str, content: bytes, file_category: str) -> Dict[str, Any]:
        """Comprehensive file validation"""
        
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        # Check file size
        max_size = cls.MAX_SIZES.get(file_category, cls.MAX_SIZES['document'])
        if len(content) > max_size:
            results['valid'] = False
            results['errors'].append(f"File size ({len(content)} bytes) exceeds limit ({max_size} bytes)")
        
        # Check for virus signatures
        for signature in cls.VIRUS_SIGNATURES:
            if signature in content:
                results['valid'] = False
                results['errors'].append("Potential virus signature detected")
                break
        
        # Validate file extension
        extension = Path(filename).suffix.lower()
        if not cls._validate_extension(extension, file_category):
            results['valid'] = False
            results['errors'].append(f"File extension '{extension}' not allowed for category '{file_category}'")
        
        # Check for embedded executables (ZIP bombs, etc.)
        if cls._check_embedded_executable(content):
            results['valid'] = False
            results['errors'].append("Embedded executable content detected")
        
        # Extract metadata
        results['metadata'] = {
            'size': len(content),
            'extension': extension,
            'category': file_category
        }
        
        return results
    
    @staticmethod
    def _validate_extension(extension: str, category: str) -> bool:
        """Validate file extension for category"""
        
        category_extensions = {
            'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp'},
            'document': {'.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'},
            'cad': {'.dwg', '.dxf', '.ifc', '.rvt', '.3dm', '.step', '.stp', '.iges', '.igs'}
        }
        
        return extension in category_extensions.get(category, set())
    
    @staticmethod
    def _check_embedded_executable(content: bytes) -> bool:
        """Check for embedded executables"""
        
        # Check for common executable signatures
        executable_signatures = [
            b'MZ',  # PE/DOS executable
            b'\x7fELF',  # ELF executable
            b'\xca\xfe\xba\xbe',  # Mach-O executable
            b'PK\x03\x04',  # ZIP file (could contain executables)
        ]
        
        for signature in executable_signatures:
            if content.startswith(signature):
                return True
        
        return False