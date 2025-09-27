"""
PII (Personally Identifiable Information) Masking for ArchBuilder.AI

Provides:
- PII detection and masking
- Data anonymization
- GDPR compliance
- Audit trail for data access
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class PIIType(str, Enum):
    """PII type categories"""

    EMAIL = "email"
    PHONE = "phone"
    CREDIT_CARD = "credit_card"
    SSN = "ssn"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"
    IP_ADDRESS = "ip_address"
    MAC_ADDRESS = "mac_address"
    NAME = "name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    USER_ID = "user_id"
    CORRELATION_ID = "correlation_id"


class MaskingStrategy(str, Enum):
    """PII masking strategies"""

    HASH = "hash"
    REDACT = "redact"
    ANONYMIZE = "anonymize"
    TOKENIZE = "tokenize"
    REMOVE = "remove"


class PIIMatch(BaseModel):
    """PII match result"""

    pii_type: PIIType
    original_value: str
    masked_value: str
    confidence: float
    start_position: int
    end_position: int
    masking_strategy: MaskingStrategy


class PIIMaskingResult(BaseModel):
    """PII masking result"""

    original_text: str
    masked_text: str
    matches: List[PIIMatch]
    total_matches: int
    masking_applied: bool
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)


class PIIMasker:
    """PII masking service for ArchBuilder.AI"""

    def __init__(self):
        # Compile regex patterns for PII detection
        self._patterns = {
            PIIType.EMAIL: re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE
            ),
            PIIType.PHONE: re.compile(
                r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
                re.IGNORECASE,
            ),
            PIIType.CREDIT_CARD: re.compile(
                r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'
            ),
            PIIType.SSN: re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            PIIType.IP_ADDRESS: re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            PIIType.MAC_ADDRESS: re.compile(
                r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b'
            ),
            PIIType.DATE_OF_BIRTH: re.compile(
                r'\b(?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12][0-9]|3[01])[-/](?:19|20)\d{2}\b'
            ),
            PIIType.USER_ID: re.compile(
                r'\buser[_-]?id[=:]\s*[a-zA-Z0-9_-]+\b', re.IGNORECASE
            ),
            PIIType.CORRELATION_ID: re.compile(r'\b[A-Z]{2,3}_\d{14}_[a-f0-9]{32}\b'),
        }

        # Name patterns (basic detection)
        self._name_patterns = [
            re.compile(
                r'\b(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
            ),
            re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'),
        ]

        # Address patterns
        self._address_patterns = [
            re.compile(
                r'\b\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)\b'
            ),
            re.compile(
                r'\b[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)\b'
            ),
        ]

    def detect_pii(self, text: str) -> List[PIIMatch]:
        """Detect PII in text"""
        matches = []

        # Check each PII type
        for pii_type, pattern in self._patterns.items():
            for match in pattern.finditer(text):
                confidence = self._calculate_confidence(pii_type, match.group())

                matches.append(
                    PIIMatch(
                        pii_type=pii_type,
                        original_value=match.group(),
                        masked_value="",  # Will be set during masking
                        confidence=confidence,
                        start_position=match.start(),
                        end_position=match.end(),
                        masking_strategy=self._get_masking_strategy(pii_type),
                    )
                )

        # Check name patterns
        for pattern in self._name_patterns:
            for match in pattern.finditer(text):
                confidence = self._calculate_confidence(PIIType.NAME, match.group())

                matches.append(
                    PIIMatch(
                        pii_type=PIIType.NAME,
                        original_value=match.group(),
                        masked_value="",
                        confidence=confidence,
                        start_position=match.start(),
                        end_position=match.end(),
                        masking_strategy=self._get_masking_strategy(PIIType.NAME),
                    )
                )

        # Check address patterns
        for pattern in self._address_patterns:
            for match in pattern.finditer(text):
                confidence = self._calculate_confidence(PIIType.ADDRESS, match.group())

                matches.append(
                    PIIMatch(
                        pii_type=PIIType.ADDRESS,
                        original_value=match.group(),
                        masked_value="",
                        confidence=confidence,
                        start_position=match.start(),
                        end_position=match.end(),
                        masking_strategy=self._get_masking_strategy(PIIType.ADDRESS),
                    )
                )

        # Sort matches by position (reverse order for replacement)
        matches.sort(key=lambda x: x.start_position, reverse=True)

        return matches

    def mask_pii(
        self,
        text: str,
        masking_strategies: Optional[Dict[PIIType, MaskingStrategy]] = None,
    ) -> PIIMaskingResult:
        """Mask PII in text"""
        matches = self.detect_pii(text)
        masked_text = text
        audit_trail = []

        # Apply masking strategies
        for match in matches:
            strategy = (
                masking_strategies.get(match.pii_type, match.masking_strategy)
                if masking_strategies
                else match.masking_strategy
            )

            masked_value = self._apply_masking_strategy(
                match.original_value, strategy, match.pii_type
            )
            match.masked_value = masked_value

            # Replace in text
            masked_text = (
                masked_text[: match.start_position]
                + masked_value
                + masked_text[match.end_position :]
            )

            # Update audit trail
            audit_trail.append(
                {
                    'timestamp': datetime.utcnow().isoformat(),
                    'pii_type': match.pii_type.value,
                    'original_value': match.original_value,
                    'masked_value': masked_value,
                    'strategy': strategy.value,
                    'confidence': match.confidence,
                    'position': f"{match.start_position}-{match.end_position}",
                }
            )

        return PIIMaskingResult(
            original_text=text,
            masked_text=masked_text,
            matches=matches,
            total_matches=len(matches),
            masking_applied=len(matches) > 0,
            audit_trail=audit_trail,
        )

    def _calculate_confidence(self, pii_type: PIIType, value: str) -> float:
        """Calculate confidence score for PII detection"""
        confidence_map = {
            PIIType.EMAIL: 0.95,
            PIIType.PHONE: 0.90,
            PIIType.CREDIT_CARD: 0.98,
            PIIType.SSN: 0.95,
            PIIType.IP_ADDRESS: 0.90,
            PIIType.MAC_ADDRESS: 0.95,
            PIIType.DATE_OF_BIRTH: 0.85,
            PIIType.USER_ID: 0.80,
            PIIType.CORRELATION_ID: 0.99,
            PIIType.NAME: 0.70,
            PIIType.ADDRESS: 0.75,
        }

        base_confidence = confidence_map.get(pii_type, 0.50)

        # Adjust confidence based on value characteristics
        if pii_type == PIIType.EMAIL:
            if '@' in value and '.' in value.split('@')[1]:
                return min(base_confidence + 0.05, 1.0)

        elif pii_type == PIIType.PHONE:
            digits = sum(1 for c in value if c.isdigit())
            if 10 <= digits <= 11:
                return min(base_confidence + 0.05, 1.0)

        elif pii_type == PIIType.CREDIT_CARD:
            # Luhn algorithm check
            if self._is_valid_credit_card(value):
                return min(base_confidence + 0.02, 1.0)

        return base_confidence

    def _is_valid_credit_card(self, card_number: str) -> bool:
        """Validate credit card number using Luhn algorithm"""
        # Remove non-digits
        digits = [int(d) for d in card_number if d.isdigit()]

        if len(digits) < 13 or len(digits) > 19:
            return False

        # Luhn algorithm
        checksum = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit = digit // 10 + digit % 10
            checksum += digit

        return checksum % 10 == 0

    def _get_masking_strategy(self, pii_type: PIIType) -> MaskingStrategy:
        """Get default masking strategy for PII type"""
        strategy_map = {
            PIIType.EMAIL: MaskingStrategy.HASH,
            PIIType.PHONE: MaskingStrategy.REDACT,
            PIIType.CREDIT_CARD: MaskingStrategy.REDACT,
            PIIType.SSN: MaskingStrategy.REDACT,
            PIIType.IP_ADDRESS: MaskingStrategy.ANONYMIZE,
            PIIType.MAC_ADDRESS: MaskingStrategy.ANONYMIZE,
            PIIType.DATE_OF_BIRTH: MaskingStrategy.REDACT,
            PIIType.USER_ID: MaskingStrategy.HASH,
            PIIType.CORRELATION_ID: MaskingStrategy.HASH,
            PIIType.NAME: MaskingStrategy.REDACT,
            PIIType.ADDRESS: MaskingStrategy.REDACT,
        }

        return strategy_map.get(pii_type, MaskingStrategy.REDACT)

    def _apply_masking_strategy(
        self, value: str, strategy: MaskingStrategy, pii_type: PIIType
    ) -> str:
        """Apply masking strategy to value"""
        if strategy == MaskingStrategy.REDACT:
            return "[REDACTED]"

        elif strategy == MaskingStrategy.HASH:
            # Create deterministic hash
            salt = f"archbuilder_{pii_type.value}"
            hash_obj = hashlib.sha256(f"{salt}{value}".encode())
            return f"hash_{hash_obj.hexdigest()[:16]}"

        elif strategy == MaskingStrategy.ANONYMIZE:
            if pii_type == PIIType.IP_ADDRESS:
                # Anonymize IP address (remove last octet)
                parts = value.split('.')
                if len(parts) == 4:
                    return f"{parts[0]}.{parts[1]}.{parts[2]}.xxx"

            elif pii_type == PIIType.MAC_ADDRESS:
                # Anonymize MAC address (replace with random)
                return "xx:xx:xx:xx:xx:xx"

            return "[ANONYMIZED]"

        elif strategy == MaskingStrategy.TOKENIZE:
            # Generate token
            token = f"token_{hash(value) % 1000000:06d}"
            return token

        elif strategy == MaskingStrategy.REMOVE:
            return ""

        else:
            return "[MASKED]"


class DataAnonymizer:
    """Data anonymization service for ArchBuilder.AI"""

    def __init__(self):
        self.pii_masker = PIIMasker()
        self._anonymization_cache: Dict[str, str] = {}

    def anonymize_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize user data dictionary"""
        anonymized_data = {}

        for key, value in user_data.items():
            if isinstance(value, str):
                # Check if key suggests PII
                if any(
                    pii_indicator in key.lower()
                    for pii_indicator in [
                        'email',
                        'phone',
                        'name',
                        'address',
                        'ssn',
                        'id',
                    ]
                ):
                    masking_result = self.pii_masker.mask_pii(value)
                    anonymized_data[key] = masking_result.masked_text
                else:
                    anonymized_data[key] = value
            elif isinstance(value, dict):
                anonymized_data[key] = self.anonymize_user_data(value)
            elif isinstance(value, list):
                anonymized_data[key] = [
                    self.anonymize_user_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                anonymized_data[key] = value

        return anonymized_data

    def anonymize_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize log entry"""
        anonymized_entry = log_entry.copy()

        # Fields that commonly contain PII
        pii_fields = [
            'user_id',
            'email',
            'username',
            'ip_address',
            'user_agent',
            'request_data',
            'response_data',
        ]

        for field in pii_fields:
            if field in anonymized_entry and isinstance(anonymized_entry[field], str):
                masking_result = self.pii_masker.mask_pii(anonymized_entry[field])
                anonymized_entry[field] = masking_result.masked_text

        return anonymized_entry

    def create_anonymized_dataset(
        self, dataset: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create anonymized version of dataset"""
        anonymized_dataset = []

        for record in dataset:
            anonymized_record = self.anonymize_user_data(record)
            anonymized_dataset.append(anonymized_record)

        return anonymized_dataset


# Global instances
_pii_masker: Optional[PIIMasker] = None
_data_anonymizer: Optional[DataAnonymizer] = None


def initialize_pii_masking() -> None:
    """Initialize global PII masking instances"""
    global _pii_masker, _data_anonymizer

    _pii_masker = PIIMasker()
    _data_anonymizer = DataAnonymizer()


def get_pii_masker() -> PIIMasker:
    """Get global PII masker instance"""
    if _pii_masker is None:
        raise RuntimeError("PII masker not initialized")
    return _pii_masker


def get_data_anonymizer() -> DataAnonymizer:
    """Get global data anonymizer instance"""
    if _data_anonymizer is None:
        raise RuntimeError("Data anonymizer not initialized")
    return _data_anonymizer
