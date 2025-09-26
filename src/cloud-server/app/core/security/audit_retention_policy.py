"""
Audit Retention Policy for ArchBuilder.AI
Audit retention policy - P44-T3
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import structlog
from pathlib import Path
import asyncio
import aiofiles
import hashlib

logger = structlog.get_logger(__name__)


class RetentionPeriod(Enum):
    """Retention periods for different data types"""
    IMMEDIATE = "immediate"  # Delete immediately
    SHORT_TERM = "short_term"  # 30 days
    MEDIUM_TERM = "medium_term"  # 1 year
    LONG_TERM = "long_term"  # 7 years
    PERMANENT = "permanent"  # Never delete


class DataClassification(Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class AuditEventType(Enum):
    """Types of audit events"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    AI_COMMAND = "ai_command"
    AI_RESPONSE = "ai_response"
    PROJECT_CREATE = "project_create"
    PROJECT_UPDATE = "project_update"
    PROJECT_DELETE = "project_delete"
    SUBSCRIPTION_CHANGE = "subscription_change"
    PAYMENT_PROCESSED = "payment_processed"
    SECURITY_VIOLATION = "security_violation"
    DATA_EXPORT = "data_export"
    ADMIN_ACTION = "admin_action"


@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    event_type: AuditEventType
    user_id: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    resource_id: Optional[str]
    action: str
    details: Dict[str, Any]
    data_classification: DataClassification
    retention_period: RetentionPeriod
    created_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class RetentionRule:
    """Retention rule configuration"""
    event_types: List[AuditEventType]
    data_classifications: List[DataClassification]
    retention_period: RetentionPeriod
    conditions: Dict[str, Any]  # Additional conditions
    description: str


@dataclass
class RetentionPolicy:
    """Audit retention policy configuration"""
    policy_name: str
    version: str
    effective_date: datetime
    rules: List[RetentionRule]
    default_retention: RetentionPeriod
    compliance_requirements: List[str]
    data_protection_regulations: List[str]


