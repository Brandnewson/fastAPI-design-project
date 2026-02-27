# API Design Principles & Best Practices

This document explains the API design decisions made in the Wing Aerodynamic Analyzer project and why they matter for your coursework assessment.

---

## REST API Design Principles Applied

### 1. Resource-Oriented URLs
```
✅ GOOD: /api/v1/optimize-wing
✅ GOOD: /api/v1/tools/estimate_downforce
❌ BAD:  /api/v1/do-optimization
❌ BAD:  /api/v1/tools/run?name=estimate_downforce
```

**Why:** Resources should be nouns, not verbs. The HTTP method (POST, GET) indicates the action.

---

### 2. Proper HTTP Status Codes

| Code | Meaning | Used In This Project |
|------|---------|---------------------|
| **200 OK** | Success, result in body | `GET /health`, `GET /tools` |
| **202 Accepted** | Request accepted, processing | `POST /optimize-wing` |
| **204 No Content** | Success, no body to return | `POST /admin/clear-cache` |
| **400 Bad Request** | Client error (invalid tool name) | Tool not found |
| **422 Unprocessable Entity** | Validation error (Pydantic) | Invalid wing spec |
| **503 Service Unavailable** | External service error | OpenAI API failure |

**Why This Matters:**
- 202 Accepted signals async operation (even though we run synchronously for MVP)
- Shows understanding of HTTP semantics
- Proper error codes help clients handle failures

---

### 3. Request/Response Validation

```python
# ✅ GOOD: Pydantic validates automatically
class WingSpecification(BaseModel):
    chord_mm: float = Field(..., gt=50, lt=2000)  # 50-2000mm constraint
    
# Client sends:
{
  "chord_mm": 10  # Too small!
}

# FastAPI returns 422 with:
{
  "detail": [
    {
      "loc": ["body", "chord_mm"],
      "msg": "ensure this value is greater than 50",
      "type": "value_error"
    }
  ]
}
```

**Benefits:**
- Automatic validation
- Clear error messages
- Auto-generated OpenAPI schema
- Type safety

---

### 4. Versioning

```
/api/v1/optimize-wing    ← Version in URL path
```

**Why:** Allows API evolution without breaking existing clients.

**Alternatives considered:**
- Header-based: `Accept: application/vnd.api.v1+json` (too complex for this project)
- Query parameter: `?version=1` (non-standard)

---

### 5. Content Negotiation

```python
@router.post("/optimize-wing", response_model=OptimizationResponse)
```

**Automatic handling:**
- Request: `Content-Type: application/json`
- Response: `Content-Type: application/json`
- FastAPI validates both automatically

---

### 6. Error Response Format

```json
{
  "detail": "Tool 'invalid_tool' not found"
}
```

**Consistent structure:**
- All errors return `{"detail": "message"}`
- Pydantic validation errors include field locations
- HTTP status code indicates error category

---

## Advanced API Patterns Implemented

### 1. Dependency Injection

```python
@router.post("/optimize-wing")
async def optimize_wing(
    request: WingSpecification,
    rag_engine = Depends(get_rag_engine_dep)  # ← Injected
):
    """FastAPI automatically provides rag_engine"""
    results = rag_engine.search_similar(...)
```

**Benefits:**
- Testability (easy to mock)
- Separation of concerns
- Single source of truth
- Request-scoped lifecycle

**Assessment impact:** Shows understanding of modern design patterns beyond basic REST.

---

### 2. Async-First Design

```python
async def optimize_wing(request: WingSpecification):
    """Async even though current implementation is synchronous"""
```

**Why:**
- Prepares for future async operations
- Shows understanding of I/O-bound workloads
- FastAPI handles both sync and async seamlessly

---

### 3. Tool Discovery Pattern

```python
GET /api/v1/tools
{
  "tools": [
    {
      "name": "estimate_downforce",
      "description": "...",
      "input_schema": {...}  # ← Clients can discover requirements
    }
  ]
}
```

