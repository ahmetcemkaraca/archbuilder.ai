// ArchBuilder.AI Staging Load Test
// K6 load testing script for staging environment

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
export let errorRate = new Rate('errors');
export let responseTime = new Trend('response_time');

// Test configuration
export let options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up to 10 users
    { duration: '5m', target: 10 },   // Stay at 10 users
    { duration: '2m', target: 20 },   // Ramp up to 20 users
    { duration: '5m', target: 20 },   // Stay at 20 users
    { duration: '2m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests must complete below 2s
    http_req_failed: ['rate<0.1'],     // Error rate must be below 10%
    errors: ['rate<0.1'],              // Custom error rate must be below 10%
  },
};

// Base URL for staging environment
const BASE_URL = __ENV.API_URL || 'http://staging-api.archbuilder.app';

// Test data
const testUsers = [
  { id: 'user_0001', email: 'test1@archbuilder.app', subscription: 'professional' },
  { id: 'user_0002', email: 'test2@archbuilder.app', subscription: 'enterprise' },
  { id: 'user_0003', email: 'test3@archbuilder.app', subscription: 'free' },
];

const testProjects = [
  { id: 'proj_0001', name: 'Test Office Building', building_type: 'office' },
  { id: 'proj_0002', name: 'Test Residential Complex', building_type: 'residential' },
  { id: 'proj_0003', name: 'Test Retail Center', building_type: 'retail' },
];

const aiPrompts = [
  'Create a modern office building layout with 20 floors',
  'Design a residential complex with 50 apartments',
  'Generate a retail center layout with parking for 200 cars',
  'Create an energy-efficient building design',
  'Design a building with accessibility features',
  'Generate a mixed-use development layout',
];

// Helper functions
function getRandomUser() {
  return testUsers[Math.floor(Math.random() * testUsers.length)];
}

function getRandomProject() {
  return testProjects[Math.floor(Math.random() * testProjects.length)];
}

function getRandomPrompt() {
  return aiPrompts[Math.floor(Math.random() * aiPrompts.length)];
}

function getAuthHeaders(user) {
  return {
    'Content-Type': 'application/json',
    'X-API-Key': `test-api-key-${user.id}`,
    'X-Correlation-ID': `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
  };
}

// Test scenarios
export function testHealthCheck() {
  const response = http.get(`${BASE_URL}/health`);
  
  const success = check(response, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  errorRate.add(!success);
  responseTime.add(response.timings.duration);
  
  return success;
}

export function testAICommand() {
  const user = getRandomUser();
  const project = getRandomProject();
  const prompt = getRandomPrompt();
  
  const payload = {
    prompt: prompt,
    user_id: user.id,
    project_id: project.id,
    ai_model: 'gpt-4',
    options: {
      temperature: 0.1,
      max_tokens: 4000,
      confidence_threshold: 0.8
    }
  };
  
  const headers = getAuthHeaders(user);
  const response = http.post(`${BASE_URL}/v1/ai/commands`, JSON.stringify(payload), { headers });
  
  const success = check(response, {
    'AI command status is 200 or 202': (r) => r.status === 200 || r.status === 202,
    'AI command response time < 5s': (r) => r.timings.duration < 5000,
    'AI command has correlation ID': (r) => r.headers['X-Correlation-ID'] !== undefined,
  });
  
  errorRate.add(!success);
  responseTime.add(response.timings.duration);
  
  return success;
}

export function testGetProjects() {
  const user = getRandomUser();
  const headers = getAuthHeaders(user);
  
  const response = http.get(`${BASE_URL}/v1/projects?user_id=${user.id}`, { headers });
  
  const success = check(response, {
    'get projects status is 200': (r) => r.status === 200,
    'get projects response time < 1s': (r) => r.timings.duration < 1000,
    'get projects returns array': (r) => {
      try {
        const data = JSON.parse(r.body);
        return Array.isArray(data.projects);
      } catch {
        return false;
      }
    },
  });
  
  errorRate.add(!success);
  responseTime.add(response.timings.duration);
  
  return success;
}

export function testGetUserProfile() {
  const user = getRandomUser();
  const headers = getAuthHeaders(user);
  
  const response = http.get(`${BASE_URL}/v1/users/${user.id}`, { headers });
  
  const success = check(response, {
    'get user profile status is 200': (r) => r.status === 200,
    'get user profile response time < 500ms': (r) => r.timings.duration < 500,
    'get user profile has user data': (r) => {
      try {
        const data = JSON.parse(r.body);
        return data.user && data.user.id === user.id;
      } catch {
        return false;
      }
    },
  });
  
  errorRate.add(!success);
  responseTime.add(response.timings.duration);
  
  return success;
}

export function testGetUsageMetrics() {
  const user = getRandomUser();
  const headers = getAuthHeaders(user);
  
  const response = http.get(`${BASE_URL}/v1/users/${user.id}/usage`, { headers });
  
  const success = check(response, {
    'get usage metrics status is 200': (r) => r.status === 200,
    'get usage metrics response time < 1s': (r) => r.timings.duration < 1000,
    'get usage metrics has data': (r) => {
      try {
        const data = JSON.parse(r.body);
        return data.usage && typeof data.usage === 'object';
      } catch {
        return false;
      }
    },
  });
  
  errorRate.add(!success);
  responseTime.add(response.timings.duration);
  
  return success;
}

export function testWebSocketConnection() {
  // WebSocket testing would require additional setup
  // For now, we'll simulate with HTTP requests
  const user = getRandomUser();
  const headers = getAuthHeaders(user);
  
  const response = http.get(`${BASE_URL}/v1/ws/status`, { headers });
  
  const success = check(response, {
    'WebSocket status is 200': (r) => r.status === 200,
    'WebSocket response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  errorRate.add(!success);
  responseTime.add(response.timings.duration);
  
  return success;
}

// Main test function
export default function() {
  // Run different test scenarios based on probability
  const scenario = Math.random();
  
  if (scenario < 0.1) {
    // 10% - Health check
    testHealthCheck();
  } else if (scenario < 0.3) {
    // 20% - Get user profile
    testGetUserProfile();
  } else if (scenario < 0.5) {
    // 20% - Get projects
    testGetProjects();
  } else if (scenario < 0.7) {
    // 20% - Get usage metrics
    testGetUsageMetrics();
  } else if (scenario < 0.9) {
    // 20% - WebSocket connection
    testWebSocketConnection();
  } else {
    // 10% - AI command (most resource intensive)
    testAICommand();
  }
  
  // Random sleep between 1-3 seconds
  sleep(Math.random() * 2 + 1);
}

// Setup function (runs once at the beginning)
export function setup() {
  console.log('Starting ArchBuilder.AI staging load test...');
  console.log(`Target URL: ${BASE_URL}`);
  console.log('Test scenarios: Health check, AI commands, User operations, WebSocket');
  
  // Verify staging environment is accessible
  const healthResponse = http.get(`${BASE_URL}/health`);
  if (healthResponse.status !== 200) {
    throw new Error(`Staging environment not accessible: ${healthResponse.status}`);
  }
  
  console.log('Staging environment is accessible');
}

// Teardown function (runs once at the end)
export function teardown(data) {
  console.log('Load test completed');
  console.log(`Total requests: ${data?.totalRequests || 'unknown'}`);
  console.log(`Error rate: ${data?.errorRate || 'unknown'}`);
}