class AuditRetentionManager:
    """Manages audit data retention policies"""
    
    def __init__(self):
        self.policy = self._create_default_policy()
        self.audit_events: List[AuditEvent] = []
        
    def _create_default_policy(self) -> RetentionPolicy:
        """Create default retention policy"""
        rules = [
            # Security events - long term retention
            RetentionRule(
                event_types=[AuditEventType.SECURITY_VIOLATION, AuditEventType.USER_LOGIN, AuditEventType.USER_LOGOUT],
                data_classifications=[DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED],
                retention_period=RetentionPeriod.LONG_TERM,
                conditions={"security_incident": True},
                description="Security-related events retained for 7 years"
            ),
            
            # Financial events - long term retention
            RetentionRule(
                event_types=[AuditEventType.PAYMENT_PROCESSED, AuditEventType.SUBSCRIPTION_CHANGE],
                data_classifications=[DataClassification.CONFIDENTIAL],
                retention_period=RetentionPeriod.LONG_TERM,
                conditions={},
                description="Financial events retained for 7 years for compliance"
            ),
            
            # AI operations - medium term retention
            RetentionRule(
                event_types=[AuditEventType.AI_COMMAND, AuditEventType.AI_RESPONSE],
                data_classifications=[DataClassification.INTERNAL, DataClassification.CONFIDENTIAL],
                retention_period=RetentionPeriod.MEDIUM_TERM,
                conditions={"ai_model_used": True},
                description="AI operations retained for 1 year for model improvement"
            ),
            
            # File operations - medium term retention
            RetentionRule(
                event_types=[AuditEventType.FILE_UPLOAD, AuditEventType.FILE_DOWNLOAD],
                data_classifications=[DataClassification.INTERNAL, DataClassification.CONFIDENTIAL],
                retention_period=RetentionPeriod.MEDIUM_TERM,
                conditions={},
                description="File operations retained for 1 year"
            ),
            
            # Project operations - medium term retention
            RetentionRule(
                event_types=[AuditEventType.PROJECT_CREATE, AuditEventType.PROJECT_UPDATE, AuditEventType.PROJECT_DELETE],
                data_classifications=[DataClassification.INTERNAL, DataClassification.CONFIDENTIAL],
                retention_period=RetentionPeriod.MEDIUM_TERM,
                conditions={},
                description="Project operations retained for 1 year"
            ),
            
            # Data exports - short term retention
            RetentionRule(
                event_types=[AuditEventType.DATA_EXPORT],
                data_classifications=[DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED],
                retention_period=RetentionPeriod.SHORT_TERM,
                conditions={},
                description="Data exports retained for 30 days"
            ),
            
            # Admin actions - long term retention
            RetentionRule(
                event_types=[AuditEventType.ADMIN_ACTION],
                data_classifications=[DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED],
                retention_period=RetentionPeriod.LONG_TERM,
                conditions={},
                description="Admin actions retained for 7 years"
            )
        ]
        
        return RetentionPolicy(
            policy_name="ArchBuilder.AI Audit Retention Policy",
            version="1.0",
            effective_date=datetime.utcnow(),
            rules=rules,
            default_retention=RetentionPeriod.MEDIUM_TERM,
            compliance_requirements=["GDPR", "CCPA", "SOX", "HIPAA"],
            data_protection_regulations=["EU GDPR", "California CCPA", "EU-US Privacy Shield"]
        )
    
    def determine_retention_period(self, event: AuditEvent) -> RetentionPeriod:
        """Determine retention period for an audit event"""
        for rule in self.policy.rules:
            if self._matches_rule(event, rule):
                return rule.retention_period
        
        return self.policy.default_retention
    
    def _matches_rule(self, event: AuditEvent, rule: RetentionRule) -> bool:
        """Check if event matches a retention rule"""
        # Check event type
        if event.event_type not in rule.event_types:
            return False
        
        # Check data classification
        if event.data_classification not in rule.data_classifications:
            return False
        
        # Check additional conditions
        for condition_key, condition_value in rule.conditions.items():
            if condition_key not in event.details:
                return False
            if event.details[condition_key] != condition_value:
                return False
        
        return True
    
    def calculate_expiration_date(self, event: AuditEvent) -> Optional[datetime]:
        """Calculate expiration date for an audit event"""
        retention_period = self.determine_retention_period(event)
        
        if retention_period == RetentionPeriod.IMMEDIATE:
            return event.timestamp  # Expire immediately
        elif retention_period == RetentionPeriod.SHORT_TERM:
            return event.timestamp + timedelta(days=30)
        elif retention_period == RetentionPeriod.MEDIUM_TERM:
            return event.timestamp + timedelta(days=365)
        elif retention_period == RetentionPeriod.LONG_TERM:
            return event.timestamp + timedelta(days=2555)  # 7 years
        elif retention_period == RetentionPeriod.PERMANENT:
            return None  # Never expire
        
        return None
    
    async def add_audit_event(self, event: AuditEvent) -> None:
        """Add an audit event to the system"""
        # Calculate expiration date
        event.expires_at = self.calculate_expiration_date(event)
        
        # Add to audit events
        self.audit_events.append(event)
        
        logger.info(
            "Audit event added",
            event_id=event.event_id,
            event_type=event.event_type.value,
            user_id=event.user_id,
            retention_period=event.retention_period.value,
            expires_at=event.expires_at.isoformat() if event.expires_at else None
        )
    
    async def get_expired_events(self) -> List[AuditEvent]:
        """Get events that have expired and should be deleted"""
        now = datetime.utcnow()
        expired_events = [
            event for event in self.audit_events
            if event.expires_at is not None and event.expires_at <= now
        ]
        
        return expired_events
    
    async def cleanup_expired_events(self) -> Dict[str, Any]:
        """Clean up expired audit events"""
        expired_events = await self.get_expired_events()
        
        if not expired_events:
            return {
                "cleaned_events": 0,
                "remaining_events": len(self.audit_events),
                "cleanup_timestamp": datetime.utcnow().isoformat()
            }
        
        # Remove expired events
        self.audit_events = [
            event for event in self.audit_events
            if event not in expired_events
        ]
        
        # Log cleanup
        logger.info(
            "Audit events cleaned up",
            cleaned_events=len(expired_events),
            remaining_events=len(self.audit_events)
        )
        
        return {
            "cleaned_events": len(expired_events),
            "remaining_events": len(self.audit_events),
            "cleanup_timestamp": datetime.utcnow().isoformat(),
            "expired_event_ids": [event.event_id for event in expired_events]
        }
    
    async def get_retention_report(self) -> Dict[str, Any]:
        """Generate retention policy report"""
        now = datetime.utcnow()
        
        # Categorize events by retention period
        events_by_retention = {}
        for retention_period in RetentionPeriod:
            events_by_retention[retention_period.value] = []
        
        for event in self.audit_events:
            retention_period = self.determine_retention_period(event)
            events_by_retention[retention_period.value].append(event)
        
        # Calculate statistics
        total_events = len(self.audit_events)
        events_expiring_soon = [
            event for event in self.audit_events
            if event.expires_at and event.expires_at <= now + timedelta(days=30)
        ]
        
        # Calculate storage usage (estimated)
        estimated_storage_mb = total_events * 0.001  # 1KB per event estimate
        
        return {
            "policy_info": {
                "name": self.policy.policy_name,
                "version": self.policy.version,
                "effective_date": self.policy.effective_date.isoformat(),
                "compliance_requirements": self.policy.compliance_requirements,
                "data_protection_regulations": self.policy.data_protection_regulations
            },
            "current_status": {
                "total_events": total_events,
                "events_expiring_soon": len(events_expiring_soon),
                "estimated_storage_mb": estimated_storage_mb
            },
            "events_by_retention": {
                retention: len(events) for retention, events in events_by_retention.items()
            },
            "retention_rules": [
                {
                    "event_types": [event_type.value for event_type in rule.event_types],
                    "data_classifications": [classification.value for classification in rule.data_classifications],
                    "retention_period": rule.retention_period.value,
                    "description": rule.description
                }
                for rule in self.policy.rules
            ]
        }
    
    async def export_audit_data(self, start_date: datetime, end_date: datetime, 
                              event_types: Optional[List[AuditEventType]] = None) -> Dict[str, Any]:
        """Export audit data for compliance purposes"""
        # Filter events by date range
        filtered_events = [
            event for event in self.audit_events
            if start_date <= event.timestamp <= end_date
        ]
        
        # Filter by event types if specified
        if event_types:
            filtered_events = [
                event for event in filtered_events
                if event.event_type in event_types
            ]
        
        # Create export data
        export_data = {
            "export_info": {
                "export_timestamp": datetime.utcnow().isoformat(),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "event_types": [event_type.value for event_type in event_types] if event_types else "all",
                "total_events": len(filtered_events)
            },
            "events": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "user_id": event.user_id,
                    "timestamp": event.timestamp.isoformat(),
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "resource_id": event.resource_id,
                    "action": event.action,
                    "details": event.details,
                    "data_classification": event.data_classification.value,
                    "retention_period": event.retention_period.value,
                    "expires_at": event.expires_at.isoformat() if event.expires_at else None
                }
                for event in filtered_events
            ]
        }
        
        return export_data
    
    async def anonymize_old_events(self, anonymization_threshold_days: int = 365) -> Dict[str, Any]:
        """Anonymize old events while preserving audit trail"""
        threshold_date = datetime.utcnow() - timedelta(days=anonymization_threshold_days)
        
        old_events = [
            event for event in self.audit_events
            if event.timestamp < threshold_date
        ]
        
        anonymized_count = 0
        
        for event in old_events:
            # Anonymize sensitive data
            event.user_id = f"ANONYMIZED_{hashlib.md5(event.user_id.encode()).hexdigest()[:8]}"
            event.ip_address = "ANONYMIZED"
            event.user_agent = "ANONYMIZED"
            
            # Remove sensitive details
            if "password" in event.details:
                del event.details["password"]
            if "api_key" in event.details:
                del event.details["api_key"]
            if "token" in event.details:
                del event.details["token"]
            
            anonymized_count += 1
        
        logger.info(
            "Events anonymized",
            anonymized_count=anonymized_count,
            threshold_days=anonymization_threshold_days
        )
        
        return {
            "anonymized_events": anonymized_count,
            "threshold_days": anonymization_threshold_days,
            "anonymization_timestamp": datetime.utcnow().isoformat()
        }