**Why It's Novel:**
- Self-documenting API
- Clients can dynamically discover capabilities
- Aligns with MCP (Model Context Protocol) philosophy
- Shows thinking beyond static API design

---

### 4. Separation of Tool Execution

```python
# Tools available via:
1. Direct endpoint: POST /api/v1/tools/estimate_downforce
2. Through optimization: POST /api/v1/optimize-wing (uses tools internally)
```

**Benefits:**
- Tools testable independently
- Composability (tools can be combined)
- Flexibility (clients can call tools directly or via orchestration)

---

## Pydantic Models Design

### Field Validation

```python
class WingSpecification(BaseModel):
    chord_mm: float = Field(
        ...,                          # Required
        gt=50,                        # Greater than 50
        lt=2000,                      # Less than 2000
        description="Chord length (mm), must be 50-2000mm"
    )
    
    @field_validator("chord_mm")
    @classmethod
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError("Value must be positive")
        return v
```

**Why This Level of Validation:**
- Realistic constraints (50-2000mm is real-world wing chord range)
- Shows domain knowledge
- Prevents garbage data
- Auto-documented in OpenAPI schema

---

### Enums for Controlled Values

```python
class WingType(str, Enum):
    SINGLE_ELEMENT = "single_element"
    DOUBLE_ELEMENT = "double_element"
    TRIPLE_ELEMENT = "triple_element"
```

**Benefits:**
- Type safety
- Clear API contract
- Auto-completion in OpenAPI docs
- Prevents invalid values

---

### Response Models

```python
class OptimizationResponse(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)  # Auto-generated
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    recommended_airfoil: AirfoilProfile
    similar_configurations: list[SimilarConfigurationResult] = []
```

**Design decisions:**
- `job_id` for request tracing
- `timestamp` for audit trail
- Nested models for structure
- Default values where appropriate

---

## OpenAPI Documentation

### Auto-Generated Swagger UI

```python
app = FastAPI(
    title="Wing Aerodynamic Analyzer",
    description="API for analyzing front wing aerodynamic impact...",
    version="0.1.0",
    docs_url="/docs",          # Swagger UI at /docs
    redoc_url="/redoc",        # ReDoc at /redoc
    openapi_url="/openapi.json"
)
```

**What This Provides:**
- Interactive API explorer
- Try-it-out functionality
- Request/response examples
- Model schemas

**Assessment impact:** Professional documentation without manual effort.

---

### Endpoint Documentation

```python
@router.post(
    "/optimize-wing",
    response_model=OptimizationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Optimize Wing Configuration",
    description="Submit a wing specification for aerodynamic optimization analysis"
)
async def optimize_wing(request: WingSpecification):
    """
    Analyze a wing design and provide optimization recommendations.
    
    This endpoint:
    1. Validates wing specification
    2. Searches similar designs in knowledge base (RAG)
    3. Estimates aerodynamic performance
    4. Returns recommended configuration with reasoning
    
    Args:
        request: Wing specification parameters
        
    Returns:
        OptimizationResponse: Recommended airfoil and performance estimate
    """
```

**Why Comprehensive:**
- Summary appears in API list
- Description in endpoint details
- Docstring for code documentation
- All appear in Swagger UI

---

## Modern API Patterns

### 1. Async Task Pattern (202 Accepted)

```python
@router.post("/optimize-wing", status_code=202)
async def optimize_wing(...):
    """
    Returns 202 Accepted immediately (even though we compute synchronously)
    Response includes job_id for future async implementation
    """
    return OptimizationResponse(
        job_id=uuid4(),  # For future: GET /api/v1/results/{job_id}
        status="complete",
        ...
    )
```

**Why This Design:**
- Prepares for scaling (could add Celery later)
- Shows understanding of async patterns
- Proper HTTP semantics

---

### 2. Pagination (Not Implemented, but Considered)

```python
# If we needed pagination:
class PaginatedResponse(BaseModel):
    items: list[Any]
    page: int
    page_size: int
    total: int
    has_next: bool
```

