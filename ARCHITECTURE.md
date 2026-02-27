# Architecture & Code Structure Guide

A comprehensive reference for understanding the codebase design.

---

## Directory Tree

```
fastAPI-design-project/
│
├── main.py                           # ← START HERE
│   └── FastAPI app factory, lifespan management, route registration
│
├── pyproject.toml                    # Poetry dependencies & config
├── .env.example                      # Configuration template
├── .env                              # (LOCAL ONLY - not in git)
│
├── app/                              # Main application package
│   ├── __init__.py
│   │
│   ├── models.py                     # ← SECOND: Understand data structures
│   │   ├── WingSpecification         # User input model
│   │   ├── OptimizationResponse      # API response
│   │   ├── AirfoilProfile            # Airfoil metadata
│   │   └── ToolOutput                # MCP tool results
│   │
│   ├── rag.py                        # ← THIRD: RAG search engine
│   │   ├── RAGEngine                 # Main RAG class
│   │   │   ├── embed_text()          # OpenAI embeddings
│   │   │   ├── add_airfoil()         # Store in Chroma
│   │   │   └── search_similar()      # Similarity search
│   │   └── get_rag_engine()          # Singleton accessor
│   │
│   ├── mcp_tools.py                  # ← FOURTH: Tool definitions
│   │   ├── MCPTool (abstract)        # Tool interface
│   │   ├── DownforceEstimatorTool    # Downforce calculation
│   │   ├── FlowInfluencePredictorTool # Flow prediction
│   │   ├── MCPToolRegistry           # Tool discovery & execution
│   │   └── get_tool_registry()       # Singleton accessor
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                 # ← FIRST: Configuration
│   │       ├── Settings              # Pydantic config model
│   │       └── get_settings()        # Singleton accessor
│   │
│   └── api/
│       ├── __init__.py
│       └── routes.py                 # ← FIFTH: API endpoints
│           ├── /api/v1/health        # Health check
│           ├── /api/v1/optimize-wing # Main feature
│           ├── /api/v1/find-similar-airfoils # RAG search
│           └── /api/v1/tools/*       # MCP tool endpoints
│
├── scripts/
│   └── load_data.py                  # ← Data loading CLI
│       ├── AirfoilData               # Data container
│       ├── AirfoilDataLoader         # CSV → Vector DB
│       └── main()                    # Entry point
│
├── data/
│   ├── uiuc_airfoils.csv             # Airfoil dataset (20 samples)
│   │   └── Columns: name, thickness_percent, camber_percent, max_cl, max_cd
│   │
│   └── chroma_db/                    # Vector database (created at runtime)
│       └── (Chroma stores vectors here)
│
├── tests/
│   ├── __init__.py
│   ├── test_rag.py                   # RAG engine tests (stubs)
│   ├── test_mcp_tools.py             # Tool tests (stubs)
│   └── test_api.py                   # API endpoint tests (stubs)
│
├── notebooks/
│   └── (Jupyter notebooks - created Week 2)
│
├── logs/
│   └── app.log                       # Application logs (created at runtime)
│
├── README.md                         # Project overview
├── SETUP_GUIDE.md                    # Step-by-step setup (this file)
└── .gitignore                        # Git ignore patterns
```

---

## Data Flow Diagram

### User submits wing optimization request

```
User Request
    ↓
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Endpoint: POST /api/v1/optimize-wing                │
│ - Validates WingSpecification (Pydantic)                    │
│ - Extracts settings (Depends → get_settings)                │
│ - Extracts RAG engine (Depends → get_rag_engine)            │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ RAG Engine: search_similar(query_text)                      │
│ 1. Format wing spec as text description                     │
│ 2. Call embed_text() → OpenAI API                           │
│ 3. Query Chroma with embedding vector                       │
│ 4. Return top-K similar airfoils + scores                   │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ MCP Tool Execution                                          │
│ 1. Get tool registry (Depends → get_tool_registry)          │
│ 2. Execute: estimate_downforce(airfoil, speed, geometry)   │
│ 3. Execute: predict_flow_influence(geometry)                │
│ 4. Collect results                                          │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Format Response: OptimizationResponse                       │
│ - job_id (UUID)                                             │
│ - recommended_airfoil (from RAG)                            │
│ - estimated_performance (from tools)                        │
│ - similar_configurations (RAG results)                      │
│ - reasoning (explanation)                                   │
│ - timestamp                                                 │
└─────────────────────────────────────────────────────────────┘
    ↓
API returns 202 Accepted with full result object
```

