"""
WebSocket Scaling and Connection Management for ArchBuilder.AI

Provides:
- Scalable WebSocket connection management
- Connection pooling and load balancing
- Message broadcasting and routing
- Connection health monitoring
- Auto-scaling support
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass

import structlog
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ConnectionStatus(str, Enum):
    """WebSocket connection status"""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MessageType(str, Enum):
    """WebSocket message types"""

    HEARTBEAT = "heartbeat"
    PROGRESS_UPDATE = "progress_update"
    AI_RESPONSE = "ai_response"
    ERROR = "error"
    NOTIFICATION = "notification"
    SYSTEM_MESSAGE = "system_message"


@dataclass
class ConnectionInfo:
    """WebSocket connection information"""

    connection_id: str
    websocket: WebSocket
    user_id: Optional[str]
    correlation_id: Optional[str]
    status: ConnectionStatus
    connected_at: datetime
    last_activity: datetime
    message_count: int = 0
    error_count: int = 0


class WebSocketMessage(BaseModel):
    """WebSocket message model"""

    type: MessageType
    correlation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebSocketManager:
    """Scalable WebSocket connection manager for ArchBuilder.AI"""

    def __init__(self, max_connections: int = 1000, heartbeat_interval: int = 30):
        self.max_connections = max_connections
        self.heartbeat_interval = heartbeat_interval
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.correlation_connections: Dict[str, Set[str]] = (
            {}
        )  # correlation_id -> connection_ids
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
        }

    async def start(self):
        """Start WebSocket manager services"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("WebSocket manager started")

    async def stop(self):
        """Stop WebSocket manager services"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        # Close all connections
        for connection_info in self.connections.values():
            try:
                await connection_info.websocket.close()
            except Exception:
                pass

        logger.info("WebSocket manager stopped")

    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Accept new WebSocket connection"""
        if len(self.connections) >= self.max_connections:
            await websocket.close(code=1013, reason="Server overloaded")
            raise WebSocketDisconnect("Maximum connections exceeded")

        connection_id = str(uuid.uuid4())

        try:
            await websocket.accept()

            connection_info = ConnectionInfo(
                connection_id=connection_id,
                websocket=websocket,
                user_id=user_id,
                correlation_id=correlation_id,
                status=ConnectionStatus.CONNECTED,
                connected_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
            )

            self.connections[connection_id] = connection_info

            # Track user connections
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(connection_id)

            # Track correlation connections
            if correlation_id:
                if correlation_id not in self.correlation_connections:
                    self.correlation_connections[correlation_id] = set()
                self.correlation_connections[correlation_id].add(connection_id)

            self._stats["total_connections"] += 1
            self._stats["active_connections"] = len(self.connections)

            logger.info(
                "WebSocket connection established",
                connection_id=connection_id,
                user_id=user_id,
                correlation_id=correlation_id,
                total_connections=len(self.connections),
            )

            # Send welcome message
            await self.send_message(
                connection_id,
                WebSocketMessage(
                    type=MessageType.SYSTEM_MESSAGE,
                    correlation_id=correlation_id or "system",
                    payload={"message": "Connected to ArchBuilder.AI WebSocket"},
                ),
            )

            return connection_id

        except Exception as e:
            logger.error("Failed to establish WebSocket connection", error=str(e))
            raise

    async def disconnect(self, connection_id: str):
        """Disconnect WebSocket connection"""
        if connection_id not in self.connections:
            return

        connection_info = self.connections[connection_id]
        connection_info.status = ConnectionStatus.DISCONNECTED

        try:
            await connection_info.websocket.close()
        except Exception:
            pass

        # Remove from tracking
        if connection_info.user_id and connection_info.user_id in self.user_connections:
            self.user_connections[connection_info.user_id].discard(connection_id)
            if not self.user_connections[connection_info.user_id]:
                del self.user_connections[connection_info.user_id]

        if (
            connection_info.correlation_id
            and connection_info.correlation_id in self.correlation_connections
        ):
            self.correlation_connections[connection_info.correlation_id].discard(
                connection_id
            )
            if not self.correlation_connections[connection_info.correlation_id]:
                del self.correlation_connections[connection_info.correlation_id]

        del self.connections[connection_id]
        self._stats["active_connections"] = len(self.connections)

        logger.info(
            "WebSocket connection closed",
            connection_id=connection_id,
            total_connections=len(self.connections),
        )

    async def send_message(self, connection_id: str, message: WebSocketMessage) -> bool:
        """Send message to specific connection"""
        if connection_id not in self.connections:
            return False

        connection_info = self.connections[connection_id]

        if connection_info.status != ConnectionStatus.CONNECTED:
            return False

        try:
            await connection_info.websocket.send_text(message.json())
            connection_info.message_count += 1
            connection_info.last_activity = datetime.utcnow()
            self._stats["messages_sent"] += 1

            return True

        except Exception as e:
            logger.error(
                "Failed to send WebSocket message",
                connection_id=connection_id,
                error=str(e),
            )
            connection_info.error_count += 1
            self._stats["errors"] += 1
            return False

    async def broadcast_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """Broadcast message to all connections for a user"""
        if user_id not in self.user_connections:
            return 0

        sent_count = 0
        for connection_id in self.user_connections[user_id].copy():
            if await self.send_message(connection_id, message):
                sent_count += 1

        logger.info("Broadcast message to user", user_id=user_id, sent_count=sent_count)
        return sent_count

    async def broadcast_to_correlation(
        self, correlation_id: str, message: WebSocketMessage
    ) -> int:
        """Broadcast message to all connections for a correlation ID"""
        if correlation_id not in self.correlation_connections:
            return 0

        sent_count = 0
        for connection_id in self.correlation_connections[correlation_id].copy():
            if await self.send_message(connection_id, message):
                sent_count += 1

        logger.info(
            "Broadcast message to correlation",
            correlation_id=correlation_id,
            sent_count=sent_count,
        )
        return sent_count

    async def broadcast_to_all(self, message: WebSocketMessage) -> int:
        """Broadcast message to all connections"""
        sent_count = 0
        for connection_id in list(self.connections.keys()):
            if await self.send_message(connection_id, message):
                sent_count += 1

        logger.info(
            "Broadcast message to all",
            sent_count=sent_count,
            total_connections=len(self.connections),
        )
        return sent_count

    async def send_progress_update(
        self, correlation_id: str, stage: str, progress: float, message: str = None
    ) -> int:
        """Send progress update to correlation connections"""
        progress_message = WebSocketMessage(
            type=MessageType.PROGRESS_UPDATE,
            correlation_id=correlation_id,
            payload={
                "stage": stage,
                "progress": progress,
                "message": message or f"Processing: {stage}",
            },
        )

        return await self.broadcast_to_correlation(correlation_id, progress_message)

    async def send_ai_response(
        self, correlation_id: str, response: Dict[str, Any]
    ) -> int:
        """Send AI response to correlation connections"""
        ai_message = WebSocketMessage(
            type=MessageType.AI_RESPONSE,
            correlation_id=correlation_id,
            payload=response,
        )

        return await self.broadcast_to_correlation(correlation_id, ai_message)

    async def send_error(
        self, correlation_id: str, error: str, error_code: str = None
    ) -> int:
        """Send error message to correlation connections"""
        error_message = WebSocketMessage(
            type=MessageType.ERROR,
            correlation_id=correlation_id,
            payload={
                "error": error,
                "error_code": error_code,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return await self.broadcast_to_correlation(correlation_id, error_message)

    async def _cleanup_loop(self):
        """Cleanup inactive connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute

                cutoff_time = datetime.utcnow() - timedelta(minutes=5)
                inactive_connections = []

                for connection_id, connection_info in self.connections.items():
                    if (
                        connection_info.last_activity < cutoff_time
                        or connection_info.status == ConnectionStatus.DISCONNECTED
                    ):
                        inactive_connections.append(connection_id)

                for connection_id in inactive_connections:
                    await self.disconnect(connection_id)

                if inactive_connections:
                    logger.info(
                        "Cleaned up inactive connections",
                        count=len(inactive_connections),
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cleanup loop", error=str(e))

    async def _heartbeat_loop(self):
        """Send heartbeat to all connections"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                heartbeat_message = WebSocketMessage(
                    type=MessageType.HEARTBEAT,
                    correlation_id="system",
                    payload={"timestamp": datetime.utcnow().isoformat()},
                )

                await self.broadcast_to_all(heartbeat_message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in heartbeat loop", error=str(e))

    def get_connection_info(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get connection information"""
        return self.connections.get(connection_id)

    def get_user_connections(self, user_id: str) -> List[ConnectionInfo]:
        """Get all connections for a user"""
        if user_id not in self.user_connections:
            return []

        return [
            self.connections[conn_id]
            for conn_id in self.user_connections[user_id]
            if conn_id in self.connections
        ]

    def get_correlation_connections(self, correlation_id: str) -> List[ConnectionInfo]:
        """Get all connections for a correlation ID"""
        if correlation_id not in self.correlation_connections:
            return []

        return [
            self.connections[conn_id]
            for conn_id in self.correlation_connections[correlation_id]
            if conn_id in self.connections
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        return {
            **self._stats,
            "connections_by_user": len(self.user_connections),
            "connections_by_correlation": len(self.correlation_connections),
            "max_connections": self.max_connections,
            "utilization_percentage": (len(self.connections) / self.max_connections)
            * 100,
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get WebSocket manager health status"""
        active_connections = len(self.connections)
        utilization = (active_connections / self.max_connections) * 100

        health_status = "healthy"
        if utilization > 90:
            health_status = "critical"
        elif utilization > 80:
            health_status = "warning"

        return {
            "status": health_status,
            "active_connections": active_connections,
            "max_connections": self.max_connections,
            "utilization_percentage": utilization,
            "user_connections": len(self.user_connections),
            "correlation_connections": len(self.correlation_connections),
        }


class WebSocketLoadBalancer:
    """WebSocket load balancer for scaling"""

    def __init__(self, managers: List[WebSocketManager]):
        self.managers = managers
        self.current_manager_index = 0

    def get_manager(self, user_id: str = None) -> WebSocketManager:
        """Get WebSocket manager using round-robin or user affinity"""
        if user_id:
            # Use user affinity for consistent routing
            manager_index = hash(user_id) % len(self.managers)
            return self.managers[manager_index]
        else:
            # Round-robin for general connections
            manager = self.managers[self.current_manager_index]
            self.current_manager_index = (self.current_manager_index + 1) % len(
                self.managers
            )
            return manager

    async def broadcast_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """Broadcast to user across all managers"""
        total_sent = 0
        for manager in self.managers:
            sent = await manager.broadcast_to_user(user_id, message)
            total_sent += sent
        return total_sent

    async def broadcast_to_correlation(
        self, correlation_id: str, message: WebSocketMessage
    ) -> int:
        """Broadcast to correlation across all managers"""
        total_sent = 0
        for manager in self.managers:
            sent = await manager.broadcast_to_correlation(correlation_id, message)
            total_sent += sent
        return total_sent

    def get_all_stats(self) -> Dict[str, Any]:
        """Get combined statistics from all managers"""
        all_stats = []
        for i, manager in enumerate(self.managers):
            stats = manager.get_stats()
            stats["manager_id"] = i
            all_stats.append(stats)

        return {
            "managers": all_stats,
            "total_connections": sum(
                stats["active_connections"] for stats in all_stats
            ),
            "total_messages_sent": sum(stats["messages_sent"] for stats in all_stats),
            "total_errors": sum(stats["errors"] for stats in all_stats),
        }


# Global WebSocket manager
_websocket_manager: Optional[WebSocketManager] = None
_websocket_load_balancer: Optional[WebSocketLoadBalancer] = None


def initialize_websocket_manager(max_connections: int = 1000) -> WebSocketManager:
    """Initialize global WebSocket manager"""
    global _websocket_manager

    _websocket_manager = WebSocketManager(max_connections)
    return _websocket_manager


def get_websocket_manager() -> WebSocketManager:
    """Get global WebSocket manager instance"""
    if _websocket_manager is None:
        raise RuntimeError("WebSocket manager not initialized")
    return _websocket_manager


def initialize_websocket_load_balancer(
    managers: List[WebSocketManager],
) -> WebSocketLoadBalancer:
    """Initialize WebSocket load balancer"""
    global _websocket_load_balancer

    _websocket_load_balancer = WebSocketLoadBalancer(managers)
    return _websocket_load_balancer


def get_websocket_load_balancer() -> WebSocketLoadBalancer:
    """Get WebSocket load balancer instance"""
    if _websocket_load_balancer is None:
        raise RuntimeError("WebSocket load balancer not initialized")
    return _websocket_load_balancer
