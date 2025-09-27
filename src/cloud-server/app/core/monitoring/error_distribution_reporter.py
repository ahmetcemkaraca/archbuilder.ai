"""
Error Distribution Reporter for ArchBuilder.AI
Error distribution reports - P45-T3
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import structlog
from collections import defaultdict, Counter
import statistics

logger = structlog.get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    AI_SERVICE = "ai_service"
    DATABASE = "database"
    NETWORK = "network"
    FILE_PROCESSING = "file_processing"
    RAG_SYSTEM = "rag_system"
    BILLING = "billing"
    SECURITY = "security"
    UNKNOWN = "unknown"


@dataclass
class ErrorEvent:
    """Error event data structure"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    error_code: str
    error_message: str
    user_id: Optional[str]
    session_id: Optional[str]
    request_id: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    status_code: Optional[int]
    stack_trace: Optional[str]
    context: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class ErrorDistribution:
    """Error distribution statistics"""
    total_errors: int
    errors_by_severity: Dict[str, int]
    errors_by_category: Dict[str, int]
    errors_by_endpoint: Dict[str, int]
    errors_by_status_code: Dict[str, int]
    errors_by_user: Dict[str, int]
    time_distribution: Dict[str, int]
    resolution_stats: Dict[str, Any]


@dataclass
class ErrorTrend:
    """Error trend analysis"""
    period: str
    total_errors: int
    error_rate: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    peak_errors: int
    peak_timestamp: datetime
    resolution_rate: float
    avg_resolution_time: float


