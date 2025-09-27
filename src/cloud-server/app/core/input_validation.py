"""
Enhanced Input Validation and Sanitization for ArchBuilder.AI
Provides comprehensive validation for CAD files, user inputs, and API requests.
"""
from __future__ import annotations

import json
import re
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, Tuple
from urllib.parse import urlparse

import bleach
from defusedxml import ElementTree as ET
from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, Field, validator, ValidationError
from pydantic.types import constr, conint, confloat

from app.core.logging import get_logger

logger = get_logger(__name__)


class ValidationResult(BaseModel):
    """Result of input validation"""
    
    valid: bool
    sanitized_data: Any = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SecurityConfig(BaseModel):
    """Security configuration for validation"""
    
    # XSS Protection
    allow_html: bool = False
    allowed_html_tags: Set[str] = {'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3'}
    allowed_html_attributes: Dict[str, List[str]] = Field(default_factory=dict)
    
    # File Upload
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_extensions: Set[str] = {'.pdf', '.txt', '.dwg', '.dxf', '.ifc', '.rvt', '.jpg', '.png'}
    blocked_file_extensions: Set[str] = {'.exe', '.bat', '.sh', '.js', '.vbs', '.scr'}
    
    # Input Length Limits
    max_string_length: int = 10000
    max_list_length: int = 1000
    max_dict_depth: int = 10
    
    # Pattern Matching
    enable_sql_injection_detection: bool = True
    enable_xss_detection: bool = True
    enable_path_traversal_detection: bool = True


