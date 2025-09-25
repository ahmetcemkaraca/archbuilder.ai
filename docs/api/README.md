# ArchBuilder.AI API Documentation

Welcome to the ArchBuilder.AI API documentation. This comprehensive guide will help you integrate ArchBuilder.AI's powerful AI-driven architectural design capabilities into your applications.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Core Endpoints](#core-endpoints)
4. [AI Design Endpoints](#ai-design-endpoints)
5. [Project Management](#project-management)
6. [File Management](#file-management)
7. [Collaboration](#collaboration)
8. [Webhooks](#webhooks)
9. [SDKs and Libraries](#sdks-and-libraries)
10. [Rate Limits](#rate-limits)
11. [Error Handling](#error-handling)
12. [Examples](#examples)

## Getting Started

### Base URL
```
Production: https://api.archbuilder.app/v1
Staging: https://staging-api.archbuilder.app/v1
```

### API Versioning
ArchBuilder.AI API uses URL-based versioning. The current version is `v1`.

### Content Type
All requests and responses use `application/json` content type.

### Response Format
All API responses follow a consistent format:

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "correlationId": "req_123456789",
    "version": "v1"
  },
  "errors": []
}
```

## Authentication

### API Keys
ArchBuilder.AI uses API key authentication. Include your API key in the request header:

```http
X-API-Key: your_api_key_here
```

### Getting API Keys
1. Log in to your ArchBuilder.AI account
2. Navigate to Settings → API Keys
3. Generate a new API key
4. Store it securely (it won't be shown again)

### Authentication Example
```bash
curl -H "X-API-Key: your_api_key_here" \
     -H "Content-Type: application/json" \
     https://api.archbuilder.app/v1/projects
```

## Core Endpoints

### Health Check
Check API status and connectivity.

```http
GET /health
```

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### User Information
Get current user information.

```http
GET /user
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "user_123456789",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "architect",
    "subscription": {
      "plan": "professional",
      "status": "active",
      "expiresAt": "2024-12-31T23:59:59Z"
    },
    "permissions": [
      "read:projects",
      "write:projects",
      "ai:design"
    ]
  }
}
```

## AI Design Endpoints

### Generate Building Layout
Generate an AI-powered building layout based on requirements.

```http
POST /ai/generate-layout
```

**Request Body:**
```json
{
  "buildingType": "residential",
  "requirements": {
    "bedrooms": 3,
    "bathrooms": 2,
    "totalArea": 150,
    "floors": 2
  },
  "constraints": {
    "siteWidth": 12,
    "siteDepth": 15,
    "setbacks": {
      "front": 3,
      "rear": 2,
      "sides": 1.5
    }
  },
  "preferences": {
    "style": "modern",
    "orientation": "north",
    "sustainability": "high"
  },
  "options": {
    "model": "gpt-4",
    "temperature": 0.7,
    "maxIterations": 3
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "layoutId": "layout_123456789",
    "status": "completed",
    "result": {
      "floorPlans": [
        {
          "floor": 1,
          "rooms": [
            {
              "id": "room_1",
              "name": "Living Room",
              "area": 25.5,
              "position": { "x": 0, "y": 0 },
              "dimensions": { "width": 5.1, "height": 5.0 }
            }
          ]
        }
      ],
      "3dModel": {
        "url": "https://api.archbuilder.app/v1/models/layout_123456789.obj",
        "format": "obj"
      },
      "analysis": {
        "efficiency": 0.85,
        "circulation": 0.12,
        "naturalLight": 0.78
      }
    },
    "processingTime": 45.2,
    "cost": {
      "credits": 10,
      "remaining": 490
    }
  }
}
```

### Optimize Design
Optimize an existing design for specific criteria.

```http
POST /ai/optimize-design
```

**Request Body:**
```json
{
  "designId": "design_123456789",
  "optimizationGoals": [
    "energy_efficiency",
    "cost_reduction",
    "accessibility"
  ],
  "constraints": {
    "budget": 500000,
    "timeline": 12,
    "regulations": ["ADA", "LEED"]
  },
  "options": {
    "maxIterations": 5,
    "convergenceThreshold": 0.01
  }
}
```

### Code Compliance Check
Check building code compliance for a design.

```http
POST /ai/code-check
```

**Request Body:**
```json
{
  "designId": "design_123456789",
  "jurisdiction": "California",
  "buildingType": "residential",
  "codes": ["IBC", "IRC", "ADA"],
  "options": {
    "detailedReport": true,
    "suggestions": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "complianceId": "compliance_123456789",
    "status": "completed",
    "result": {
      "overallCompliance": 0.92,
      "violations": [
        {
          "code": "IBC-1008.1.1",
          "description": "Door width insufficient",
          "severity": "error",
          "location": "room_1_door_1",
          "suggestion": "Increase door width to minimum 32 inches"
        }
      ],
      "recommendations": [
        {
          "category": "accessibility",
          "description": "Add accessible route to all rooms",
          "priority": "high"
        }
      ],
      "certification": {
        "LEED": {
          "eligible": true,
          "potentialScore": 45
        }
      }
    }
  }
}
```

## Project Management

### Create Project
Create a new architectural project.

```http
POST /projects
```

**Request Body:**
```json
{
  "name": "Modern House Design",
  "description": "A contemporary residential design",
  "buildingType": "residential",
  "client": {
    "name": "John Smith",
    "email": "john@example.com"
  },
  "settings": {
    "units": "metric",
    "language": "en",
    "timezone": "UTC"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "project_123456789",
    "name": "Modern House Design",
    "status": "active",
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:30:00Z",
    "owner": {
      "id": "user_123456789",
      "name": "John Doe"
    },
    "collaborators": [],
    "settings": {
      "units": "metric",
      "language": "en",
      "timezone": "UTC"
    }
  }
}
```

### List Projects
Get a list of user's projects.

```http
GET /projects?page=1&limit=20&status=active
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)
- `status` (optional): Filter by status (active, archived, deleted)
- `buildingType` (optional): Filter by building type
- `sort` (optional): Sort field (createdAt, updatedAt, name)
- `order` (optional): Sort order (asc, desc)

**Response:**
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "id": "project_123456789",
        "name": "Modern House Design",
        "status": "active",
        "buildingType": "residential",
        "createdAt": "2024-01-15T10:30:00Z",
        "updatedAt": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 1,
      "pages": 1
    }
  }
}
```

### Get Project Details
Get detailed information about a specific project.

```http
GET /projects/{projectId}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "project_123456789",
    "name": "Modern House Design",
    "description": "A contemporary residential design",
    "status": "active",
    "buildingType": "residential",
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:30:00Z",
    "owner": {
      "id": "user_123456789",
      "name": "John Doe",
      "email": "john@example.com"
    },
    "collaborators": [
      {
        "id": "user_987654321",
        "name": "Jane Smith",
        "role": "collaborator",
        "permissions": ["read", "comment"]
      }
    ],
    "settings": {
      "units": "metric",
      "language": "en",
      "timezone": "UTC"
    },
    "statistics": {
      "designs": 5,
      "files": 12,
      "collaborators": 2,
      "lastActivity": "2024-01-15T10:30:00Z"
    }
  }
}
```

### Update Project
Update project information.

```http
PUT /projects/{projectId}
```

**Request Body:**
```json
{
  "name": "Updated Project Name",
  "description": "Updated description",
  "settings": {
    "units": "imperial",
    "language": "es"
  }
}
```

### Delete Project
Delete a project (soft delete).

```http
DELETE /projects/{projectId}
```

## File Management

### Upload File
Upload a file to a project.

```http
POST /projects/{projectId}/files
```

**Request (multipart/form-data):**
```
Content-Type: multipart/form-data

