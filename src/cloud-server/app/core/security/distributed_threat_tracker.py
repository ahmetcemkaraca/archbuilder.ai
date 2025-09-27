"""
Distributed Security Threat Tracking for ArchBuilder.AI

This module provides Redis-based threat tracking to replace
in-memory tracking for production environments with multiple workers.
"""

import time
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


class DistributedThreatTracker:
    """Redis-based threat tracking for production environments"""

    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "threat_tracker"):
        """Initialize distributed threat tracker"""
        self.prefix = prefix
        self.redis_client = None

        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                logger.info("Redis threat tracker initialized successfully")
            except Exception as e:
                logger.warning("Failed to connect to Redis: %s. Falling back to in-memory tracking", e)
                self.redis_client = None
        else:
            logger.warning("Redis not available. Using in-memory threat tracking")

        # Fallback in-memory storage
        self.memory_storage: Dict[str, float] = {}

    def track_request(self, client_ip: str) -> float:
        """Track request and return threat score increment"""
        current_time = time.time()
        key = f"{self.prefix}:ip:{client_ip}"

        if self.redis_client:
            try:
                # Get last request time
                last_request_data = self.redis_client.get(key)

                if last_request_data:
                    last_request = float(last_request_data)
                    time_diff = current_time - last_request

                    # Calculate threat score based on request frequency
                    if time_diff < 1.0:  # Less than 1 second
                        threat_increment = 0.3
                    elif time_diff < 5.0:  # Less than 5 seconds
                        threat_increment = 0.1
                    else:
                        threat_increment = 0.0
                else:
                    threat_increment = 0.0

                # Update last request time with expiration (1 hour)
                self.redis_client.setex(key, 3600, current_time)

                return threat_increment

            except Exception as e:
                logger.error("Redis operation failed: %s. Using fallback", e)
                return self._fallback_track_request(client_ip, current_time)
        else:
            return self._fallback_track_request(client_ip, current_time)

    def _fallback_track_request(self, client_ip: str, current_time: float) -> float:
        """Fallback in-memory request tracking"""
        if client_ip in self.memory_storage:
            last_request = self.memory_storage[client_ip]
            time_diff = current_time - last_request

            if time_diff < 1.0:
                threat_increment = 0.3
            elif time_diff < 5.0:
                threat_increment = 0.1
            else:
                threat_increment = 0.0
        else:
            threat_increment = 0.0

        self.memory_storage[client_ip] = current_time
        return threat_increment

    def get_ip_threat_history(self, client_ip: str, hours: int = 24) -> Dict[str, Any]:
        """Get threat history for an IP address"""
        key = f"{self.prefix}:history:{client_ip}"

        if self.redis_client:
            try:
                history_data = self.redis_client.get(key)
                if history_data:
                    return json.loads(history_data)
            except Exception as e:
                logger.error("Failed to get threat history: %s", e)

        return {"total_requests": 0, "threat_events": 0, "first_seen": None}

    def record_threat_event(self, client_ip: str, threat_type: str, severity: float):
        """Record a threat event for tracking"""
        key = f"{self.prefix}:history:{client_ip}"
        current_time = datetime.utcnow().isoformat()

        if self.redis_client:
            try:
                # Get existing history
                history_data = self.redis_client.get(key)
                if history_data:
                    history = json.loads(history_data)
                else:
                    history = {
                        "total_requests": 0,
                        "threat_events": 0,
                        "first_seen": current_time,
                        "events": []
                    }

                # Add new threat event
                history["threat_events"] += 1
                history["events"].append({
                    "timestamp": current_time,
                    "type": threat_type,
                    "severity": severity
                })

                # Keep only last 100 events
                if len(history["events"]) > 100:
                    history["events"] = history["events"][-100:]

                # Store with 7 day expiration
                self.redis_client.setex(key, 7 * 24 * 3600, json.dumps(history))

            except Exception as e:
                logger.error("Failed to record threat event: %s", e)

    def cleanup_old_entries(self):
        """Clean up old entries (call periodically)"""
        if not self.redis_client:
            # Clean in-memory storage
            current_time = time.time()
            expired_keys = [
                ip for ip, timestamp in self.memory_storage.items()
                if current_time - timestamp > 3600  # 1 hour
            ]
            for key in expired_keys:
                del self.memory_storage[key]

            logger.info("Cleaned %d expired in-memory entries", len(expired_keys))


# Global instance
_threat_tracker: Optional[DistributedThreatTracker] = None


def get_threat_tracker(redis_url: str = "redis://localhost:6379") -> DistributedThreatTracker:
    """Get global threat tracker instance"""
    global _threat_tracker  # noqa: PLW0603
    if _threat_tracker is None:
        _threat_tracker = DistributedThreatTracker(redis_url)
    return _threat_tracker


def initialize_threat_tracker(redis_url: str = "redis://localhost:6379"):
    """Initialize the global threat tracker"""
    global _threat_tracker  # noqa: PLW0603
    _threat_tracker = DistributedThreatTracker(redis_url)