class CADFileValidator:
    """Specialized validator for CAD file formats"""
    
    # CAD file format signatures and validation rules
    CAD_SIGNATURES = {
        '.dwg': {
            'magic_bytes': [b'AC10', b'AC12', b'AC13', b'AC14', b'AC15', b'AC18', b'AC21', b'AC24', b'AC27', b'AC32'],
            'min_size': 100,  # Minimum file size in bytes
            'max_size': 500 * 1024 * 1024,  # 500MB max for DWG
            'mime_types': ['application/acad', 'application/autocad', 'application/dwg', 'image/vnd.dwg']
        },
        '.dxf': {
            'text_markers': [b'0\r\nSECTION', b'0\nSECTION', b'999\r\nDXF', b'999\nDXF'],
            'min_size': 50,
            'max_size': 100 * 1024 * 1024,  # 100MB max for DXF
            'mime_types': ['application/dxf', 'image/vnd.dxf', 'text/plain']
        },
        '.ifc': {
            'text_markers': [b'ISO-10303-21', b'HEADER;', b'FILE_DESCRIPTION', b'IFC2X3', b'IFC4'],
            'min_size': 100,
            'max_size': 200 * 1024 * 1024,  # 200MB max for IFC
            'mime_types': ['application/x-ifc', 'model/ifc', 'text/plain']
        },
        '.rvt': {
            'magic_bytes': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],  # OLE compound document
            'min_size': 1000,
            'max_size': 1024 * 1024 * 1024,  # 1GB max for Revit files
            'mime_types': ['application/octet-stream', 'application/x-ole-storage']
        },
        '.step': {
            'text_markers': [b'ISO-10303-21', b'HEADER;', b'FILE_DESCRIPTION'],
            'min_size': 50,
            'max_size': 500 * 1024 * 1024,
            'mime_types': ['application/step', 'model/step', 'text/plain']
        },
        '.stp': {
            'text_markers': [b'ISO-10303-21', b'HEADER;', b'FILE_DESCRIPTION'],
            'min_size': 50,
            'max_size': 500 * 1024 * 1024,
            'mime_types': ['application/step', 'model/step', 'text/plain']
        }
    }
    
    @classmethod
    def validate_cad_file(cls, filename: str, content: bytes) -> ValidationResult:
        """Validate CAD file format and content"""
        
        result = ValidationResult(valid=True)
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        # Check if it's a supported CAD format
        if extension not in cls.CAD_SIGNATURES:
            result.valid = False
            result.errors.append(f"Unsupported CAD file format: {extension}")
            return result
        
        signature_config = cls.CAD_SIGNATURES[extension]
        
        # File size validation
        if len(content) < signature_config['min_size']:
            result.valid = False
            result.errors.append(f"File too small for {extension} format (min: {signature_config['min_size']} bytes)")
        
        if len(content) > signature_config['max_size']:
            result.valid = False
            result.errors.append(f"File too large for {extension} format (max: {signature_config['max_size']} bytes)")
        
        # Format-specific validation
        if extension == '.dwg':
            result = cls._validate_dwg_content(content, result)
        elif extension == '.dxf':
            result = cls._validate_dxf_content(content, result)
        elif extension == '.ifc':
            result = cls._validate_ifc_content(content, result)
        elif extension == '.rvt':
            result = cls._validate_rvt_content(content, result)
        elif extension in ['.step', '.stp']:
            result = cls._validate_step_content(content, result)
        
        # Add metadata
        result.metadata.update({
            'file_size': len(content),
            'file_format': extension,
            'estimated_cad_version': cls._detect_cad_version(extension, content)
        })
        
        return result
    
    @classmethod
    def _validate_dwg_content(cls, content: bytes, result: ValidationResult) -> ValidationResult:
        """Validate DWG file content"""
        
        # Check for DWG version signature
        dwg_versions = {
            b'AC1006': 'AutoCAD R10',
            b'AC1009': 'AutoCAD R11/R12',
            b'AC1012': 'AutoCAD R13',
            b'AC1014': 'AutoCAD R14',
            b'AC1015': 'AutoCAD 2000',
            b'AC1018': 'AutoCAD 2004',
            b'AC1021': 'AutoCAD 2007',
            b'AC1024': 'AutoCAD 2010',
            b'AC1027': 'AutoCAD 2013',
            b'AC1032': 'AutoCAD 2018+'
        }
        
        version_detected = False
        for version_sig, version_name in dwg_versions.items():
            if content.startswith(version_sig):
                result.metadata['dwg_version'] = version_name
                version_detected = True
                break
        
        if not version_detected:
            result.warnings.append("Could not detect DWG version - file may be corrupted or unsupported")
        
        # Basic structure validation
        if len(content) > 20:
            # Check for sentinel bytes (basic validation)
            if b'\x95\xa0' not in content[:100] and b'\x8f\x46' not in content[:100]:
                result.warnings.append("DWG file structure may be invalid")
        
        return result
    
    @classmethod
    def _validate_dxf_content(cls, content: bytes, result: ValidationResult) -> ValidationResult:
        """Validate DXF file content"""
        
        try:
            # Try to decode as text (DXF can be ASCII or binary)
            text_content = content.decode('utf-8', errors='ignore')
            
            # Check for required DXF sections
            required_sections = ['HEADER', 'TABLES', 'ENTITIES']
            found_sections = []
            
            for section in required_sections:
                if f'\n{section}\n' in text_content or f'\r\n{section}\r\n' in text_content:
                    found_sections.append(section)
            
            if len(found_sections) < 2:
                result.warnings.append(f"DXF file missing standard sections. Found: {found_sections}")
            
            # Check for AutoCAD version in header
            version_match = re.search(r'\$ACADVER\n.*\n([^\n]+)', text_content)
            if version_match:
                result.metadata['dxf_version'] = version_match.group(1).strip()
            
        except UnicodeDecodeError:
            # Binary DXF - basic validation only
            if b'AutoCAD' not in content[:1000]:
                result.warnings.append("Binary DXF file - limited validation available")
        
        return result
    
    @classmethod
    def _validate_ifc_content(cls, content: bytes, result: ValidationResult) -> ValidationResult:
        """Validate IFC file content"""
        
        try:
            text_content = content.decode('utf-8', errors='ignore')
            
            # Check for IFC header structure
            if 'ISO-10303-21' not in text_content[:100]:
                result.errors.append("Missing ISO-10303-21 header in IFC file")
                result.valid = False
            
            # Check for IFC schema version
            schema_match = re.search(r'FILE_SCHEMA\s*\(\s*\(\'([^\']+)\'', text_content)
            if schema_match:
                schema = schema_match.group(1)
                result.metadata['ifc_schema'] = schema
                
                # Validate known schemas
                known_schemas = ['IFC2X3', 'IFC4', 'IFC4X1', 'IFC4X2', 'IFC4X3']
                if not any(known in schema for known in known_schemas):
                    result.warnings.append(f"Unknown IFC schema: {schema}")
            
            # Check for proper structure
            if 'ENDSEC;' not in text_content:
                result.warnings.append("IFC file may be incomplete - missing ENDSEC markers")
            
        except UnicodeDecodeError:
            result.errors.append("IFC file is not valid UTF-8 text")
            result.valid = False
        
        return result
    
    @classmethod
    def _validate_rvt_content(cls, content: bytes, result: ValidationResult) -> ValidationResult:
        """Validate Revit RVT file content"""
        
        # RVT files are OLE compound documents - basic validation
        if not content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
            result.errors.append("RVT file is missing OLE compound document signature")
            result.valid = False
            return result
        
        # Look for Revit-specific markers in the first few KB
        revit_markers = [b'Autodesk Revit', b'Revit', b'ACA_Application']
        marker_found = False
        
        search_area = content[:10000]  # Search first 10KB
        for marker in revit_markers:
            if marker in search_area:
                marker_found = True
                break
        
        if not marker_found:
            result.warnings.append("File appears to be OLE document but Revit markers not found")
        
        # Estimate Revit version (basic heuristic)
        if b'2020' in search_area or b'2021' in search_area or b'2022' in search_area:
            result.metadata['estimated_revit_version'] = '2020+'
        elif b'2018' in search_area or b'2019' in search_area:
            result.metadata['estimated_revit_version'] = '2018-2019'
        else:
            result.metadata['estimated_revit_version'] = 'unknown'
        
        return result
    
    @classmethod
    def _validate_step_content(cls, content: bytes, result: ValidationResult) -> ValidationResult:
        """Validate STEP file content"""
        
        try:
            text_content = content.decode('utf-8', errors='ignore')
            
            # Check for STEP header
            if 'ISO-10303-21' not in text_content[:100]:
                result.errors.append("Missing ISO-10303-21 header in STEP file")
                result.valid = False
            
            # Check for STEP sections
            required_sections = ['HEADER', 'DATA']
            for section in required_sections:
                if f'{section};' not in text_content:
                    result.warnings.append(f"STEP file missing {section} section")
            
            # Extract file description
            desc_match = re.search(r'FILE_DESCRIPTION\s*\(\s*\(\'([^\']+)\'', text_content)
            if desc_match:
                result.metadata['step_description'] = desc_match.group(1)
            
        except UnicodeDecodeError:
            result.errors.append("STEP file is not valid UTF-8 text")
            result.valid = False
        
        return result
    
    @classmethod
    def _detect_cad_version(cls, extension: str, content: bytes) -> Optional[str]:
        """Detect CAD software version from file content"""
        
        if extension == '.dwg':
            for version_sig, version_name in {
                b'AC1032': 'AutoCAD 2018+',
                b'AC1027': 'AutoCAD 2013-2017',
                b'AC1024': 'AutoCAD 2010-2012',
                b'AC1021': 'AutoCAD 2007-2009'
            }.items():
                if content.startswith(version_sig):
                    return version_name
        
        elif extension == '.dxf':
            try:
                text = content[:2000].decode('utf-8', errors='ignore')
                version_match = re.search(r'\$ACADVER\n.*\n([^\n]+)', text)
                if version_match:
                    return f"AutoCAD {version_match.group(1).strip()}"
            except:
                pass
        
        return None