file: [binary file data]
metadata: {
  "name": "floor_plan.dwg",
  "type": "drawing",
  "description": "Ground floor plan"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "file_123456789",
    "name": "floor_plan.dwg",
    "type": "drawing",
    "size": 2048576,
    "url": "https://api.archbuilder.app/v1/files/file_123456789",
    "uploadedAt": "2024-01-15T10:30:00Z"
  }
}
```

### List Project Files
Get files associated with a project.

```http
GET /projects/{projectId}/files
```

### Download File
Download a file.

```http
GET /files/{fileId}/download
```

### File Processing
Process uploaded files (e.g., extract data from CAD files).

```http
POST /files/{fileId}/process
```

**Request Body:**
```json
{
  "processType": "extract_geometry",
  "options": {
    "includeMetadata": true,
    "generateThumbnail": true
  }
}
```

## Collaboration

### Add Collaborator
Add a collaborator to a project.

```http
POST /projects/{projectId}/collaborators
```

**Request Body:**
```json
{
  "email": "collaborator@example.com",
  "role": "collaborator",
  "permissions": ["read", "comment", "edit"]
}
```

### Update Collaborator Permissions
Update collaborator permissions.

```http
PUT /projects/{projectId}/collaborators/{userId}
```

**Request Body:**
```json
{
  "permissions": ["read", "comment"]
}
```

### Remove Collaborator
Remove a collaborator from a project.

```http
DELETE /projects/{projectId}/collaborators/{userId}
```

### Project Comments
Add comments to a project.

```http
POST /projects/{projectId}/comments
```

**Request Body:**
```json
{
  "content": "This design looks great!",
  "target": {
    "type": "design",
    "id": "design_123456789"
  },
  "mentions": ["user_987654321"]
}
```

## Webhooks

### Register Webhook
Register a webhook endpoint to receive notifications.

```http
POST /webhooks
```

**Request Body:**
```json
{
  "url": "https://your-app.com/webhooks/archbuilder",
  "events": [
    "project.created",
    "project.updated",
    "design.completed",
    "file.uploaded"
  ],
  "secret": "your_webhook_secret"
}
```

### Webhook Events
ArchBuilder.AI sends webhook notifications for various events:

#### Project Events
- `project.created`: New project created
- `project.updated`: Project updated
- `project.deleted`: Project deleted
- `project.shared`: Project shared with collaborator

#### Design Events
- `design.started`: AI design process started
- `design.completed`: AI design process completed
- `design.failed`: AI design process failed

#### File Events
- `file.uploaded`: File uploaded
- `file.processed`: File processing completed
- `file.deleted`: File deleted

#### Collaboration Events
- `collaborator.added`: Collaborator added to project
- `collaborator.removed`: Collaborator removed from project
- `comment.added`: Comment added to project

### Webhook Payload Example
```json
{
  "event": "design.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "projectId": "project_123456789",
    "designId": "design_123456789",
    "status": "completed",
    "result": {
      "layoutId": "layout_123456789"
    }
  }
}
```

## SDKs and Libraries

### Official SDKs

#### Python SDK
```bash
pip install archbuilder-ai
```

```python
from archbuilder import ArchBuilderClient