class ErrorDistributionReporter:
    """Generates error distribution reports"""
    
    def __init__(self):
        self.error_events: List[ErrorEvent] = []
        self.error_patterns: Dict[str, List[ErrorEvent]] = defaultdict(list)
        
    async def add_error_event(self, error_event: ErrorEvent) -> None:
        """Add an error event to the system"""
        self.error_events.append(error_event)
        
        # Group by error pattern
        pattern_key = f"{error_event.category.value}_{error_event.error_code}"
        self.error_patterns[pattern_key].append(error_event)
        
        logger.info(
            "Error event recorded",
            error_id=error_event.error_id,
            severity=error_event.severity.value,
            category=error_event.category.value,
            error_code=error_event.error_code
        )
    
    async def generate_distribution_report(self, start_date: datetime, end_date: datetime) -> ErrorDistribution:
        """Generate error distribution report for a time period"""
        # Filter errors by date range
        filtered_errors = [
            error for error in self.error_events
            if start_date <= error.timestamp <= end_date
        ]
        
        if not filtered_errors:
            return ErrorDistribution(
                total_errors=0,
                errors_by_severity={},
                errors_by_category={},
                errors_by_endpoint={},
                errors_by_status_code={},
                errors_by_user={},
                time_distribution={},
                resolution_stats={}
            )
        
        # Calculate distributions
        errors_by_severity = Counter(error.severity.value for error in filtered_errors)
        errors_by_category = Counter(error.category.value for error in filtered_errors)
        errors_by_endpoint = Counter(error.endpoint for error in filtered_errors if error.endpoint)
        errors_by_status_code = Counter(str(error.status_code) for error in filtered_errors if error.status_code)
        errors_by_user = Counter(error.user_id for error in filtered_errors if error.user_id)
        
        # Time distribution (by hour)
        time_distribution = defaultdict(int)
        for error in filtered_errors:
            hour = error.timestamp.hour
            time_distribution[f"{hour:02d}:00"] += 1
        
        # Resolution statistics
        resolved_errors = [error for error in filtered_errors if error.resolved]
        resolution_times = []
        for error in resolved_errors:
            if error.resolution_time:
                resolution_time = (error.resolution_time - error.timestamp).total_seconds()
                resolution_times.append(resolution_time)
        
        resolution_stats = {
            "total_resolved": len(resolved_errors),
            "resolution_rate": len(resolved_errors) / len(filtered_errors) if filtered_errors else 0,
            "avg_resolution_time_seconds": statistics.mean(resolution_times) if resolution_times else 0,
            "median_resolution_time_seconds": statistics.median(resolution_times) if resolution_times else 0
        }
        
        return ErrorDistribution(
            total_errors=len(filtered_errors),
            errors_by_severity=dict(errors_by_severity),
            errors_by_category=dict(errors_by_category),
            errors_by_endpoint=dict(errors_by_endpoint),
            errors_by_status_code=dict(errors_by_status_code),
            errors_by_user=dict(errors_by_user),
            time_distribution=dict(time_distribution),
            resolution_stats=resolution_stats
        )
    
    async def generate_trend_analysis(self, days: int = 30) -> List[ErrorTrend]:
        """Generate error trend analysis"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        trends = []
        
        # Analyze daily trends
        current_date = start_date
        while current_date < end_date:
            next_date = current_date + timedelta(days=1)
            
            daily_errors = [
                error for error in self.error_events
                if current_date <= error.timestamp < next_date
            ]
            
            if daily_errors:
                # Calculate trend direction
                prev_day_errors = [
                    error for error in self.error_errors
                    if current_date - timedelta(days=1) <= error.timestamp < current_date
                ]
                
                if len(daily_errors) > len(prev_day_errors):
                    trend_direction = "increasing"
                elif len(daily_errors) < len(prev_day_errors):
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
                
                # Find peak errors
                peak_errors = max(len(daily_errors), 0)
                peak_timestamp = max(error.timestamp for error in daily_errors) if daily_errors else current_date
                
                # Calculate resolution rate
                resolved_count = sum(1 for error in daily_errors if error.resolved)
                resolution_rate = resolved_count / len(daily_errors) if daily_errors else 0
                
                # Calculate average resolution time
                resolution_times = []
                for error in daily_errors:
                    if error.resolved and error.resolution_time:
                        resolution_time = (error.resolution_time - error.timestamp).total_seconds()
                        resolution_times.append(resolution_time)
                
                avg_resolution_time = statistics.mean(resolution_times) if resolution_times else 0
                
                trend = ErrorTrend(
                    period=current_date.strftime("%Y-%m-%d"),
                    total_errors=len(daily_errors),
                    error_rate=len(daily_errors) / 86400,  # errors per second
                    trend_direction=trend_direction,
                    peak_errors=peak_errors,
                    peak_timestamp=peak_timestamp,
                    resolution_rate=resolution_rate,
                    avg_resolution_time=avg_resolution_time
                )
                
                trends.append(trend)
            
            current_date = next_date
        
        return trends
    
    async def generate_top_errors_report(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Generate report of top errors by frequency"""
        error_counts = Counter()
        error_details = {}
        
        for error in self.error_errors:
            key = f"{error.category.value}_{error.error_code}"
            error_counts[key] += 1
            
            if key not in error_details:
                error_details[key] = {
                    "category": error.category.value,
                    "error_code": error.error_code,
                    "severity": error.severity.value,
                    "first_occurrence": error.timestamp,
                    "last_occurrence": error.timestamp,
                    "sample_message": error.error_message
                }
            else:
                error_details[key]["last_occurrence"] = max(
                    error_details[key]["last_occurrence"], 
                    error.timestamp
                )
        
        # Get top errors
        top_errors = []
        for error_key, count in error_counts.most_common(limit):
            details = error_details[error_key]
            details["count"] = count
            details["frequency"] = count / len(self.error_events) if self.error_events else 0
            top_errors.append(details)
        
        return top_errors
    
    async def generate_user_error_report(self, user_id: str) -> Dict[str, Any]:
        """Generate error report for a specific user"""
        user_errors = [
            error for error in self.error_events
            if error.user_id == user_id
        ]
        
        if not user_errors:
            return {
                "user_id": user_id,
                "total_errors": 0,
                "error_categories": {},
                "error_timeline": [],
                "recommendations": []
            }
        
        # Categorize errors
        error_categories = Counter(error.category.value for error in user_errors)
        
        # Create timeline
        timeline = []
        for error in sorted(user_errors, key=lambda x: x.timestamp):
            timeline.append({
                "timestamp": error.timestamp.isoformat(),
                "category": error.category.value,
                "severity": error.severity.value,
                "error_code": error.error_code,
                "message": error.error_message
            })
        
        # Generate recommendations
        recommendations = []
        if error_categories.get("authentication", 0) > 5:
            recommendations.append("User experiencing authentication issues - consider password reset")
        
        if error_categories.get("validation", 0) > 10:
            recommendations.append("User experiencing validation errors - consider user training")
        
        if error_categories.get("ai_service", 0) > 3:
            recommendations.append("User experiencing AI service issues - check service health")
        
        return {
            "user_id": user_id,
            "total_errors": len(user_errors),
            "error_categories": dict(error_categories),
            "error_timeline": timeline,
            "recommendations": recommendations
        }
    
    async def generate_security_error_report(self) -> Dict[str, Any]:
        """Generate security-focused error report"""
        security_errors = [
            error for error in self.error_events
            if error.category == ErrorCategory.SECURITY or error.severity == ErrorSeverity.CRITICAL
        ]
        
        if not security_errors:
            return {
                "total_security_errors": 0,
                "critical_errors": 0,
                "security_trends": {},
                "threat_indicators": []
            }
        
        # Analyze security trends
        security_trends = defaultdict(int)
        for error in security_errors:
            hour = error.timestamp.hour
            security_trends[f"{hour:02d}:00"] += 1
        
        # Identify threat indicators
        threat_indicators = []
        
        # Check for brute force attempts
        auth_errors = [error for error in security_errors if error.category == ErrorCategory.AUTHENTICATION]
        if len(auth_errors) > 10:
            threat_indicators.append("Potential brute force attack detected")
        
        # Check for suspicious patterns
        error_ips = Counter(error.context.get("ip_address") for error in security_errors if error.context.get("ip_address"))
        if len(error_ips) > 5:
            threat_indicators.append("Multiple IP addresses involved in security errors")
        
        # Check for rapid error escalation
        recent_errors = [
            error for error in security_errors
            if error.timestamp > datetime.utcnow() - timedelta(hours=1)
        ]
        if len(recent_errors) > 5:
            threat_indicators.append("Rapid escalation of security errors in the last hour")
        
        return {
            "total_security_errors": len(security_errors),
            "critical_errors": len([error for error in security_errors if error.severity == ErrorSeverity.CRITICAL]),
            "security_trends": dict(security_trends),
            "threat_indicators": threat_indicators
        }
    
    async def generate_comprehensive_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive error distribution report"""
        # Generate all report components
        distribution = await self.generate_distribution_report(start_date, end_date)
        trends = await self.generate_trend_analysis((end_date - start_date).days)
        top_errors = await self.generate_top_errors_report()
        security_report = await self.generate_security_error_report()
        
        # Calculate additional metrics
        total_errors = len(self.error_events)
        error_rate = total_errors / ((end_date - start_date).total_seconds() / 3600)  # errors per hour
        
        # Error severity breakdown
        severity_breakdown = {
            "critical": len([e for e in self.error_events if e.severity == ErrorSeverity.CRITICAL]),
            "high": len([e for e in self.error_events if e.severity == ErrorSeverity.HIGH]),
            "medium": len([e for e in self.error_events if e.severity == ErrorSeverity.MEDIUM]),
            "low": len([e for e in self.error_events if e.severity == ErrorSeverity.LOW])
        }
        
        # Generate recommendations
        recommendations = []
        
        if severity_breakdown["critical"] > 0:
            recommendations.append("Address critical errors immediately")
        
        if distribution.resolution_stats["resolution_rate"] < 0.8:
            recommendations.append("Improve error resolution rate")
        
        if security_report["threat_indicators"]:
            recommendations.append("Investigate security threats")
        
        return {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_errors_analyzed": total_errors
            },
            "summary": {
                "total_errors": distribution.total_errors,
                "error_rate_per_hour": error_rate,
                "severity_breakdown": severity_breakdown,
                "resolution_rate": distribution.resolution_stats["resolution_rate"]
            },
            "distribution": asdict(distribution),
            "trends": [asdict(trend) for trend in trends],
            "top_errors": top_errors,
            "security_analysis": security_report,
            "recommendations": recommendations
        }
    
    async def export_report(self, report: Dict[str, Any], format: str = "json") -> str:
        """Export report in specified format"""
        if format == "json":
            return json.dumps(report, indent=2, default=str)
        elif format == "csv":
            # Convert to CSV format (simplified)
            csv_data = []
            for error in self.error_events:
                csv_data.append({
                    "timestamp": error.timestamp.isoformat(),
                    "severity": error.severity.value,
                    "category": error.category.value,
                    "error_code": error.error_code,
                    "user_id": error.user_id,
                    "endpoint": error.endpoint,
                    "status_code": error.status_code
                })
            return json.dumps(csv_data, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global error reporter instance
_error_reporter = ErrorDistributionReporter()


async def record_error_event(error_event: ErrorEvent) -> None:
    """Record an error event"""
    await _error_reporter.add_error_event(error_event)


async def generate_error_distribution_report(start_date: datetime, end_date: datetime) -> ErrorDistribution:
    """Generate error distribution report"""
    return await _error_reporter.generate_distribution_report(start_date, end_date)


async def generate_comprehensive_error_report(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate comprehensive error report"""
    return await _error_reporter.generate_comprehensive_report(start_date, end_date)


async def generate_user_error_report(user_id: str) -> Dict[str, Any]:
    """Generate user-specific error report"""
    return await _error_reporter.generate_user_error_report(user_id)


async def generate_security_error_report() -> Dict[str, Any]:
    """Generate security-focused error report"""
    return await _error_reporter.generate_security_error_report()