class EnhancedInputValidator:
    """Comprehensive input validation and sanitization"""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        
        # Compile regex patterns for performance
        self._sql_patterns = self._compile_sql_patterns()
        self._xss_patterns = self._compile_xss_patterns()
        self._path_traversal_patterns = self._compile_path_traversal_patterns()
    
    def _compile_sql_patterns(self) -> List[re.Pattern]:
        """Compile SQL injection detection patterns"""
        
        patterns = [
            # Basic SQL injection patterns
            r'\b(union|select|insert|delete|update|drop|create|alter|exec|execute)\s+',
            r'\b(or|and)\s+\d+\s*=\s*\d+\b',
            r';\s*(drop|delete|truncate|update)\s+',
            r'--\s*$',
            r'/\*.*\*/',
            r"'\s*(or|and)\s*'[^']*'\s*=\s*'",
            r'\bxp_cmdshell\b',
            r'\bsp_executesql\b',
            r'\bwaitfor\s+delay\b',
            
            # Advanced patterns
            r'\bunion\s+all\s+select\b',
            r'\bif\s*\(\s*\d+\s*=\s*\d+\s*\)',
            r'\bcast\s*\(\s*char\b',
            r'\bconvert\s*\(\s*(char|varchar)\b',
            
            # Time-based injection
            r'\bwaitfor\s+delay\s+[\'"][\d:]+[\'"]',
            r'\bsleep\s*\(\s*\d+\s*\)',
            r'\bbenchmark\s*\(',
            
            # Boolean-based injection
            r'\band\s+\d+\s*>\s*\d+\s*--',
            r'\bor\s+\d+\s*<\s*\d+\s*--',
        ]
        
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def _compile_xss_patterns(self) -> List[re.Pattern]:
        """Compile XSS detection patterns"""
        
        patterns = [
            # Script tags
            r'<\s*script[^>]*>.*?</\s*script\s*>',
            r'<\s*script[^>]*>',
            r'</\s*script\s*>',
            
            # Event handlers
            r'\bon\w+\s*=\s*[\'"][^\'\"]*[\'"]',
            r'\bon\w+\s*=\s*[^\s>]+',
            
            # JavaScript protocols
            r'javascript\s*:',
            r'vbscript\s*:',
            r'data\s*:\s*text/html',
            r'data\s*:.*base64',
            
            # Dangerous tags
            r'<\s*(iframe|object|embed|applet|meta)[^>]*>',
            r'<\s*link[^>]*rel\s*=\s*[\'"]stylesheet[\'"][^>]*>',
            
            # Encoded attacks
            r'%3Cscript',
            r'&lt;script',
            r'\\u003c\\u0073\\u0063\\u0072\\u0069\\u0070\\u0074',
            
            # DOM-based XSS
            r'document\.(write|writeln|location|cookie)',
            r'window\.(location|open)',
            r'eval\s*\(',
            r'setTimeout\s*\(',
            r'setInterval\s*\(',
            
            # HTML5 specific
            r'<\s*svg[^>]*on\w+',
            r'<\s*math[^>]*on\w+',
        ]
        
        return [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in patterns]
    
    def _compile_path_traversal_patterns(self) -> List[re.Pattern]:
        """Compile path traversal detection patterns"""
        
        patterns = [
            r'\.\./+',
            r'\.\.\\+',
            r'%2e%2e%2f',
            r'%2e%2e\\',
            r'\.\.%2f',
            r'\.\.%5c',
            r'%252e%252e%252f',
            r'\.\.\/+',
            r'\.\.\\+',
            r'\/\.\.\/+',
            r'\\\.\.\\+',
        ]
        
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def validate_string(self, value: str, field_name: str = "input") -> ValidationResult:
        """Validate and sanitize string input"""
        
        result = ValidationResult(valid=True)
        
        # Length validation
        if len(value) > self.config.max_string_length:
            result.valid = False
            result.errors.append(f"{field_name} exceeds maximum length ({self.config.max_string_length})")
            return result
        
        # SQL injection detection
        if self.config.enable_sql_injection_detection:
            for pattern in self._sql_patterns:
                if pattern.search(value):
                    result.valid = False
                    result.errors.append(f"Potential SQL injection detected in {field_name}")
                    break
        
        # XSS detection
        if self.config.enable_xss_detection:
            for pattern in self._xss_patterns:
                if pattern.search(value):
                    result.valid = False
                    result.errors.append(f"Potential XSS attack detected in {field_name}")
                    break
        
        # Path traversal detection
        if self.config.enable_path_traversal_detection:
            for pattern in self._path_traversal_patterns:
                if pattern.search(value):
                    result.valid = False
                    result.errors.append(f"Potential path traversal detected in {field_name}")
                    break
        
        # Sanitize if valid
        if result.valid:
            if self.config.allow_html:
                # Sanitize HTML while preserving allowed tags
                result.sanitized_data = bleach.clean(
                    value,
                    tags=self.config.allowed_html_tags,
                    attributes=self.config.allowed_html_attributes,
                    strip=True
                )
            else:
                # Strip all HTML tags
                result.sanitized_data = bleach.clean(value, tags=[], attributes={}, strip=True)
        
        return result
    
    def validate_email(self, email: str) -> ValidationResult:
        """Validate email address"""
        
        result = ValidationResult(valid=True)
        
        try:
            # Use email-validator library
            validated_email = validate_email(email)
            result.sanitized_data = validated_email.email
            result.metadata['normalized'] = validated_email.email
            result.metadata['local'] = validated_email.local
            result.metadata['domain'] = validated_email.domain
            
        except EmailNotValidError as e:
            result.valid = False
            result.errors.append(f"Invalid email format: {str(e)}")
        
        return result
    
    def validate_url(self, url: str, allowed_schemes: Optional[Set[str]] = None) -> ValidationResult:
        """Validate URL"""
        
        result = ValidationResult(valid=True)
        allowed_schemes = allowed_schemes or {'http', 'https'}
        
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme.lower() not in allowed_schemes:
                result.valid = False
                result.errors.append(f"URL scheme '{parsed.scheme}' not allowed")
            
            # Check for malicious patterns
            if any(pattern.search(url) for pattern in self._xss_patterns):
                result.valid = False
                result.errors.append("Potential XSS in URL")
            
            # Basic domain validation
            if not parsed.netloc:
                result.valid = False
                result.errors.append("URL missing domain")
            
            result.metadata['scheme'] = parsed.scheme
            result.metadata['domain'] = parsed.netloc
            result.metadata['path'] = parsed.path
            result.sanitized_data = url
            
        except Exception as e:
            result.valid = False
            result.errors.append(f"Invalid URL format: {str(e)}")
        
        return result
    
    def validate_json(self, json_str: str, max_depth: Optional[int] = None) -> ValidationResult:
        """Validate JSON string"""
        
        result = ValidationResult(valid=True)
        max_depth = max_depth or self.config.max_dict_depth
        
        try:
            parsed_json = json.loads(json_str)
            
            # Check nesting depth
            if self._get_dict_depth(parsed_json) > max_depth:
                result.valid = False
                result.errors.append(f"JSON nesting exceeds maximum depth ({max_depth})")
            
            # Validate string values in JSON
            validation_errors = []
            self._validate_json_strings(parsed_json, validation_errors)
            
            if validation_errors:
                result.valid = False
                result.errors.extend(validation_errors)
            
            result.sanitized_data = parsed_json
            result.metadata['size'] = len(json_str)
            result.metadata['depth'] = self._get_dict_depth(parsed_json)
            
        except json.JSONDecodeError as e:
            result.valid = False
            result.errors.append(f"Invalid JSON format: {str(e)}")
        
        return result
    
    def validate_xml(self, xml_str: str) -> ValidationResult:
        """Validate XML string using defusedxml for security"""
        
        result = ValidationResult(valid=True)
        
        try:
            # Use defusedxml to prevent XML bombs and other attacks
            root = ET.fromstring(xml_str)
            
            # Basic validation - check for suspicious content
            xml_text = ET.tostring(root, encoding='unicode')
            
            for pattern in self._xss_patterns:
                if pattern.search(xml_text):
                    result.valid = False
                    result.errors.append("Potential XSS detected in XML content")
                    break
            
            result.sanitized_data = xml_text
            result.metadata['root_tag'] = root.tag
            result.metadata['size'] = len(xml_str)
            
        except ET.ParseError as e:
            result.valid = False
            result.errors.append(f"Invalid XML format: {str(e)}")
        except Exception as e:
            result.valid = False
            result.errors.append(f"XML validation error: {str(e)}")
        
        return result
    
    def validate_file_upload(self, filename: str, content: bytes, file_category: str = "general") -> ValidationResult:
        """Validate file upload"""
        
        result = ValidationResult(valid=True)
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        result.sanitized_data = safe_filename
        
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        # Check blocked extensions
        if extension in self.config.blocked_file_extensions:
            result.valid = False
            result.errors.append(f"File extension '{extension}' is not allowed")
            return result
        
        # Check allowed extensions
        if extension not in self.config.allowed_file_extensions:
            result.valid = False
            result.errors.append(f"File extension '{extension}' is not in allowed list")
            return result
        
        # File size validation
        if len(content) > self.config.max_file_size:
            result.valid = False
            result.errors.append(f"File size ({len(content)} bytes) exceeds limit ({self.config.max_file_size} bytes)")
        
        # CAD file specific validation
        if extension in {'.dwg', '.dxf', '.ifc', '.rvt', '.step', '.stp'}:
            cad_result = CADFileValidator.validate_cad_file(filename, content)
            if not cad_result.valid:
                result.valid = False
                result.errors.extend(cad_result.errors)
            result.warnings.extend(cad_result.warnings)
            result.metadata.update(cad_result.metadata)
        
        # MIME type validation
        expected_mime = mimetypes.guess_type(filename)[0]
        result.metadata['expected_mime_type'] = expected_mime
        result.metadata['file_size'] = len(content)
        result.metadata['file_extension'] = extension
        
        return result
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        
        # Remove path components
        filename = Path(filename).name
        
        # Remove dangerous characters
        dangerous_chars = '<>:"|?*\x00'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Replace path traversal sequences
        filename = filename.replace('..', '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_len = 255 - len(ext) - 1
            filename = f"{name[:max_name_len]}.{ext}" if ext else name[:255]
        
        return filename
    
    def _get_dict_depth(self, obj: Any, depth: int = 0) -> int:
        """Calculate maximum nesting depth of dictionary/list"""
        
        if isinstance(obj, dict):
            return max([self._get_dict_depth(value, depth + 1) for value in obj.values()]) if obj else depth
        elif isinstance(obj, list):
            return max([self._get_dict_depth(item, depth + 1) for item in obj]) if obj else depth
        else:
            return depth
    
    def _validate_json_strings(self, obj: Any, errors: List[str]) -> None:
        """Recursively validate string values in JSON object"""
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    string_result = self.validate_string(value, f"JSON field '{key}'")
                    if not string_result.valid:
                        errors.extend(string_result.errors)
                else:
                    self._validate_json_strings(value, errors)
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str):
                    string_result = self.validate_string(item, f"JSON array item {i}")
                    if not string_result.valid:
                        errors.extend(string_result.errors)
                else:
                    self._validate_json_strings(item, errors)