class ComplianceReporter:
    """Generates compliance reports for audit retention"""
    
    def __init__(self, retention_manager: AuditRetentionManager):
        self.retention_manager = retention_manager
    
    async def generate_gdpr_report(self) -> Dict[str, Any]:
        """Generate GDPR compliance report"""
        # Get events that contain personal data
        personal_data_events = [
            event for event in self.retention_manager.audit_events
            if event.data_classification in [DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED]
        ]
        
        # Calculate retention compliance
        compliant_events = 0
        non_compliant_events = 0
        
        for event in personal_data_events:
            if event.retention_period in [RetentionPeriod.SHORT_TERM, RetentionPeriod.MEDIUM_TERM]:
                compliant_events += 1
            else:
                non_compliant_events += 1
        
        return {
            "report_type": "GDPR Compliance Report",
            "generated_at": datetime.utcnow().isoformat(),
            "personal_data_events": len(personal_data_events),
            "compliant_events": compliant_events,
            "non_compliant_events": non_compliant_events,
            "compliance_rate": compliant_events / len(personal_data_events) if personal_data_events else 1.0,
            "recommendations": [
                "Ensure all personal data events have appropriate retention periods",
                "Regularly review and update retention policies",
                "Implement data minimization principles"
            ]
        }
    
    async def generate_sox_report(self) -> Dict[str, Any]:
        """Generate SOX compliance report"""
        # Get financial events
        financial_events = [
            event for event in self.retention_manager.audit_events
            if event.event_type in [AuditEventType.PAYMENT_PROCESSED, AuditEventType.SUBSCRIPTION_CHANGE]
        ]
        
        # Check retention compliance
        long_term_retained = len([
            event for event in financial_events
            if event.retention_period == RetentionPeriod.LONG_TERM
        ])
        
        return {
            "report_type": "SOX Compliance Report",
            "generated_at": datetime.utcnow().isoformat(),
            "financial_events": len(financial_events),
            "long_term_retained": long_term_retained,
            "compliance_rate": long_term_retained / len(financial_events) if financial_events else 1.0,
            "requirements_met": long_term_retained == len(financial_events),
            "recommendations": [
                "Ensure all financial events are retained for 7 years",
                "Maintain audit trail integrity",
                "Regular compliance monitoring"
            ]
        }


# Global instances
_retention_manager = AuditRetentionManager()
_compliance_reporter = ComplianceReporter(_retention_manager)


async def add_audit_event(event: AuditEvent) -> None:
    """Add an audit event"""
    await _retention_manager.add_audit_event(event)


async def cleanup_expired_audit_events() -> Dict[str, Any]:
    """Clean up expired audit events"""
    return await _retention_manager.cleanup_expired_events()


async def get_retention_report() -> Dict[str, Any]:
    """Get retention policy report"""
    return await _retention_manager.get_retention_report()


async def generate_compliance_report(regulation: str) -> Dict[str, Any]:
    """Generate compliance report for specific regulation"""
    if regulation.upper() == "GDPR":
        return await _compliance_reporter.generate_gdpr_report()
    elif regulation.upper() == "SOX":
        return await _compliance_reporter.generate_sox_report()
    else:
        return {"error": f"Unsupported regulation: {regulation}"}



