"""
File Abuse Detection for ArchBuilder.AI
File abuse scenarios - P44-T1
"""

import os
import hashlib
import magic
import mimetypes
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog
from pathlib import Path
import aiofiles
import asyncio

logger = structlog.get_logger(__name__)


class AbuseType(Enum):
    """Types of file abuse"""
    MALICIOUS_CONTENT = "malicious_content"
    OVERSIZED_FILE = "oversized_file"
    SUSPICIOUS_FORMAT = "suspicious_format"
    REPEATED_UPLOADS = "repeated_uploads"
    PATH_TRAVERSAL = "path_traversal"
    EXECUTABLE_CONTENT = "executable_content"
    ENCRYPTED_RANSOMWARE = "encrypted_ransomware"
    DATA_EXFILTRATION = "data_exfiltration"


@dataclass
class AbuseDetectionResult:
    """Result of abuse detection"""
    is_abuse: bool
    abuse_types: List[AbuseType]
    confidence: float  # 0.0 to 1.0
    details: Dict[str, Any]
    risk_level: str  # low, medium, high, critical
    recommendations: List[str]


@dataclass
class FileMetadata:
    """File metadata for analysis"""
    filename: str
    size_bytes: int
    mime_type: str
    file_extension: str
    content_hash: str
    upload_timestamp: float
    user_id: str
    ip_address: str