client = ArchBuilderClient(api_key="your_api_key")

# Create a project
project = client.projects.create({
    "name": "My Project",
    "buildingType": "residential"
})

# Generate AI layout
layout = client.ai.generate_layout({
    "buildingType": "residential",
    "requirements": {
        "bedrooms": 3,
        "bathrooms": 2
    }
})
```

#### JavaScript SDK
```bash
npm install @archbuilder/ai-sdk
```

```javascript
import { ArchBuilderClient } from '@archbuilder/ai-sdk';

const client = new ArchBuilderClient({
  apiKey: 'your_api_key'
});

// Create a project
const project = await client.projects.create({
  name: 'My Project',
  buildingType: 'residential'
});

// Generate AI layout
const layout = await client.ai.generateLayout({
  buildingType: 'residential',
  requirements: {
    bedrooms: 3,
    bathrooms: 2
  }
});
```

#### C# SDK
```bash
dotnet add package ArchBuilder.AI.SDK
```

```csharp
using ArchBuilder.AI;

var client = new ArchBuilderClient("your_api_key");

// Create a project
var project = await client.Projects.CreateAsync(new CreateProjectRequest
{
    Name = "My Project",
    BuildingType = "residential"
});

// Generate AI layout
var layout = await client.AI.GenerateLayoutAsync(new GenerateLayoutRequest
{
    BuildingType = "residential",
    Requirements = new Requirements
    {
        Bedrooms = 3,
        Bathrooms = 2
    }
});
```

## Rate Limits

ArchBuilder.AI API implements rate limiting to ensure fair usage:

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```

### Rate Limits by Plan

#### Free Plan
- **Requests**: 100 requests/hour
- **AI Operations**: 10 operations/month
- **File Storage**: 1GB

#### Professional Plan
- **Requests**: 10,000 requests/hour
- **AI Operations**: 1,000 operations/month
- **File Storage**: 100GB

#### Enterprise Plan
- **Requests**: 100,000 requests/hour
- **AI Operations**: Unlimited
- **File Storage**: 1TB

### Handling Rate Limits
When rate limits are exceeded, the API returns a `429 Too Many Requests` status:

```json
{
  "success": false,
  "errors": [
    {
      "code": "RATE_LIMIT_EXCEEDED",
      "message": "Rate limit exceeded. Try again in 3600 seconds.",
      "details": {
        "limit": 1000,
        "remaining": 0,
        "resetAt": "2024-01-15T11:30:00Z"
      }
    }
  ]
}
```

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Invalid input parameters",
      "field": "buildingType",
      "details": {
        "allowedValues": ["residential", "commercial", "industrial"]
      }
    }
  ],
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "correlationId": "req_123456789"
  }
}
```

### Common Error Codes

#### Authentication Errors
- `UNAUTHORIZED`: Invalid or missing API key
- `FORBIDDEN`: Insufficient permissions
- `ACCOUNT_SUSPENDED`: Account suspended

#### Validation Errors
- `VALIDATION_ERROR`: Invalid input parameters
- `MISSING_REQUIRED_FIELD`: Required field missing
- `INVALID_FORMAT`: Invalid data format

#### Resource Errors
- `NOT_FOUND`: Resource not found
- `ALREADY_EXISTS`: Resource already exists
- `CONFLICT`: Resource conflict

#### AI Service Errors
- `AI_SERVICE_UNAVAILABLE`: AI service temporarily unavailable
- `AI_PROCESSING_FAILED`: AI processing failed
- `INSUFFICIENT_CREDITS`: Insufficient AI credits

#### Rate Limiting
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded

### Error Handling Best Practices

#### Retry Logic
```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
```

#### Exponential Backoff
```python
import time
import random