# Pydantic models with enhanced validation
class SecureBaseModel(BaseModel):
    """Base model with built-in security validation"""
    
    class Config:
        # Prevent extra fields to avoid injection
        extra = "forbid"
        # Validate field assignments
        validate_assignment = True
        # Use enum values
        use_enum_values = True


# Specialized validators for ArchBuilder.AI
class ArchBuilderString(constr):
    """Secure string type for ArchBuilder.AI"""
    min_length = 1
    max_length = 10000
    regex = re.compile(r'^[^<>]*$')  # No angle brackets to prevent basic XSS


class ArchBuilderEmail(BaseModel):
    """Validated email field"""
    email: str
    
    @validator('email')
    def validate_email_field(cls, v):
        validator = EnhancedInputValidator()
        result = validator.validate_email(v)
        if not result.valid:
            raise ValueError(f"Invalid email: {'; '.join(result.errors)}")
        return result.sanitized_data


class ArchBuilderCADFile(BaseModel):
    """Validated CAD file upload"""
    filename: str
    content: bytes
    category: str = "cad"
    
    @validator('filename', 'content', pre=True)
    def validate_cad_file(cls, v, values):
        if 'filename' in values and 'content' in values:
            filename = values['filename']
            content = values['content']
            
            validator = EnhancedInputValidator()
            result = validator.validate_file_upload(filename, content, "cad")
            
            if not result.valid:
                raise ValueError(f"Invalid CAD file: {'; '.join(result.errors)}")
        
        return v


