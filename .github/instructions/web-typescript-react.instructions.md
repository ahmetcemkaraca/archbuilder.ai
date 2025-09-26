---
applyTo: "**/*.tsx,**/*.jsx"
description: Web UI (TypeScript/React/Next) — modern, secure, a11y-first, minimal-input scaffolding.
---
As Web UI (TS/React):

# ArchBuilder.AI Web Frontend Standards- Use TypeScript strict mode, ESLint + Prettier; small, testable components.

- Prefer Next.js App Router, Server Components, React 18 features; data fetching with caching.

## Core Architecture- UI kit: Tailwind CSS + Radix UI + shadcn/ui; dark/light themes, design tokens, responsive grid.

As Web UI Developer for ArchBuilder.AI:- State: server-first; client state minimal; tanstack query for remote state when needed.

- Build TypeScript-first React components with strict mode enabled- A11y: labels, focus ring, roles, keyboard nav; test with axe.

- Use Next.js App Router for AI workflow orchestration- Security: escape/encode outputs; CSP headers; avoid dangerous HTML; sanitize user content.

- Implement Server Components for performance-critical AI interactions- Forms: react-hook-form + zod resolver; field-level errors; optimistic UI when safe.

- Apply shadcn/ui + Tailwind CSS for consistent design system- Testing: Vitest + Testing Library for units; Playwright for e2e critical flows.

- Integrate with ArchBuilder.AI cloud API and desktop client- Performance: image optimization, code-splitting, lazy routes; avoid blocking JS; measure Lighthouse ≥ 90.

- DX: consistent imports, absolute paths; CI checks for lint, type, test.

## ArchBuilder.AI Specific Requirements

Registry & i18n (mandatory)

### AI Integration Components- Do not hardcode UI text in components; add strings to locale files (EN default, TR translation) and reference via i18n.

```typescript- When adding components/hooks that export public APIs, record them in `docs/registry/identifiers.json`.

// components/ai/AILayoutGenerator.tsx- If client-side models or form schemas change, reflect them in `docs/registry/schemas.json`.
interface AILayoutRequest {
  buildingType: 'residential' | 'commercial' | 'mixed-use'
  plotSize: { width: number; height: number }
  constraints: LayoutConstraint[]
  preferences: UserPreference[]
}

interface AILayoutResponse {
  layoutId: string
  generatedPlan: CADLayout
  confidence: number
  alternatives: CADLayout[]
  processingTime: number
}
```

### Project Management Components
```typescript
// components/project/ProjectDashboard.tsx
// Manage multiple architectural projects
// Integration with desktop app synchronization
// Real-time collaboration features

// components/project/FileUpload.tsx 
// CAD file upload (DWG, DXF, IFC)
// Progress tracking for AI processing
// Validation and format conversion
```

### Real-time Status Components
```typescript
// components/status/AIProcessingStatus.tsx
interface ProcessingStatus {
  stage: 'analyzing' | 'generating' | 'optimizing' | 'complete'
  progress: number
  estimatedTime: number
  currentOperation: string
}

// Real-time WebSocket connection to cloud server
// Progress indicators for long-running AI operations
```

## Technical Standards

### State Management
```typescript
// Use Tanstack Query for ArchBuilder.AI API calls
const useAILayoutGeneration = (request: AILayoutRequest) => {
  return useQuery({
    queryKey: ['ai-layout', request],
    queryFn: () => archBuilderAPI.generateLayout(request),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error) => {
      // Retry logic for AI service failures
      return failureCount < 3 && error.status !== 402 // Don't retry billing issues
    }
  })
}

// Optimistic updates for user interactions
const useProjectUpdate = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: updateProject,
    onMutate: async (updatedProject) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries(['project', updatedProject.id])
      
      // Snapshot previous value
      const previousProject = queryClient.getQueryData(['project', updatedProject.id])
      
      // Optimistically update
      queryClient.setQueryData(['project', updatedProject.id], updatedProject)
      
      return { previousProject }
    },
    onError: (err, updatedProject, context) => {
      // Rollback on error
      queryClient.setQueryData(['project', updatedProject.id], context?.previousProject)
    }
  })
}
```