def exponential_backoff(attempt):
    delay = (2 ** attempt) + random.uniform(0, 1)
    time.sleep(delay)
```

## Examples

### Complete Workflow Example

#### 1. Create Project
```bash
curl -X POST https://api.archbuilder.app/v1/projects \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Modern House",
    "buildingType": "residential"
  }'
```

#### 2. Generate AI Layout
```bash
curl -X POST https://api.archbuilder.app/v1/ai/generate-layout \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "buildingType": "residential",
    "requirements": {
      "bedrooms": 3,
      "bathrooms": 2,
      "totalArea": 150
    }
  }'
```

#### 3. Upload Design Files
```bash
curl -X POST https://api.archbuilder.app/v1/projects/project_123/files \
  -H "X-API-Key: your_api_key" \
  -F "file=@floor_plan.dwg" \
  -F "metadata={\"name\":\"Floor Plan\",\"type\":\"drawing\"}"
```

#### 4. Check Code Compliance
```bash
curl -X POST https://api.archbuilder.app/v1/ai/code-check \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "designId": "design_123456789",
    "jurisdiction": "California",
    "buildingType": "residential"
  }'
```

### Python Integration Example
```python
import archbuilder
import asyncio

async def main():
    client = archbuilder.ArchBuilderClient(api_key="your_api_key")
    
    # Create project
    project = await client.projects.create({
        "name": "AI-Generated House",
        "buildingType": "residential"
    })
    
    # Generate layout
    layout = await client.ai.generate_layout({
        "buildingType": "residential",
        "requirements": {
            "bedrooms": 3,
            "bathrooms": 2,
            "totalArea": 150
        }
    })
    
    # Wait for completion
    while layout.status != "completed":
        await asyncio.sleep(5)
        layout = await client.ai.get_layout(layout.id)
    
    # Get results
    result = layout.result
    print(f"Generated {len(result.floorPlans)} floor plans")
    
    # Upload additional files
    with open("site_plan.dwg", "rb") as f:
        file = await client.files.upload(project.id, f, {
            "name": "Site Plan",
            "type": "drawing"
        })
    
    # Check code compliance
    compliance = await client.ai.code_check({
        "designId": layout.id,
        "jurisdiction": "California"
    })
    
    print(f"Code compliance: {compliance.result.overallCompliance:.2%}")

if __name__ == "__main__":
    asyncio.run(main())
```

### JavaScript Integration Example
```javascript
import { ArchBuilderClient } from '@archbuilder/ai-sdk';

async function createAIDesign() {
  const client = new ArchBuilderClient({
    apiKey: 'your_api_key'
  });
  
  try {
    // Create project
    const project = await client.projects.create({
      name: 'AI-Generated House',
      buildingType: 'residential'
    });
    
    // Generate layout
    const layout = await client.ai.generateLayout({
      buildingType: 'residential',
      requirements: {
        bedrooms: 3,
        bathrooms: 2,
        totalArea: 150
      }
    });
    
    // Poll for completion
    let status = layout.status;
    while (status !== 'completed' && status !== 'failed') {
      await new Promise(resolve => setTimeout(resolve, 5000));
      const updatedLayout = await client.ai.getLayout(layout.id);
      status = updatedLayout.status;
    }
    
    if (status === 'completed') {
      console.log('Layout generated successfully!');
      console.log('Floor plans:', layout.result.floorPlans);
    } else {
      console.error('Layout generation failed');
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

createAIDesign();
```

---

## Support and Resources

### Documentation
- **API Reference**: [api.archbuilder.app/docs](https://api.archbuilder.app/docs)
- **SDK Documentation**: [docs.archbuilder.app/sdks](https://docs.archbuilder.app/sdks)
- **Code Examples**: [github.com/archbuilder/examples](https://github.com/archbuilder/examples)

### Community
- **Developer Forum**: [forum.archbuilder.app](https://forum.archbuilder.app)
- **Discord Community**: [discord.gg/archbuilder](https://discord.gg/archbuilder)
- **Stack Overflow**: Tag your questions with `archbuilder-ai`

### Support
- **Email**: api-support@archbuilder.app
- **Status Page**: [status.archbuilder.app](https://status.archbuilder.app)
- **Enterprise Support**: enterprise@archbuilder.app

---

*For the most up-to-date API documentation, visit [api.archbuilder.app/docs](https://api.archbuilder.app/docs)*