---

## Key Classes & Their Responsibilities

### Configuration: `Settings` (app/core/config.py)

```python
class Settings:
    app_env: str                    # development/staging/production
    app_debug: bool                 # enable debug mode
    openai_api_key: str             # ← MUST BE SET IN .env
    embedding_model: str            # OpenAI model (default: text-embedding-3-small)
    chroma_path: Path               # Where to store vectors
    airfoil_data_path: Path         # Where to find CSV
    rag_similarity_threshold: float  # Min similarity score (0-1)
    rag_top_k_results: int          # How many results to return
```

**Singleton pattern:** `get_settings()` returns cached instance

---

### Data Models: `Pydantic Models` (app/models.py)

```python
# REQUEST: What the user sends
class WingSpecification(BaseModel):
    wing_type: WingType             # single_element, double_element, etc
    chord_mm: float                 # 50-2000 mm (validated)
    span_mm: float                  # 100-3000 mm (validated)
    target_downforce_kg: float      # 1-500 kg (validated)
    operating_speed_kph: float      # 10-400 kph (validated)

# RESPONSE: What the API returns
class OptimizationResponse(BaseModel):
    job_id: UUID                    # Unique request ID
    status: str                     # "complete", "processing", etc
    recommended_airfoil: AirfoilProfile
    estimated_performance: AeroPerformanceEstimate
    similar_configurations: list[SimilarConfigurationResult]
    reasoning: str                  # Explanation
    timestamp: datetime             # When completed
```

---

### RAG Search: `RAGEngine` (app/rag.py)

```python
class RAGEngine:
    def __init__(self, settings: Settings):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.collection = chroma.get_or_create_collection(...)
    
    def embed_text(self, text: str) -> list[float]:
        """Convert text to 1536-dimensional vector via OpenAI"""
        response = self.client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    
    def add_airfoil(self, name: str, desc: str, metadata: dict, doc_id: str):
        """Store airfoil in vector database"""
        embedding = self.embed_text(desc)
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[desc],
            metadatas=[metadata]
        )
    
    def search_similar(self, query: str, limit: int=5) -> list:
        """Find similar airfoils via embedding similarity"""
        query_embedding = self.embed_text(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )
        return results
```

**Singleton pattern:** `get_rag_engine()` returns cached instance

---

### MCP Tools: `MCPTool` (app/mcp_tools.py)

```python
# Abstract interface for all tools
class MCPTool(ABC):
    @property
    def name(self) -> str:          # Tool ID
        pass
    
    @property
    def description(self) -> str:   # What it does
        pass
    
    @property
    def input_schema(self) -> dict: # Input validation
        pass
    
    async def execute(self, **kwargs) -> dict:
        """Execute the tool"""
        pass

# Example implementation
class DownforceEstimatorTool(MCPTool):
    name = "estimate_downforce"
    
    async def execute(self, airfoil: str, speed_kph: float, 
                     chord_mm: float, span_mm: float) -> dict:
        # Lookup aerodynamic coefficients
        # Calculate: L = 0.5 * rho * v^2 * S * CL
        # Return estimated downforce
        return {
            "airfoil": airfoil,
            "estimated_downforce_kg": 45.2,
            "method": "database_lookup"
        }

# Tool registry for discovery & execution
class MCPToolRegistry:
    def register(self, tool: MCPTool):
        self._tools[tool.name] = tool
    
    def list_tools(self) -> list[dict]:
        return [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema
        } for tool in self._tools.values()]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolOutput:
        tool = self._tools[tool_name]
        result = await tool.execute(**kwargs)
        return ToolOutput(tool_name, success=True, result=result, ...)
```

**Singleton pattern:** `get_tool_registry()` returns cached instance

---

### FastAPI Application: `create_app()` (main.py)

