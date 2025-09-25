"""
AI Inference Tasks for ArchBuilder.AI

Handles:
- AI model inference requests
- Prompt processing
- Response validation
- Result caching
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from celery import Task

from app.core.celery_app import ArchBuilderTask, TaskRequest, TaskResult, TaskStatus
from app.core.cache import get_cache_service
from app.ai.model_selector import AIModelSelector
from app.ai.validation import AIOutputValidator

logger = structlog.get_logger(__name__)


class AIInferenceTask(ArchBuilderTask):
    """AI inference task with enhanced monitoring"""
    
    def run(self, task_request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI inference task"""
        task_request = TaskRequest(**task_request_dict)
        
        logger.info(
            "Starting AI inference task",
            task_id=task_request.task_id,
            correlation_id=task_request.correlation_id,
            model=task_request.payload.get('model'),
            user_id=task_request.user_id
        )
        
        start_time = time.time()
        
        try:
            # Get AI model selector
            model_selector = AIModelSelector()
            
            # Select appropriate model
            model_config = model_selector.select_model(
                language=task_request.payload.get('context', {}).get('language', 'en'),
                document_type=task_request.payload.get('context', {}).get('document_type', 'general'),
                complexity=task_request.payload.get('context', {}).get('complexity', 'medium'),
                file_format=task_request.payload.get('context', {}).get('file_format'),
                analysis_type=task_request.payload.get('context', {}).get('analysis_type', 'creation'),
                user_preference=task_request.payload.get('context', {}).get('user_preference')
            )
            
            # Check cache first
            cache_service = asyncio.run(get_cache_service())
            cache_key = f"ai_response:{task_request.correlation_id}:{model_config['model']}"
            cached_result = asyncio.run(cache_service.get_ai_response(
                task_request.correlation_id,
                model_config['model']
            ))
            
            if cached_result:
                logger.info("AI response served from cache", correlation_id=task_request.correlation_id)
                return {
                    'status': 'success',
                    'result': cached_result,
                    'cached': True,
                    'model_used': model_config['model'],
                    'execution_time': time.time() - start_time
                }
            
            # Process AI inference
            result = self._process_ai_inference(task_request, model_config)
            
            # Cache the result
            asyncio.run(cache_service.cache_ai_response(
                task_request.correlation_id,
                model_config['model'],
                result,
                ttl=3600  # 1 hour
            ))
            
            execution_time = time.time() - start_time
            
            logger.info(
                "AI inference task completed",
                task_id=task_request.task_id,
                correlation_id=task_request.correlation_id,
                execution_time=execution_time,
                model_used=model_config['model']
            )
            
            return {
                'status': 'success',
                'result': result,
                'cached': False,
                'model_used': model_config['model'],
                'execution_time': execution_time
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                "AI inference task failed",
                task_id=task_request.task_id,
                correlation_id=task_request.correlation_id,
                error=str(e),
                execution_time=execution_time
            )
            
            raise
    
    def _process_ai_inference(self, task_request: TaskRequest, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process AI inference with model-specific logic"""
        prompt = task_request.payload.get('prompt', '')
        context = task_request.payload.get('context', {})
        
        # Create AI client based on model configuration
        if model_config['provider'] == 'openai':
            from app.ai.openai.client import OpenAIClient
            client = OpenAIClient()
        elif model_config['provider'] == 'vertex_ai':
            from app.ai.vertex.client import VertexAIClient
            client = VertexAIClient()
        else:
            raise ValueError(f"Unsupported AI provider: {model_config['provider']}")
        
        # Generate AI response
        response = client.generate_response(
            prompt=prompt,
            model=model_config['model'],
            context=context,
            correlation_id=task_request.correlation_id
        )
        
        # Validate AI output
        validator = AIOutputValidator()
        validation_result = validator.validate_response(
            response=response,
            correlation_id=task_request.correlation_id
        )
        
        if not validation_result.is_valid:
            logger.warning(
                "AI response validation failed",
                correlation_id=task_request.correlation_id,
                errors=validation_result.errors
            )
        
        return {
            'response': response,
            'validation': validation_result.dict(),
            'model_config': model_config,
            'confidence': response.get('confidence', 0.0),
            'requires_human_review': validation_result.requires_human_review
        }


@celery_app.task(bind=True, base=AIInferenceTask)
def process_ai_inference(self, task_request_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Process AI inference task"""
    return self.run(task_request_dict)


@celery_app.task(bind=True, base=ArchBuilderTask)
def batch_ai_inference(self, task_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process multiple AI inference tasks in batch"""
    logger.info("Starting batch AI inference", task_count=len(task_requests))
    
    results = []
    
    for task_request_dict in task_requests:
        try:
            # Create individual task
            task = AIInferenceTask()
            result = task.run(task_request_dict)
            results.append(result)
        except Exception as e:
            logger.error("Batch AI inference task failed", error=str(e))
            results.append({
                'status': 'error',
                'error': str(e),
                'task_id': task_request_dict.get('task_id')
            })
    
    logger.info("Batch AI inference completed", success_count=len([r for r in results if r.get('status') == 'success']))
    return results


@celery_app.task(bind=True, base=ArchBuilderTask)
def validate_ai_responses(self, correlation_ids: List[str]) -> Dict[str, Any]:
    """Validate multiple AI responses"""
    logger.info("Starting AI response validation", correlation_count=len(correlation_ids))
    
    validator = AIOutputValidator()
    validation_results = {}
    
    for correlation_id in correlation_ids:
        try:
            # Get cached response
            cache_service = asyncio.run(get_cache_service())
            cached_response = asyncio.run(cache_service.get_ai_response(correlation_id, "unknown"))
            
            if cached_response:
                validation_result = validator.validate_response(
                    response=cached_response,
                    correlation_id=correlation_id
                )
                validation_results[correlation_id] = validation_result.dict()
            else:
                validation_results[correlation_id] = {
                    'status': 'error',
                    'error': 'Response not found in cache'
                }
                
        except Exception as e:
            logger.error("AI response validation failed", correlation_id=correlation_id, error=str(e))
            validation_results[correlation_id] = {
                'status': 'error',
                'error': str(e)
            }
    
    return {
        'validation_results': validation_results,
        'total_validated': len(correlation_ids),
        'successful_validations': len([r for r in validation_results.values() if r.get('status') == 'success'])
    }


@celery_app.task(bind=True, base=ArchBuilderTask)
def cleanup_ai_cache(self, older_than_hours: int = 24) -> Dict[str, Any]:
    """Cleanup old AI responses from cache"""
    logger.info("Starting AI cache cleanup", older_than_hours=older_than_hours)
    
    try:
        cache_service = asyncio.run(get_cache_service())
        
        # Get cache manager
        cache_manager = cache_service.cache_manager
        
        # Delete old AI responses
        pattern = f"archbuilder:{CacheKeyType.AI_RESPONSE.value}:*"
        deleted_count = asyncio.run(cache_manager.delete_pattern(pattern))
        
        logger.info("AI cache cleanup completed", deleted_count=deleted_count)
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'older_than_hours': older_than_hours
        }
        
    except Exception as e:
        logger.error("AI cache cleanup failed", error=str(e))
        return {
            'status': 'error',
            'error': str(e)
        }
