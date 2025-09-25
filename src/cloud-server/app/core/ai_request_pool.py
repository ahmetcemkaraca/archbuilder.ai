"""
AI Request Pool with Rate Limiting and Caps for ArchBuilder.AI

Provides:
- AI request pooling and queuing
- Rate limiting per user and model
- Request prioritization
- Cost tracking and limits
- Load balancing across AI providers
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict, deque

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class RequestPriority(str, Enum):
    """AI request priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class RequestStatus(str, Enum):
    """AI request status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RATE_LIMITED = "rate_limited"


@dataclass
class AIRequest:
    """AI request data structure"""
    request_id: str
    user_id: str
    correlation_id: str
    model: str
    provider: str
    prompt: str
    priority: RequestPriority
    max_tokens: int
    temperature: float
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: RequestStatus = RequestStatus.QUEUED
    result: Optional[Any] = None
    error: Optional[str] = None
    cost_estimate: float = 0.0
    actual_cost: float = 0.0


class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    tokens_per_minute: int = 100000
    tokens_per_hour: int = 1000000
    cost_per_hour: float = 100.0
    cost_per_day: float = 1000.0


class AIRequestPool:
    """AI request pool with rate limiting and caps"""
    
    def __init__(self, max_concurrent_requests: int = 50):
        self.max_concurrent_requests = max_concurrent_requests
        self.active_requests: Dict[str, AIRequest] = {}
        self.request_queue: deque = deque()
        self.completed_requests: Dict[str, AIRequest] = {}
        
        # Rate limiting tracking
        self.user_rate_limits: Dict[str, Dict[str, List[datetime]]] = defaultdict(lambda: defaultdict(list))
        self.model_rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        
        # Cost tracking
        self.user_costs: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.model_costs: Dict[str, float] = defaultdict(float)
        
        # Configuration
        self.rate_limit_configs: Dict[str, RateLimitConfig] = {}
        self.model_configs: Dict[str, Dict[str, Any]] = {}
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'completed_requests': 0,
            'failed_requests': 0,
            'rate_limited_requests': 0,
            'total_cost': 0.0,
            'avg_response_time': 0.0
        }
        
        # Processing task
        self._processing_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start AI request pool processing"""
        self._processing_task = asyncio.create_task(self._process_requests())
        self._cleanup_task = asyncio.create_task(self._cleanup_completed_requests())
        logger.info("AI request pool started")
    
    async def stop(self):
        """Stop AI request pool processing"""
        if self._processing_task:
            self._processing_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        logger.info("AI request pool stopped")
    
    async def submit_request(
        self,
        user_id: str,
        correlation_id: str,
        model: str,
        provider: str,
        prompt: str,
        priority: RequestPriority = RequestPriority.NORMAL,
        max_tokens: int = 4000,
        temperature: float = 0.1
    ) -> str:
        """Submit AI request to pool"""
        
        # Check rate limits
        if not await self._check_rate_limits(user_id, model, provider):
            self.stats['rate_limited_requests'] += 1
            raise Exception("Rate limit exceeded")
        
        # Create request
        request_id = f"ai_req_{int(time.time() * 1000000)}"
        cost_estimate = self._estimate_cost(model, provider, max_tokens)
        
        request = AIRequest(
            request_id=request_id,
            user_id=user_id,
            correlation_id=correlation_id,
            model=model,
            provider=provider,
            prompt=prompt,
            priority=priority,
            max_tokens=max_tokens,
            temperature=temperature,
            created_at=datetime.utcnow(),
            cost_estimate=cost_estimate
        )
        
        # Add to queue
        self.request_queue.append(request)
        self.stats['total_requests'] += 1
        
        logger.info(
            "AI request submitted",
            request_id=request_id,
            user_id=user_id,
            model=model,
            provider=provider,
            priority=priority.value,
            queue_length=len(self.request_queue)
        )
        
        return request_id
    
    async def get_request_status(self, request_id: str) -> Optional[AIRequest]:
        """Get request status"""
        if request_id in self.active_requests:
            return self.active_requests[request_id]
        elif request_id in self.completed_requests:
            return self.completed_requests[request_id]
        else:
            return None
    
    async def cancel_request(self, request_id: str) -> bool:
        """Cancel AI request"""
        if request_id in self.active_requests:
            request = self.active_requests[request_id]
            request.status = RequestStatus.CANCELLED
            request.completed_at = datetime.utcnow()
            
            # Move to completed
            self.completed_requests[request_id] = request
            del self.active_requests[request_id]
            
            logger.info("AI request cancelled", request_id=request_id)
            return True
        
        return False
    
    async def _process_requests(self):
        """Process AI requests from queue"""
        while True:
            try:
                # Check if we can process more requests
                if len(self.active_requests) >= self.max_concurrent_requests:
                    await asyncio.sleep(0.1)
                    continue
                
                # Get next request from queue
                if not self.request_queue:
                    await asyncio.sleep(0.1)
                    continue
                
                # Sort queue by priority
                self.request_queue = deque(sorted(
                    self.request_queue,
                    key=lambda req: self._get_priority_value(req.priority),
                    reverse=True
                ))
                
                request = self.request_queue.popleft()
                
                # Check rate limits again
                if not await self._check_rate_limits(request.user_id, request.model, request.provider):
                    request.status = RequestStatus.RATE_LIMITED
                    self.completed_requests[request.request_id] = request
                    self.stats['rate_limited_requests'] += 1
                    continue
                
                # Process request
                await self._process_single_request(request)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error processing AI request", error=str(e))
                await asyncio.sleep(1)
    
    async def _process_single_request(self, request: AIRequest):
        """Process a single AI request"""
        request.status = RequestStatus.PROCESSING
        request.started_at = datetime.utcnow()
        self.active_requests[request.request_id] = request
        
        start_time = time.time()
        
        try:
            # Simulate AI processing (replace with actual AI client calls)
            result = await self._call_ai_model(request)
            
            # Update request
            request.status = RequestStatus.COMPLETED
            request.completed_at = datetime.utcnow()
            request.result = result
            request.actual_cost = self._calculate_actual_cost(request, result)
            
            # Update statistics
            self.stats['completed_requests'] += 1
            self.stats['total_cost'] += request.actual_cost
            
            # Update user costs
            self.user_costs[request.user_id]['total'] += request.actual_cost
            self.user_costs[request.user_id][request.model] += request.actual_cost
            self.model_costs[request.model] += request.actual_cost
            
            # Update rate limiting tracking
            await self._update_rate_limits(request)
            
            # Move to completed
            self.completed_requests[request.request_id] = request
            del self.active_requests[request.request_id]
            
            processing_time = time.time() - start_time
            self._update_avg_response_time(processing_time)
            
            logger.info(
                "AI request completed",
                request_id=request.request_id,
                processing_time=processing_time,
                cost=request.actual_cost
            )
            
        except Exception as e:
            # Handle request failure
            request.status = RequestStatus.FAILED
            request.completed_at = datetime.utcnow()
            request.error = str(e)
            
            self.stats['failed_requests'] += 1
            
            # Move to completed
            self.completed_requests[request.request_id] = request
            del self.active_requests[request.request_id]
            
            logger.error(
                "AI request failed",
                request_id=request.request_id,
                error=str(e)
            )
    
    async def _call_ai_model(self, request: AIRequest) -> Dict[str, Any]:
        """Call AI model (placeholder for actual implementation)"""
        # This would be replaced with actual AI client calls
        await asyncio.sleep(1)  # Simulate processing time
        
        return {
            "response": f"AI response for: {request.prompt[:50]}...",
            "tokens_used": request.max_tokens,
            "model": request.model,
            "provider": request.provider
        }
    
    async def _check_rate_limits(self, user_id: str, model: str, provider: str) -> bool:
        """Check if request is within rate limits"""
        now = datetime.utcnow()
        
        # Get user rate limit config
        user_config = self.rate_limit_configs.get(user_id, RateLimitConfig())
        
        # Check user rate limits
        user_requests = self.user_rate_limits[user_id]['requests']
        user_requests = [req_time for req_time in user_requests if now - req_time < timedelta(minutes=1)]
        
        if len(user_requests) >= user_config.requests_per_minute:
            return False
        
        # Check model rate limits
        model_requests = self.model_rate_limits[model]
        model_requests = [req_time for req_time in model_requests if now - req_time < timedelta(minutes=1)]
        
        if len(model_requests) >= 100:  # Model-specific limit
            return False
        
        # Check cost limits
        user_hourly_cost = self.user_costs[user_id]['total']
        if user_hourly_cost >= user_config.cost_per_hour:
            return False
        
        return True
    
    async def _update_rate_limits(self, request: AIRequest):
        """Update rate limiting tracking"""
        now = datetime.utcnow()
        
        # Update user rate limits
        self.user_rate_limits[request.user_id]['requests'].append(now)
        
        # Update model rate limits
        self.model_rate_limits[request.model].append(now)
        
        # Clean old entries
        cutoff_time = now - timedelta(hours=1)
        self.user_rate_limits[request.user_id]['requests'] = [
            req_time for req_time in self.user_rate_limits[request.user_id]['requests']
            if req_time > cutoff_time
        ]
        self.model_rate_limits[request.model] = [
            req_time for req_time in self.model_rate_limits[request.model]
            if req_time > cutoff_time
        ]
    
    def _get_priority_value(self, priority: RequestPriority) -> int:
        """Get numeric priority value"""
        priority_map = {
            RequestPriority.LOW: 1,
            RequestPriority.NORMAL: 2,
            RequestPriority.HIGH: 3,
            RequestPriority.CRITICAL: 4
        }
        return priority_map.get(priority, 2)
    
    def _estimate_cost(self, model: str, provider: str, max_tokens: int) -> float:
        """Estimate request cost"""
        # Simplified cost estimation
        cost_per_token = 0.0001  # $0.0001 per token
        return max_tokens * cost_per_token
    
    def _calculate_actual_cost(self, request: AIRequest, result: Dict[str, Any]) -> float:
        """Calculate actual request cost"""
        tokens_used = result.get('tokens_used', request.max_tokens)
        cost_per_token = 0.0001
        return tokens_used * cost_per_token
    
    def _update_avg_response_time(self, response_time: float):
        """Update average response time"""
        total_requests = self.stats['completed_requests'] + self.stats['failed_requests']
        if total_requests > 0:
            current_avg = self.stats['avg_response_time']
            new_avg = ((current_avg * (total_requests - 1)) + response_time) / total_requests
            self.stats['avg_response_time'] = new_avg
    
    async def _cleanup_completed_requests(self):
        """Cleanup old completed requests"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                old_requests = [
                    req_id for req_id, req in self.completed_requests.items()
                    if req.completed_at and req.completed_at < cutoff_time
                ]
                
                for req_id in old_requests:
                    del self.completed_requests[req_id]
                
                if old_requests:
                    logger.info("Cleaned up old completed requests", count=len(old_requests))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cleanup task", error=str(e))
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get AI request pool statistics"""
        return {
            'active_requests': len(self.active_requests),
            'queued_requests': len(self.request_queue),
            'completed_requests': len(self.completed_requests),
            'max_concurrent_requests': self.max_concurrent_requests,
            'utilization_percentage': (len(self.active_requests) / self.max_concurrent_requests) * 100,
            'stats': self.stats.copy(),
            'user_costs': dict(self.user_costs),
            'model_costs': dict(self.model_costs)
        }
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user-specific statistics"""
        user_requests = [
            req for req in self.completed_requests.values()
            if req.user_id == user_id
        ]
        
        return {
            'total_requests': len(user_requests),
            'completed_requests': len([req for req in user_requests if req.status == RequestStatus.COMPLETED]),
            'failed_requests': len([req for req in user_requests if req.status == RequestStatus.FAILED]),
            'total_cost': self.user_costs[user_id]['total'],
            'cost_by_model': dict(self.user_costs[user_id])
        }
    
    def set_user_rate_limit(self, user_id: str, config: RateLimitConfig):
        """Set rate limit configuration for user"""
        self.rate_limit_configs[user_id] = config
        logger.info("Rate limit config updated", user_id=user_id, config=config.dict())


# Global AI request pool
_ai_request_pool: Optional[AIRequestPool] = None


def initialize_ai_request_pool(max_concurrent_requests: int = 50) -> AIRequestPool:
    """Initialize global AI request pool"""
    global _ai_request_pool
    
    _ai_request_pool = AIRequestPool(max_concurrent_requests)
    return _ai_request_pool


def get_ai_request_pool() -> AIRequestPool:
    """Get global AI request pool instance"""
    if _ai_request_pool is None:
        raise RuntimeError("AI request pool not initialized")
    return _ai_request_pool
