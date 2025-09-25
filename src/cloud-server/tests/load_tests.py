"""
Load Testing Infrastructure for ArchBuilder.AI
Kapsamlı yük testleri altyapısı - P42-T2
"""

import asyncio
import json
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import aiohttp
import pytest
import structlog
from locust import HttpUser, task, between
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging

logger = structlog.get_logger(__name__)


@dataclass
class LoadTestConfig:
    """Load test configuration"""
    base_url: str = "http://localhost:8000"
    api_key: str = "test-api-key"
    max_users: int = 100
    spawn_rate: int = 10
    test_duration: int = 300  # 5 minutes
    ramp_up_time: int = 60   # 1 minute
    cool_down_time: int = 30  # 30 seconds
    
    # Performance thresholds
    max_response_time_ms: int = 2000
    max_error_rate: float = 0.05  # 5%
    min_throughput_rps: int = 10
    
    # AI operation thresholds
    ai_max_response_time_ms: int = 30000  # 30 seconds
    ai_max_error_rate: float = 0.1  # 10%


@dataclass
class LoadTestResult:
    """Load test result data"""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    max_response_time_ms: float
    min_response_time_ms: float
    requests_per_second: float
    concurrent_users: int
    errors: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]


class ArchBuilderLoadTestUser(HttpUser):
    """Locust user class for ArchBuilder.AI load testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Setup user session"""
        self.api_key = "test-api-key"
        self.correlation_id = f"load_test_{int(time.time())}_{self.user_id}"
        self.headers = {
            "X-API-Key": self.api_key,
            "X-Correlation-ID": self.correlation_id,
            "Content-Type": "application/json"
        }
        
    @task(3)
    def test_health_endpoint(self):
        """Test health check endpoint"""
        with self.client.get("/v1/health", headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(2)
    def test_ai_command_simple(self):
        """Test simple AI command"""
        payload = {
            "user_prompt": "Create a simple 2 bedroom apartment layout",
            "total_area_m2": 80,
            "building_type": "residential",
            "options": {
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 1000
            }
        }
        
        with self.client.post(
            "/v1/ai/commands", 
            json=payload, 
            headers=self.headers,
            catch_response=True,
            timeout=35  # 35 second timeout for AI operations
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"AI command failed: {response.status_code}")
    
    @task(1)
    def test_project_analysis(self):
        """Test project analysis endpoint"""
        payload = {
            "project_id": "test_project_123",
            "analysis_type": "existing_project_analysis",
            "options": {
                "include_metrics": True,
                "include_clash_detection": True
            }
        }
        
        with self.client.post(
            "/v1/projects/analyze",
            json=payload,
            headers=self.headers,
            catch_response=True,
            timeout=30
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Project analysis failed: {response.status_code}")
    
    @task(1)
    def test_document_upload(self):
        """Test document upload endpoint"""
        # Simulate file upload with multipart form data
        files = {
            'file': ('test_drawing.dwg', b'fake_dwg_content', 'application/dwg')
        }
        
        with self.client.post(
            "/v1/documents/upload",
            files=files,
            headers={"X-API-Key": self.api_key},
            catch_response=True,
            timeout=60  # Longer timeout for file uploads
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Document upload failed: {response.status_code}")


class LoadTestRunner:
    """Main load test runner"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results: List[LoadTestResult] = []
        
    async def run_load_test(self, test_name: str) -> LoadTestResult:
        """Run a single load test"""
        logger.info("Starting load test", test_name=test_name, config=asdict(self.config))
        
        start_time = datetime.utcnow()
        
        # Create Locust environment
        env = Environment(user_classes=[ArchBuilderLoadTestUser])
        env.host = self.config.base_url
        
        # Configure test parameters
        env.create_local_runner()
        env.runner.start(
            user_count=self.config.max_users,
            spawn_rate=self.config.spawn_rate
        )
        
        # Run test for specified duration
        await asyncio.sleep(self.config.test_duration)
        
        # Stop the test
        env.runner.quit()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Collect results
        stats = env.stats
        result = LoadTestResult(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            total_requests=stats.total.num_requests,
            successful_requests=stats.total.num_requests - stats.total.num_failures,
            failed_requests=stats.total.num_failures,
            error_rate=stats.total.fail_ratio,
            avg_response_time_ms=stats.total.avg_response_time,
            p95_response_time_ms=stats.total.get_response_time_percentile(0.95),
            p99_response_time_ms=stats.total.get_response_time_percentile(0.99),
            max_response_time_ms=stats.total.max_response_time,
            min_response_time_ms=stats.total.min_response_time,
            requests_per_second=stats.total.current_rps,
            concurrent_users=self.config.max_users,
            errors=self._collect_errors(stats),
            performance_metrics=self._collect_performance_metrics(stats)
        )
        
        self.results.append(result)
        logger.info("Load test completed", result=asdict(result))
        
        return result
    
    def _collect_errors(self, stats) -> List[Dict[str, Any]]:
        """Collect error information from stats"""
        errors = []
        for entry in stats.entries.values():
            if entry.num_failures > 0:
                errors.append({
                    "endpoint": entry.name,
                    "failures": entry.num_failures,
                    "failure_rate": entry.fail_ratio,
                    "avg_response_time": entry.avg_response_time
                })
        return errors
    
    def _collect_performance_metrics(self, stats) -> Dict[str, Any]:
        """Collect performance metrics"""
        return {
            "total_requests": stats.total.num_requests,
            "successful_requests": stats.total.num_requests - stats.total.num_failures,
            "failed_requests": stats.total.num_failures,
            "error_rate": stats.total.fail_ratio,
            "avg_response_time": stats.total.avg_response_time,
            "p95_response_time": stats.total.get_response_time_percentile(0.95),
            "p99_response_time": stats.total.get_response_time_percentile(0.99),
            "max_response_time": stats.total.max_response_time,
            "min_response_time": stats.total.min_response_time,
            "current_rps": stats.total.current_rps,
            "total_rps": stats.total.total_rps
        }
    
    def validate_performance_thresholds(self, result: LoadTestResult) -> Dict[str, bool]:
        """Validate performance against thresholds"""
        validation = {
            "response_time_ok": result.avg_response_time_ms <= self.config.max_response_time_ms,
            "error_rate_ok": result.error_rate <= self.config.max_error_rate,
            "throughput_ok": result.requests_per_second >= self.config.min_throughput_rps,
            "ai_response_time_ok": result.avg_response_time_ms <= self.config.ai_max_response_time_ms,
            "ai_error_rate_ok": result.error_rate <= self.config.ai_max_error_rate
        }
        
        validation["overall_pass"] = all(validation.values())
        return validation
    
    def generate_report(self, result: LoadTestResult) -> str:
        """Generate load test report"""
        validation = self.validate_performance_thresholds(result)
        
        report = f"""
# Load Test Report: {result.test_name}

## Test Configuration
- Base URL: {self.config.base_url}
- Max Users: {self.config.max_users}
- Spawn Rate: {self.config.spawn_rate}
- Test Duration: {self.config.test_duration}s

## Results Summary
- Total Requests: {result.total_requests:,}
- Successful Requests: {result.successful_requests:,}
- Failed Requests: {result.failed_requests:,}
- Error Rate: {result.error_rate:.2%}
- Average Response Time: {result.avg_response_time_ms:.2f}ms
- P95 Response Time: {result.p95_response_time_ms:.2f}ms
- P99 Response Time: {result.p99_response_time_ms:.2f}ms
- Requests per Second: {result.requests_per_second:.2f}

## Performance Validation
- Response Time OK: {'✅' if validation['response_time_ok'] else '❌'} ({result.avg_response_time_ms:.2f}ms <= {self.config.max_response_time_ms}ms)
- Error Rate OK: {'✅' if validation['error_rate_ok'] else '❌'} ({result.error_rate:.2%} <= {self.config.max_error_rate:.2%})
- Throughput OK: {'✅' if validation['throughput_ok'] else '❌'} ({result.requests_per_second:.2f} RPS >= {self.config.min_throughput_rps} RPS)
- AI Response Time OK: {'✅' if validation['ai_response_time_ok'] else '❌'} ({result.avg_response_time_ms:.2f}ms <= {self.config.ai_max_response_time_ms}ms)
- AI Error Rate OK: {'✅' if validation['ai_error_rate_ok'] else '❌'} ({result.error_rate:.2%} <= {self.config.ai_max_error_rate:.2%})

## Overall Result: {'✅ PASS' if validation['overall_pass'] else '❌ FAIL'}

## Errors
"""
        
        if result.errors:
            for error in result.errors:
                report += f"- {error['endpoint']}: {error['failures']} failures ({error['failure_rate']:.2%})\n"
        else:
            report += "- No errors detected\n"
        
        return report


class LoadTestSuite:
    """Comprehensive load test suite"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.runner = LoadTestRunner(config)
        
    async def run_all_tests(self) -> List[LoadTestResult]:
        """Run all load tests"""
        tests = [
            ("Basic Load Test", self._basic_load_test),
            ("AI Operations Load Test", self._ai_operations_load_test),
            ("Document Processing Load Test", self._document_processing_load_test),
            ("Concurrent Users Load Test", self._concurrent_users_load_test),
            ("Stress Test", self._stress_test)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            logger.info("Running load test", test_name=test_name)
            try:
                result = await test_func()
                results.append(result)
                
                # Validate results
                validation = self.runner.validate_performance_thresholds(result)
                if not validation["overall_pass"]:
                    logger.warning("Load test failed validation", 
                                 test_name=test_name, 
                                 validation=validation)
                
            except Exception as e:
                logger.error("Load test failed", test_name=test_name, error=str(e))
                # Create failed result
                failed_result = LoadTestResult(
                    test_name=test_name,
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                    duration_seconds=0,
                    total_requests=0,
                    successful_requests=0,
                    failed_requests=0,
                    error_rate=1.0,
                    avg_response_time_ms=0,
                    p95_response_time_ms=0,
                    p99_response_time_ms=0,
                    max_response_time_ms=0,
                    min_response_time_ms=0,
                    requests_per_second=0,
                    concurrent_users=0,
                    errors=[{"error": str(e)}],
                    performance_metrics={}
                )
                results.append(failed_result)
        
        return results
    
    async def _basic_load_test(self) -> LoadTestResult:
        """Basic load test with moderate load"""
        config = LoadTestConfig(
            max_users=50,
            spawn_rate=10,
            test_duration=180,  # 3 minutes
            max_response_time_ms=1000,
            max_error_rate=0.02
        )
        runner = LoadTestRunner(config)
        return await runner.run_load_test("Basic Load Test")
    
    async def _ai_operations_load_test(self) -> LoadTestResult:
        """Load test focused on AI operations"""
        config = LoadTestConfig(
            max_users=20,
            spawn_rate=5,
            test_duration=300,  # 5 minutes
            max_response_time_ms=30000,  # 30 seconds for AI
            max_error_rate=0.1  # 10% for AI operations
        )
        runner = LoadTestRunner(config)
        return await runner.run_load_test("AI Operations Load Test")
    
    async def _document_processing_load_test(self) -> LoadTestResult:
        """Load test for document processing"""
        config = LoadTestConfig(
            max_users=10,
            spawn_rate=2,
            test_duration=600,  # 10 minutes
            max_response_time_ms=120000,  # 2 minutes for document processing
            max_error_rate=0.05
        )
        runner = LoadTestRunner(config)
        return await runner.run_load_test("Document Processing Load Test")
    
    async def _concurrent_users_load_test(self) -> LoadTestResult:
        """Test with high concurrent users"""
        config = LoadTestConfig(
            max_users=200,
            spawn_rate=20,
            test_duration=120,  # 2 minutes
            max_response_time_ms=2000,
            max_error_rate=0.05
        )
        runner = LoadTestRunner(config)
        return await runner.run_load_test("Concurrent Users Load Test")
    
    async def _stress_test(self) -> LoadTestResult:
        """Stress test to find breaking point"""
        config = LoadTestConfig(
            max_users=500,
            spawn_rate=50,
            test_duration=300,  # 5 minutes
            max_response_time_ms=5000,
            max_error_rate=0.2  # Allow higher error rate for stress test
        )
        runner = LoadTestRunner(config)
        return await runner.run_load_test("Stress Test")


# Pytest integration
@pytest.mark.load_test
@pytest.mark.asyncio
async def test_load_test_suite():
    """Pytest integration for load tests"""
    config = LoadTestConfig()
    suite = LoadTestSuite(config)
    
    results = await suite.run_all_tests()
    
    # Validate all tests passed
    for result in results:
        validation = LoadTestRunner(config).validate_performance_thresholds(result)
        if not validation["overall_pass"]:
            pytest.fail(f"Load test {result.test_name} failed validation: {validation}")


if __name__ == "__main__":
    """Run load tests directly"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run ArchBuilder.AI load tests")
    parser.add_argument("--config", type=str, help="Config file path")
    parser.add_argument("--test", type=str, help="Specific test to run")
    parser.add_argument("--duration", type=int, default=300, help="Test duration in seconds")
    parser.add_argument("--users", type=int, default=100, help="Number of concurrent users")
    
    args = parser.parse_args()
    
    config = LoadTestConfig(
        test_duration=args.duration,
        max_users=args.users
    )
    
    async def main():
        suite = LoadTestSuite(config)
        results = await suite.run_all_tests()
        
        # Generate reports
        for result in results:
            report = LoadTestRunner(config).generate_report(result)
            print(report)
            print("\n" + "="*80 + "\n")
    
    asyncio.run(main())