# Usage example for API endpoints
def validate_api_input(data: Dict[str, Any], validation_rules: Dict[str, str]) -> ValidationResult:
    """
    Validate API input data according to specified rules.
    
    Args:
        data: Input data dictionary
        validation_rules: Dictionary mapping field names to validation types
        
    Returns:
        ValidationResult with sanitized data
    """
    
    validator = EnhancedInputValidator()
    result = ValidationResult(valid=True)
    sanitized_data = {}
    
    for field_name, validation_type in validation_rules.items():
        if field_name not in data:
            continue
        
        field_value = data[field_name]
        field_result = None
        
        if validation_type == "string":
            field_result = validator.validate_string(str(field_value), field_name)
        elif validation_type == "email":
            field_result = validator.validate_email(str(field_value))
        elif validation_type == "url":
            field_result = validator.validate_url(str(field_value))
        elif validation_type == "json":
            field_result = validator.validate_json(str(field_value))
        elif validation_type == "xml":
            field_result = validator.validate_xml(str(field_value))
        
        if field_result:
            if not field_result.valid:
                result.valid = False
                result.errors.extend([f"{field_name}: {error}" for error in field_result.errors])
            else:
                sanitized_data[field_name] = field_result.sanitized_data
            
            result.warnings.extend([f"{field_name}: {warning}" for warning in field_result.warnings])
    
    result.sanitized_data = sanitized_data
    return result