class FileAbuseDetector:
    """Detects various types of file abuse"""
    
    def __init__(self):
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.max_daily_uploads = 50
        self.suspicious_extensions = {
            '.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.vbs', '.js', '.jar',
            '.php', '.asp', '.jsp', '.sh', '.ps1', '.py', '.rb', '.pl'
        }
        self.allowed_extensions = {
            '.dwg', '.dxf', '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.tiff', '.tif', '.svg', '.doc', '.docx', '.xls', '.xlsx', '.ppt',
            '.pptx', '.txt', '.rtf', '.zip', '.rar', '.7z'
        }
        self.malicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'<iframe',
            b'<object',
            b'<embed',
            b'<applet',
            b'<form',
            b'<input',
            b'<textarea',
            b'<select',
            b'<button',
            b'<link',
            b'<meta',
            b'<style',
            b'<base',
            b'<frame',
            b'<frameset'
        ]
        self.ransomware_signatures = [
            b'encrypted',
            b'ransom',
            b'decrypt',
            b'payment',
            b'bitcoin',
            b'crypto',
            b'locked',
            b'key'
        ]
        
    async def analyze_file(self, file_path: str, metadata: FileMetadata) -> AbuseDetectionResult:
        """Analyze file for abuse patterns"""
        logger.info("Analyzing file for abuse", filename=metadata.filename, user_id=metadata.user_id)
        
        abuse_types = []
        confidence = 0.0
        details = {}
        recommendations = []
        
        # Check file size
        if metadata.size_bytes > self.max_file_size:
            abuse_types.append(AbuseType.OVERSIZED_FILE)
            confidence += 0.3
            details['file_size_mb'] = metadata.size_bytes / (1024 * 1024)
            details['max_allowed_mb'] = self.max_file_size / (1024 * 1024)
            recommendations.append("File size exceeds maximum allowed limit")
        
        # Check file extension
        if metadata.file_extension.lower() in self.suspicious_extensions:
            abuse_types.append(AbuseType.SUSPICIOUS_FORMAT)
            confidence += 0.4
            details['suspicious_extension'] = metadata.file_extension
            recommendations.append("File extension is not allowed for security reasons")
        
        # Check if extension is in allowed list
        if metadata.file_extension.lower() not in self.allowed_extensions:
            abuse_types.append(AbuseType.SUSPICIOUS_FORMAT)
            confidence += 0.2
            details['unallowed_extension'] = metadata.file_extension
            recommendations.append("File extension is not in the allowed list")
        
        # Check for path traversal
        if self._detect_path_traversal(metadata.filename):
            abuse_types.append(AbuseType.PATH_TRAVERSAL)
            confidence += 0.8
            details['path_traversal_detected'] = True
            recommendations.append("Filename contains path traversal patterns")
        
        # Check file content
        content_analysis = await self._analyze_file_content(file_path, metadata)
        if content_analysis['malicious_content']:
            abuse_types.append(AbuseType.MALICIOUS_CONTENT)
            confidence += 0.6
            details['malicious_patterns'] = content_analysis['malicious_patterns']
            recommendations.append("File contains potentially malicious content")
        
        if content_analysis['executable_content']:
            abuse_types.append(AbuseType.EXECUTABLE_CONTENT)
            confidence += 0.5
            details['executable_content'] = True
            recommendations.append("File appears to contain executable content")
        
        if content_analysis['ransomware_signatures']:
            abuse_types.append(AbuseType.ENCRYPTED_RANSOMWARE)
            confidence += 0.9
            details['ransomware_signatures'] = content_analysis['ransomware_signatures']
            recommendations.append("File may be encrypted ransomware")
        
        # Check for repeated uploads
        repeated_uploads = await self._check_repeated_uploads(metadata)
        if repeated_uploads['is_repeated']:
            abuse_types.append(AbuseType.REPEATED_UPLOADS)
            confidence += 0.3
            details['upload_frequency'] = repeated_uploads['frequency']
            details['similar_files'] = repeated_uploads['similar_count']
            recommendations.append("User is uploading files too frequently")
        
        # Determine risk level
        risk_level = self._determine_risk_level(abuse_types, confidence)
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        is_abuse = len(abuse_types) > 0 and confidence > 0.3
        
        return AbuseDetectionResult(
            is_abuse=is_abuse,
            abuse_types=abuse_types,
            confidence=confidence,
            details=details,
            risk_level=risk_level,
            recommendations=recommendations
        )
    
    def _detect_path_traversal(self, filename: str) -> bool:
        """Detect path traversal attempts"""
        traversal_patterns = [
            '../', '..\\', '/../', '\\..\\',
            '....//', '....\\\\',
            '%2e%2e%2f', '%2e%2e%5c',
            '..%2f', '..%5c',
            '%252e%252e%252f'
        ]
        
        filename_lower = filename.lower()
        return any(pattern in filename_lower for pattern in traversal_patterns)
    
    async def _analyze_file_content(self, file_path: str, metadata: FileMetadata) -> Dict[str, Any]:
        """Analyze file content for malicious patterns"""
        result = {
            'malicious_content': False,
            'executable_content': False,
            'ransomware_signatures': False,
            'malicious_patterns': [],
            'ransomware_signatures': []
        }
        
        try:
            # Read first 1MB of file for analysis
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read(1024 * 1024)  # 1MB sample
                
                # Check for malicious patterns
                for pattern in self.malicious_patterns:
                    if pattern in content.lower():
                        result['malicious_content'] = True
                        result['malicious_patterns'].append(pattern.decode('utf-8', errors='ignore'))
                
                # Check for executable signatures
                if self._is_executable_content(content, metadata.mime_type):
                    result['executable_content'] = True
                
                # Check for ransomware signatures
                for signature in self.ransomware_signatures:
                    if signature in content.lower():
                        result['ransomware_signatures'] = True
                        result['ransomware_signatures'].append(signature.decode('utf-8', errors='ignore'))
                
        except Exception as e:
            logger.warning("Error analyzing file content", error=str(e), filename=metadata.filename)
        
        return result
    
    def _is_executable_content(self, content: bytes, mime_type: str) -> bool:
        """Check if content appears to be executable"""
        # Check MIME type
        executable_mimes = [
            'application/x-executable',
            'application/x-msdownload',
            'application/x-msdos-program',
            'application/x-winexe',
            'application/x-elf',
            'application/x-mach-binary'
        ]
        
        if mime_type in executable_mimes:
            return True
        
        # Check for executable signatures
        executable_signatures = [
            b'MZ',  # DOS/Windows executable
            b'\x7fELF',  # ELF executable
            b'\xfe\xed\xfa',  # Mach-O executable
            b'\xce\xfa\xed\xfe',  # Mach-O executable (64-bit)
            b'\xca\xfe\xba\xbe',  # Java class file
        ]
        
        return any(content.startswith(sig) for sig in executable_signatures)
    
    async def _check_repeated_uploads(self, metadata: FileMetadata) -> Dict[str, Any]:
        """Check for repeated upload patterns"""
        # This would typically query a database
        # For now, return mock data
        return {
            'is_repeated': False,
            'frequency': 0,
            'similar_count': 0
        }
    
    def _determine_risk_level(self, abuse_types: List[AbuseType], confidence: float) -> str:
        """Determine risk level based on abuse types and confidence"""
        if not abuse_types:
            return "low"
        
        # Critical risk factors
        critical_types = {
            AbuseType.ENCRYPTED_RANSOMWARE,
            AbuseType.PATH_TRAVERSAL,
            AbuseType.MALICIOUS_CONTENT
        }
        
        if any(abuse_type in critical_types for abuse_type in abuse_types):
            return "critical"
        
        # High risk factors
        high_types = {
            AbuseType.EXECUTABLE_CONTENT,
            AbuseType.SUSPICIOUS_FORMAT
        }
        
        if any(abuse_type in high_types for abuse_type in abuse_types) or confidence > 0.7:
            return "high"
        
        # Medium risk factors
        medium_types = {
            AbuseType.OVERSIZED_FILE,
            AbuseType.REPEATED_UPLOADS
        }
        
        if any(abuse_type in medium_types for abuse_type in abuse_types) or confidence > 0.4:
            return "medium"
        
        return "low"
    
    async def scan_upload_directory(self, directory_path: str) -> List[AbuseDetectionResult]:
        """Scan directory for potential abuse files"""
        results = []
        
        try:
            directory = Path(directory_path)
            if not directory.exists():
                return results
            
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    # Create mock metadata
                    metadata = FileMetadata(
                        filename=file_path.name,
                        size_bytes=file_path.stat().st_size,
                        mime_type=mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream',
                        file_extension=file_path.suffix,
                        content_hash=await self._calculate_file_hash(file_path),
                        upload_timestamp=file_path.stat().st_mtime,
                        user_id="system",
                        ip_address="127.0.0.1"
                    )
                    
                    result = await self.analyze_file(str(file_path), metadata)
                    if result.is_abuse:
                        results.append(result)
                        
        except Exception as e:
            logger.error("Error scanning directory", error=str(e), directory=directory_path)
        
        return results
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                while chunk := await f.read(8192):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""


