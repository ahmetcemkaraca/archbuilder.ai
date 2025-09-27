"""
Enhanced Security Module for ArchBuilder.AI

Provides advanced security features including:
- File type validation using magic numbers
- MIME type verification
- File content analysis
- Security threat detection
"""

import logging
from pathlib import Path
from typing import Dict

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    magic = None
    MAGIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class EnhancedSecurityValidator:
    """Enhanced security validator with file type validation"""
    
    # Dangerous file extensions that should always be blocked
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.sh', '.py', '.php', '.asp', '.aspx', '.jsp', '.pl', '.rb', '.go'
    }
    
    # Allowed file extensions by category
    ALLOWED_CAD_EXTENSIONS = {'.dwg', '.dxf', '.ifc', '.rvt', '.3dm', '.step', '.iges'}
    ALLOWED_DOC_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg'}
    
    def __init__(self):
        """Initialize enhanced security validator"""
        if MAGIC_AVAILABLE:
            try:
                self.file_magic = magic.Magic(mime=True)
            except (OSError, ImportError, AttributeError) as e:
                logger.warning("Failed to initialize python-magic: %s", e)
                self.file_magic = None
        else:
            self.file_magic = None
            logger.info("python-magic not available, MIME validation disabled")
    
    def validate_upload_file(self, file_path: Path, content: bytes) -> Dict[str, any]:
        """
        Comprehensive file validation
        
        Args:
            file_path: Path object with file name and extension
            content: File content as bytes
            
        Returns:
            Dict with validation results
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'file_info': {}
        }
        
        # Basic extension validation
        if not self._validate_file_type(file_path, content):
            result['is_valid'] = False
            result['errors'].append(f"File type validation failed for {file_path.name}")
        
        # File size validation
        file_size = len(content)
        if file_size == 0:
            result['is_valid'] = False
            result['errors'].append("Empty file not allowed")
        elif file_size > 100 * 1024 * 1024:  # 100MB limit
            result['is_valid'] = False
            result['errors'].append("File size exceeds 100MB limit")
        
        # Content analysis
        content_analysis = self._analyze_file_content(content)
        result['file_info'].update(content_analysis)
        
        return result
    
    def _validate_file_type(self, file_path: Path, content: bytes) -> bool:
        """Validate file type using magic numbers and extension"""

        # Check extension
        extension = file_path.suffix.lower()

        # Block dangerous extensions
        if extension in self.DANGEROUS_EXTENSIONS:
            logger.warning("Dangerous file extension blocked: %s", extension)
            return False

        # Check if extension is in allowed lists
        allowed_extensions = (
            self.ALLOWED_CAD_EXTENSIONS | 
            self.ALLOWED_DOC_EXTENSIONS | 
            self.ALLOWED_IMAGE_EXTENSIONS
        )

        if extension not in allowed_extensions:
            logger.warning("File extension not in allowed list: %s", extension)
            return False

        # Validate MIME type matches extension (if magic is available)
        if self.file_magic:
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
                    logger.warning("MIME type mismatch: expected %s, got %s", expected_mime, detected_mime)
                    # For CAD files, be more lenient as they might not have specific MIME types
                    if extension not in self.ALLOWED_CAD_EXTENSIONS:
                        return False

            except (OSError, AttributeError, UnicodeDecodeError) as e:
                logger.warning("File type detection failed: %s", e)
                return False

        return True
    
    def _analyze_file_content(self, content: bytes) -> Dict[str, any]:
        """Analyze file content for additional security checks"""
        analysis = {
            'file_size': len(content),
            'has_null_bytes': b'\x00' in content[:1024],
            'suspicious_patterns': []
        }
        
        # Check for suspicious patterns in first 1KB
        sample = content[:1024]
        
        # Look for script tags, executable headers, etc.
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'MZ',  # PE executable header
            b'\x7fELF',  # ELF executable header
        ]
        
        for pattern in suspicious_patterns:
            if pattern in sample:
                analysis['suspicious_patterns'].append(pattern.decode('utf-8', errors='ignore'))
        
        return analysis


# Global instance
_enhanced_security = None


def get_enhanced_security() -> EnhancedSecurityValidator:
    """Get global enhanced security validator instance"""
    global _enhanced_security  # noqa: PLW0603
    if _enhanced_security is None:
        _enhanced_security = EnhancedSecurityValidator()
    return _enhanced_security