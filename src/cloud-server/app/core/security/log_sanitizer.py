"""
Log Sanitizer for ArchBuilder.AI
Secrets in logs prevention - P43-T3
"""

import re
import json
import hashlib
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


@dataclass
class SanitizationRule:
    """Rule for sanitizing sensitive data"""
    pattern: str
    replacement: str
    description: str
    severity: str = "high"  # high, medium, low


class SecretPatterns:
    """Common secret patterns to detect and sanitize"""
    
    # API Keys and Tokens
    API_KEY_PATTERN = r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?'
    JWT_TOKEN_PATTERN = r'(?i)(jwt|token|bearer)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{50,})["\']?'
    ACCESS_TOKEN_PATTERN = r'(?i)(access[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?'
    
    # Database credentials
    DB_PASSWORD_PATTERN = r'(?i)(password|pwd|pass)\s*[:=]\s*["\']?([^"\'\s]{3,})["\']?'
    DB_CONNECTION_PATTERN = r'(?i)(database|db)[_-]?(url|uri|connection)\s*[:=]\s*["\']?([^"\'\s]+)["\']?'
    
    # Cloud credentials
    AWS_ACCESS_KEY_PATTERN = r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[:=]\s*["\']?([A-Z0-9]{20})["\']?'
    AWS_SECRET_KEY_PATTERN = r'(?i)(aws[_-]?secret[_-]?access[_-]?key)\s*[:=]\s*["\']?([A-Za-z0-9/+=]{40})["\']?'
    AZURE_KEY_PATTERN = r'(?i)(azure[_-]?key|azure[_-]?account[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9+/=]{40,})["\']?'
    
    # OpenAI/Azure OpenAI keys
    OPENAI_KEY_PATTERN = r'(?i)(openai[_-]?api[_-]?key)\s*[:=]\s*["\']?(sk-[a-zA-Z0-9]{48})["\']?'
    AZURE_OPENAI_KEY_PATTERN = r'(?i)(azure[_-]?openai[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9]{32})["\']?'
    
    # Vertex AI credentials
    VERTEX_AI_KEY_PATTERN = r'(?i)(vertex[_-]?ai[_-]?key|gcp[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?'
    
    # Stripe keys
    STRIPE_KEY_PATTERN = r'(?i)(stripe[_-]?key)\s*[:=]\s*["\']?(sk_[a-zA-Z0-9]{24,})["\']?'
    
    # Email credentials
    EMAIL_PASSWORD_PATTERN = r'(?i)(email[_-]?password|smtp[_-]?password)\s*[:=]\s*["\']?([^"\'\s]{3,})["\']?'
    
    # Generic secrets
    SECRET_PATTERN = r'(?i)(secret|private[_-]?key|credential)\s*[:=]\s*["\']?([^"\'\s]{8,})["\']?'
    
    # Credit card numbers (basic pattern)
    CREDIT_CARD_PATTERN = r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'
    
    # SSN pattern (US)
    SSN_PATTERN = r'\b(?:[0-9]{3}-[0-9]{2}-[0-9]{4}|[0-9]{9})\b'
    
    # Phone numbers
    PHONE_PATTERN = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'


class LogSanitizer:
    """Sanitizes logs to prevent secret leakage"""
    
    def __init__(self):
        self.rules = self._create_sanitization_rules()
        self.compiled_patterns = self._compile_patterns()
        
    def _create_sanitization_rules(self) -> List[SanitizationRule]:
        """Create sanitization rules"""
        return [
            SanitizationRule(
                pattern=SecretPatterns.API_KEY_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="API Key sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.JWT_TOKEN_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="JWT Token sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.ACCESS_TOKEN_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="Access Token sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.DB_PASSWORD_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="Database password sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.DB_CONNECTION_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="Database connection string sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.AWS_ACCESS_KEY_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="AWS Access Key sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.AWS_SECRET_KEY_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="AWS Secret Key sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.AZURE_KEY_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="Azure Key sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.OPENAI_KEY_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="OpenAI API Key sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.AZURE_OPENAI_KEY_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="Azure OpenAI Key sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.VERTEX_AI_KEY_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="Vertex AI Key sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.STRIPE_KEY_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="Stripe Key sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.EMAIL_PASSWORD_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="Email password sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.SECRET_PATTERN,
                replacement=r'\1=***REDACTED***',
                description="Generic secret sanitization",
                severity="medium"
            ),
            SanitizationRule(
                pattern=SecretPatterns.CREDIT_CARD_PATTERN,
                replacement="***REDACTED***",
                description="Credit card number sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.SSN_PATTERN,
                replacement="***REDACTED***",
                description="SSN sanitization",
                severity="high"
            ),
            SanitizationRule(
                pattern=SecretPatterns.PHONE_PATTERN,
                replacement="***REDACTED***",
                description="Phone number sanitization",
                severity="medium"
            )
        ]
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for performance"""
        compiled = {}
        for rule in self.rules:
            try:
                compiled[rule.pattern] = re.compile(rule.pattern, re.IGNORECASE)
            except re.error as e:
                logger.warning("Invalid regex pattern", pattern=rule.pattern, error=str(e))
        return compiled
    
    def sanitize_string(self, text: str) -> str:
        """Sanitize a string by removing/replacing secrets"""
        if not isinstance(text, str):
            return text
            
        sanitized = text
        
        for rule in self.rules:
            try:
                if rule.pattern in self.compiled_patterns:
                    sanitized = self.compiled_patterns[rule.pattern].sub(rule.replacement, sanitized)
            except Exception as e:
                logger.warning("Sanitization error", pattern=rule.pattern, error=str(e))
        
        return sanitized
    
    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary data"""
        if not isinstance(data, dict):
            return data
            
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize the key
            sanitized_key = self.sanitize_string(str(key))
            
            # Sanitize the value
            if isinstance(value, str):
                sanitized_value = self.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized_value = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized_value = self.sanitize_list(value)
            else:
                sanitized_value = value
                
            sanitized[sanitized_key] = sanitized_value
            
        return sanitized
    
    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """Recursively sanitize list data"""
        if not isinstance(data, list):
            return data
            
        sanitized = []
        
        for item in data:
            if isinstance(item, str):
                sanitized.append(self.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item))
            else:
                sanitized.append(item)
                
        return sanitized
    
    def sanitize_any(self, data: Any) -> Any:
        """Sanitize any data type"""
        if isinstance(data, str):
            return self.sanitize_string(data)
        elif isinstance(data, dict):
            return self.sanitize_dict(data)
        elif isinstance(data, list):
            return self.sanitize_list(data)
        else:
            return data
    
    def detect_secrets(self, text: str) -> List[Dict[str, Any]]:
        """Detect potential secrets in text"""
        if not isinstance(text, str):
            return []
            
        detected = []
        
        for rule in self.rules:
            if rule.pattern in self.compiled_patterns:
                matches = self.compiled_patterns[rule.pattern].findall(text)
                if matches:
                    detected.append({
                        "pattern": rule.pattern,
                        "description": rule.description,
                        "severity": rule.severity,
                        "matches": len(matches),
                        "sample": matches[0] if matches else None
                    })
        
        return detected
    
    def validate_no_secrets(self, data: Any) -> Dict[str, Any]:
        """Validate that data contains no secrets"""
        validation_result = {
            "has_secrets": False,
            "secret_count": 0,
            "secrets_found": [],
            "risk_level": "low"
        }
        
        if isinstance(data, str):
            secrets = self.detect_secrets(data)
        elif isinstance(data, dict):
            secrets = self.detect_secrets(json.dumps(data, default=str))
        else:
            secrets = self.detect_secrets(str(data))
        
        if secrets:
            validation_result["has_secrets"] = True
            validation_result["secret_count"] = sum(s["matches"] for s in secrets)
            validation_result["secrets_found"] = secrets
            
            # Determine risk level
            high_severity_count = sum(1 for s in secrets if s["severity"] == "high")
            if high_severity_count > 0:
                validation_result["risk_level"] = "high"
            elif validation_result["secret_count"] > 5:
                validation_result["risk_level"] = "medium"
        
        return validation_result