class FileAbuseMonitor:
    """Monitors file uploads for abuse patterns"""
    
    def __init__(self, detector: FileAbuseDetector):
        self.detector = detector
        self.upload_history: Dict[str, List[FileMetadata]] = {}
        
    async def monitor_upload(self, file_path: str, metadata: FileMetadata) -> AbuseDetectionResult:
        """Monitor a file upload for abuse"""
        # Add to upload history
        user_key = f"{metadata.user_id}_{metadata.ip_address}"
        if user_key not in self.upload_history:
            self.upload_history[user_key] = []
        
        self.upload_history[user_key].append(metadata)
        
        # Keep only last 100 uploads per user
        if len(self.upload_history[user_key]) > 100:
            self.upload_history[user_key] = self.upload_history[user_key][-100:]
        
        # Analyze file
        result = await self.detector.analyze_file(file_path, metadata)
        
        # Log abuse detection
        if result.is_abuse:
            logger.warning(
                "File abuse detected",
                filename=metadata.filename,
                user_id=metadata.user_id,
                abuse_types=[abuse_type.value for abuse_type in result.abuse_types],
                confidence=result.confidence,
                risk_level=result.risk_level,
                details=result.details
            )
        
        return result
    
    async def get_user_upload_stats(self, user_id: str, ip_address: str) -> Dict[str, Any]:
        """Get upload statistics for a user"""
        user_key = f"{user_id}_{ip_address}"
        uploads = self.upload_history.get(user_key, [])
        
        if not uploads:
            return {
                'total_uploads': 0,
                'total_size_mb': 0,
                'upload_frequency': 0,
                'risk_score': 0
            }
        
        total_size = sum(upload.size_bytes for upload in uploads)
        time_span = max(upload.upload_timestamp for upload in uploads) - min(upload.upload_timestamp for upload in uploads)
        frequency = len(uploads) / max(time_span / 3600, 1)  # uploads per hour
        
        # Calculate risk score
        risk_score = 0
        if len(uploads) > 50:
            risk_score += 0.3
        if total_size > 1000 * 1024 * 1024:  # 1GB
            risk_score += 0.3
        if frequency > 10:  # 10 uploads per hour
            risk_score += 0.4
        
        return {
            'total_uploads': len(uploads),
            'total_size_mb': total_size / (1024 * 1024),
            'upload_frequency': frequency,
            'risk_score': min(risk_score, 1.0)
        }


# Global instances
_detector = FileAbuseDetector()
_monitor = FileAbuseMonitor(_detector)


async def analyze_uploaded_file(file_path: str, metadata: FileMetadata) -> AbuseDetectionResult:
    """Analyze an uploaded file for abuse"""
    return await _monitor.monitor_upload(file_path, metadata)


async def scan_directory_for_abuse(directory_path: str) -> List[AbuseDetectionResult]:
    """Scan directory for abuse files"""
    return await _detector.scan_upload_directory(directory_path)


async def get_user_upload_risk(user_id: str, ip_address: str) -> Dict[str, Any]:
    """Get user upload risk assessment"""
    return await _monitor.get_user_upload_stats(user_id, ip_address)