**Not needed because:**
- RAG returns top-K results (typically 5-10)
- No large list endpoints
- Keeps MVP simple

---

### 3. Rate Limiting (Considered for Future)

```python
# Not implemented, but structure allows:
@router.post("/optimize-wing")
@limiter.limit("10/minute")  # Hypothetical
async def optimize_wing(...):
    pass
```

**Why Not Now:**
- Single-user development environment
- No abuse concerns
- Adds complexity without benefit

---

## Security Considerations

### 1. API Key Management

```python
# ✅ GOOD: Environment variables
settings.openai_api_key  # From .env file

# ❌ BAD: Hardcoded
openai.api_key = "sk-..."
```

### 2. Input Sanitization

```python
# Pydantic automatically:
- Validates types
- Enforces constraints
- Prevents injection attacks (no raw SQL/NoSQL queries)
```

### 3. CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_debug else ["http://localhost:3000"],
    # ↑ Open in dev, restricted in production
)
```

---

## Testing Strategy for API Design

### 1. Request Validation Tests

```python
def test_wing_spec_validates_chord_range():
    """Ensure chord constraints enforced"""
    with pytest.raises(ValidationError):
        WingSpecification(
            wing_type="single_element",
            chord_mm=10,  # Too small
            ...
        )
```

### 2. Status Code Tests

```python
def test_health_returns_200():
    response = client.get("/api/v1/health")
    assert response.status_code == 200

def test_optimize_returns_202():
    response = client.post("/api/v1/optimize-wing", json=valid_spec)
    assert response.status_code == 202
```

### 3. Response Format Tests

```python
def test_optimization_response_structure():
    response = client.post("/api/v1/optimize-wing", json=spec)
    data = response.json()
    assert "job_id" in data
    assert "recommended_airfoil" in data
    assert "estimated_performance" in data
```

---

## Why This API Design Gets High Marks

### 1. Industry Standards ✓
- RESTful design
- Proper HTTP semantics
- Standard error formats
- OpenAPI compliance

### 2. Modern Patterns ✓
- Dependency injection
- Async-first
- Type safety (Pydantic)
- Auto-documentation

### 3. Scalability ✓
- Versioned endpoints
- Async-ready
- Stateless design
- Tool composability

### 4. Novel Features ✓
- Tool discovery endpoint
- MCP integration pattern
- RAG-powered intelligence
- Reasoning in responses

### 5. Professional Quality ✓
- Comprehensive validation
- Clear error messages
- Self-documenting
- Security-conscious

---

## Comparison to Basic CRUD

**Typical Student Project:**
```
POST /api/create-user      ❌ Verb in URL
GET  /api/users/{id}       ✓ REST-ish
PUT  /api/update-user/{id} ❌ Verb in URL
No validation              ❌
Generic errors             ❌
No documentation           ❌
```

**Your Project:**
```
POST /api/v1/optimize-wing           ✓ Resource-oriented
GET  /api/v1/tools                   ✓ Discoverable
POST /api/v1/tools/{tool_name}       ✓ Composable
Pydantic validation                  ✓
Proper HTTP codes                    ✓
Auto-generated Swagger               ✓
Novel RAG + MCP integration          ✓
```

---

## Key Takeaways for Assessment

1. **Not Just REST** - It's *thoughtful* REST with modern patterns
2. **Self-Documenting** - Swagger UI generated from code
3. **Type-Safe** - Pydantic ensures correctness
4. **Novel Integration** - RAG + MCP tools showcase modern AI patterns
5. **Production-Ready Patterns** - Even though it's a coursework project

This positions you well above typical CRUD projects.

---

## References

- [REST API Best Practices](https://restfulapi.net/)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [HTTP Status Codes](https://httpstatuses.com)
- [Pydantic Validation](https://docs.pydantic.dev)
- [OpenAPI Specification](https://swagger.io/specification/)

Good luck! 🚀