### Form Validation
```typescript
// Zod schemas for ArchBuilder.AI data validation
import { z } from 'zod'

const ProjectSchema = z.object({
  name: z.string().min(1).max(100),
  buildingType: z.enum(['residential', 'commercial', 'mixed-use']),
  plotDimensions: z.object({
    width: z.number().min(1).max(1000),
    height: z.number().min(1).max(1000),
    units: z.enum(['meters', 'feet'])
  }),
  constraints: z.array(z.object({
    type: z.enum(['setback', 'height-limit', 'density', 'parking']),
    value: z.number(),
    description: z.string().optional()
  }))
})

// React Hook Form integration
const ProjectForm = () => {
  const form = useForm<ProjectFormData>({
    resolver: zodResolver(ProjectSchema),
    defaultValues: {
      buildingType: 'residential',
      plotDimensions: { units: 'meters' }
    }
  })

  const onSubmit = (data: ProjectFormData) => {
    // Türkçe hata mesajları ile form gönderimi
    createProjectMutation.mutate(data)
  }
}
```

### Internationalization (i18n)
```json
// locales/tr/common.json
{
  "ai": {
    "generating": "AI layout oluşturuluyor...",
    "analyzing": "Proje analiz ediliyor...",
    "optimizing": "Layout optimize ediliyor...",
    "complete": "AI işlemi tamamlandı"
  },
  "project": {
    "create": "Yeni Proje Oluştur",
    "upload": "CAD Dosyası Yükle",
    "collaborate": "İş Birliği Yap"
  },
  "validation": {
    "required": "Bu alan zorunludur",
    "invalidFile": "Geçersiz dosya formatı. DWG, DXF veya IFC dosyası yükleyin."
  }
}

// locales/en/common.json
{
  "ai": {
    "generating": "Generating AI layout...",
    "analyzing": "Analyzing project...",
    "optimizing": "Optimizing layout...",
    "complete": "AI processing complete"
  }
}
```

### Performance & Security
```typescript
// Lazy loading for heavy AI visualization components
const AILayoutViewer = lazy(() => import('./AILayoutViewer'))
const CADRenderer = lazy(() => import('./CADRenderer'))

// Security: Sanitize user-uploaded file content
import DOMPurify from 'dompurify'

const sanitizeCADMetadata = (metadata: string) => {
  return DOMPurify.sanitize(metadata, {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: []
  })
}

// CSP headers for AI API integration
const securityHeaders = {
  'Content-Security-Policy': "default-src 'self'; script-src 'self'; connect-src 'self' https://api.archbuilder.app wss://api.archbuilder.app"
}
```

### Testing Standards
```typescript
// Playwright E2E for critical AI workflows
// tests/e2e/ai-layout-generation.spec.ts
test('AI layout generation workflow', async ({ page }) => {
  await page.goto('/projects/new')
  
  // Proje bilgilerini doldur
  await page.fill('[data-testid="project-name"]', 'Test Residential Project')
  await page.selectOption('[data-testid="building-type"]', 'residential')
  
  // CAD dosyası yükle
  await page.setInputFiles('[data-testid="cad-upload"]', 'test-files/sample.dwg')
  
  // AI layout oluşturma işlemini başlat
  await page.click('[data-testid="generate-layout"]')
  
  // AI işlemi tamamlanana kadar bekle
  await page.waitForSelector('[data-testid="layout-complete"]', { timeout: 60000 })
  
  // Sonuçları doğrula
  await expect(page.locator('[data-testid="generated-layout"]')).toBeVisible()
  await expect(page.locator('[data-testid="confidence-score"]')).toContainText('%')
})

// Component testing with React Testing Library
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

test('AI processing status updates correctly', async () => {
  const mockStatus = { stage: 'analyzing', progress: 25, estimatedTime: 120 }
  
  render(<AIProcessingStatus status={mockStatus} />)
  
  expect(screen.getByText('Proje analiz ediliyor...')).toBeInTheDocument()
  expect(screen.getByText('25%')).toBeInTheDocument()
  expect(screen.getByText('Tahmini süre: 2 dakika')).toBeInTheDocument()
})
```

## Registry & Context Integration
- Register all AI-related components and hooks in `docs/registry/identifiers.json`
- Document API schemas for AI requests/responses in `docs/registry/schemas.json`
- Update context in `.mds/context/current-context.md` for major UI workflow changes
- Use TypeScript for contract enforcement with backend APIs

## Error Handling
```typescript
// AI service error boundaries
class AIErrorBoundary extends Component {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log AI processing errors
    logger.error('AI component error', {
      error: error.message,
      component: errorInfo.componentStack,
      userId: user?.id
    })
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="ai-error-fallback">
          <h2>AI İşlemi Başarısız</h2>
          <p>Layout oluşturma sırasında bir hata oluştu. Lütfen tekrar deneyin.</p>
          <button onClick={() => this.setState({ hasError: false })}>
            Tekrar Dene
          </button>
        </div>
      )
    }
    
    return this.props.children
  }
}
```

Always prioritize user experience with clear progress indicators, helpful error messages in English, and responsive design for both desktop and mobile interfaces.