```python
def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="Wing Aerodynamic Analyzer",
        docs_url="/docs",              # Swagger UI
        openapi_url="/openapi.json"    # OpenAPI schema
    )
    
    # Startup/shutdown hooks (lifespan context manager)
    @asynccontextmanager
    async def lifespan(app):
        # STARTUP
        logger.info("Starting up...")
        settings = get_settings()
        rag_engine = get_rag_engine(settings)  # Initialize
        tool_registry = get_tool_registry()    # Initialize
        
        yield  # Application runs here
        
        # SHUTDOWN
        logger.info("Shutting down...")
        # Cleanup if needed
    
    # Middleware: CORS, error handling, etc
    app.add_middleware(CORSMiddleware, ...)
    
    # Exception handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        return JSONResponse(status_code=400, ...)
    
    # Register routes
    app.include_router(router)
    
    return app
```

---

## Dependency Injection Pattern

FastAPI uses `Depends()` to inject dependencies:

```python
# In routes.py
@router.post("/optimize-wing")
async def optimize_wing(
    request: WingSpecification,
    rag_engine = Depends(get_rag_engine_dep)
) -> OptimizationResponse:
    """
    FastAPI automatically:
    1. Calls get_rag_engine_dep() to get RAG engine
    2. Passes it as rag_engine parameter
    3. Caches result during request lifecycle
    """
    results = rag_engine.search_similar(...)
    return OptimizationResponse(...)
```

**Benefits:**
- Easy to test (mock dependencies)
- Clean separation of concerns
- Single source of truth for each service

---

## Error Handling Strategy

```python
# Validation errors (Pydantic)
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
    # HTTP 400 Bad Request

# API errors (OpenAI, Chroma)
try:
    result = rag_engine.search_similar(query)
except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Search service error"
    )
    # HTTP 503 Service Unavailable

# Tool execution errors
async def execute_tool(...):
    try:
        result = await tool.execute(...)
        return ToolOutput(success=True, result=result, ...)
    except Exception as e:
        return ToolOutput(success=False, error_message=str(e), ...)
    # Tool returns error to client; doesn't crash API
```

---

## Testing Strategy

```python
# Unit tests for each module
tests/
├── test_rag.py          # Test RAG embedding, search, storage
├── test_mcp_tools.py    # Test tool execution and validation
└── test_api.py          # Test endpoints and integration

# Example test
def test_wing_validation():
    """Test that chord constraints are enforced"""
    wing = WingSpecification(
        wing_type="single_element",
        chord_mm=10,  # TOO SMALL! (min 50)
        span_mm=1400,
        target_downforce_kg=45,
        operating_speed_kph=200
    )
    # Should raise ValidationError

# Run tests
pytest                   # All tests
pytest -v               # Verbose
pytest --cov           # With coverage report
```

---

## Security Best Practices Implemented

1. **API Key Management**
   - Keys loaded from environment variables
   - `.env` file git-ignored
   - No hardcoded secrets

2. **Input Validation**
   - All inputs validated by Pydantic
   - Numeric constraints (wing chord 50-2000 mm)
   - Type checking

3. **Error Handling**
   - Production: Generic error messages
   - Development: Verbose logs
   - No stack traces to client in production

4. **Logging**
   - Comprehensive logging throughout
   - DEBUG level in development
   - INFO level in production

---

## Week 1 Implementation Roadmap

**Current Status:** Architecture complete, stubs in place

**Day 2-3: RAG Implementation**
```
app/rag.py
├── RAGEngine.embed_text()       ← Call OpenAI embeddings API
├── RAGEngine.search_similar()   ← Query Chroma for nearest neighbors
└── RAGEngine.add_airfoil()      ← Already has structure
```

**Day 2-3: MCP Tools Implementation**
```
app/mcp_tools.py
├── DownforceEstimatorTool.execute()      ← Aerodynamic calculations
└── FlowInfluencePredictorTool.execute()  ← Empirical models
```

**Day 4: Optimization Endpoint**
```
app/api/routes.py
└── optimize_wing()              ← Main business logic
    ├── Call RAG search
    ├── Call MCP tools
    ├── Aggregate results
    └── Return OptimizationResponse
```

**Day 5: Testing**
```
tests/
├── test_rag.py      ← Write full test suite
├── test_mcp_tools.py
└── test_api.py
```

---

## Reference

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Pydantic Docs](https://docs.pydantic.dev)
- [OpenAI API](https://platform.openai.com/docs)
- [Chroma Docs](https://docs.trychroma.com)

Good luck with your implementation! 🚀