class SanitizedLogger:
    """Logger wrapper that automatically sanitizes log data"""
    
    def __init__(self, logger_instance, sanitizer: LogSanitizer):
        self.logger = logger_instance
        self.sanitizer = sanitizer
    
    def _sanitize_args(self, *args, **kwargs):
        """Sanitize logger arguments"""
        sanitized_args = []
        for arg in args:
            sanitized_args.append(self.sanitizer.sanitize_any(arg))
        
        sanitized_kwargs = {}
        for key, value in kwargs.items():
            sanitized_key = self.sanitizer.sanitize_string(str(key))
            sanitized_value = self.sanitizer.sanitize_any(value)
            sanitized_kwargs[sanitized_key] = sanitized_value
        
        return sanitized_args, sanitized_kwargs
    
    def debug(self, *args, **kwargs):
        sanitized_args, sanitized_kwargs = self._sanitize_args(*args, **kwargs)
        return self.logger.debug(*sanitized_args, **sanitized_kwargs)
    
    def info(self, *args, **kwargs):
        sanitized_args, sanitized_kwargs = self._sanitize_args(*args, **kwargs)
        return self.logger.info(*sanitized_args, **sanitized_kwargs)
    
    def warning(self, *args, **kwargs):
        sanitized_args, sanitized_kwargs = self._sanitize_args(*args, **kwargs)
        return self.logger.warning(*sanitized_args, **sanitized_kwargs)
    
    def error(self, *args, **kwargs):
        sanitized_args, sanitized_kwargs = self._sanitize_args(*args, **kwargs)
        return self.logger.error(*sanitized_args, **sanitized_kwargs)
    
    def critical(self, *args, **kwargs):
        sanitized_args, sanitized_kwargs = self._sanitize_args(*args, **kwargs)
        return self.logger.critical(*sanitized_args, **sanitized_kwargs)


# Global sanitizer instance
_sanitizer = LogSanitizer()


def get_sanitized_logger(logger_name: str = None):
    """Get a sanitized logger instance"""
    base_logger = structlog.get_logger(logger_name)
    return SanitizedLogger(base_logger, _sanitizer)


def sanitize_log_data(data: Any) -> Any:
    """Sanitize data for logging"""
    return _sanitizer.sanitize_any(data)


def validate_log_data(data: Any) -> Dict[str, Any]:
    """Validate that data is safe for logging"""
    return _sanitizer.validate_no_secrets(data)


# Structured logging processor
def sanitize_processor(logger, method_name, event_dict):
    """Structlog processor for automatic sanitization"""
    for key, value in event_dict.items():
        if isinstance(value, (str, dict, list)):
            event_dict[key] = _sanitizer.sanitize_any(value)
    return event_dict


# Configure structlog with sanitization
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        sanitize_processor,  # Add sanitization processor
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)



