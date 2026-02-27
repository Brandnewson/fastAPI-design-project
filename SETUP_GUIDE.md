# Project Initialization Guide

## Day 1 Scaffolding Complete ✅

You now have a fully architected FastAPI project with:
- ✅ Clean, modular project structure
- ✅ Configuration management with `.env`
- ✅ Pydantic models with validation
- ✅ RAG engine framework (Chroma + OpenAI)
- ✅ MCP tool architecture
- ✅ API routes (stubs)
- ✅ Data loader script
- ✅ Sample aerodynamic dataset

---

## Setup Instructions

### Step 1: Install uv and Dependencies

```bash
# Navigate to project
cd c:\Code\fastAPI-design-project

# Create virtual environment and install dependencies
uv venv
uv sync
```

**Expected output:**
```
Using Python 3.10-3.13
Creating virtual environment at .venv
Resolved and installed dependencies
```

### Step 2: Configure Environment

```bash
# Copy template to .env
copy .env.example .env

# Edit .env and add your OpenAI API key
# Use any text editor to open .env and paste your key on this line:
# OPENAI_API_KEY=sk-...
```

**Required for RAG to work:**
- `OPENAI_API_KEY` - Your OpenAI API key (get one at https://platform.openai.com/api-keys)

**Optional offline mode:**
- Set `EMBEDDING_PROVIDER=local` to use local hash-based embeddings without API calls

**Optional (have sensible defaults):**
- `APP_ENV` - development/staging/production
- `APP_DEBUG` - true/false
- `RAG_TOP_K_RESULTS` - how many similar airfoils to return (default: 5)

### Step 3: Verify Setup

```bash
# Test that imports work
python -c "from app.core.config import get_settings; print('✓ Config working')"

# Check OpenAI API key is configured
python -c "from app.core.config import get_settings; s=get_settings(); print(f'✓ API key configured: {s.openai_api_key[:10]}...')"
```

**Expected output:**
```
✓ Config working
✓ API key configured: sk-...
```

### Step 4: Load Aerodynamic Data

```bash
# Load airfoil data into vector database
python scripts/load_data.py

# You should see:
# Loading airfoil data from CSV...
# Progress: 20 airfoils loaded...
# ✓ Successfully loaded 20 airfoils into vector store
```

**Note:** The sample dataset includes 20 airfoils. In production, you'd download the full UIUC database (1500+ airfoils).

### Step 5: Start Development Server

```bash
# Start FastAPI development server with auto-reload
uv run uvicorn main:app --reload

# You should see:
# ✓ Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Step 6: Verify API is Running

**Option A: In your browser**
- Visit http://localhost:8000/docs
- You should see the Swagger UI with all endpoints listed

**Option B: Using curl**
```bash
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"healthy","app_name":"Wing Aerodynamic Analyzer","version":"0.1.0","environment":"development"}
```

---

## Project Architecture Overview

### 1. Configuration Layer (`app/core/config.py`)
- Loads settings from `.env` file
- Validates with Pydantic
- Singleton pattern with caching
- 12-factor app compliance

### 2. Data Models (`app/models.py`)
- Request/response validation
- Type safety with Pydantic
- Field constraints (e.g., chord 50-2000 mm)
- Auto-generated OpenAPI schemas

### 3. RAG Engine (`app/rag.py`)
- Manages Chroma vector database
- Handles OpenAI embeddings
- Provides similarity search
- Structured result formatting

**How it works:**
1. User submits wing spec
2. RAG converts spec to text query
3. OpenAI embeds the query
4. Chroma performs similarity search
5. Top-K similar airfoils returned

### 4. MCP Tools (`app/mcp_tools.py`)
- Abstract base class for tools
- Tool registry for discovery
- Execution framework
- Structured result formatting

**Built-in tools:**
1. `estimate_downforce` - Calculate wing downforce
2. `predict_flow_influence` - Predict downstream effects

### 5. API Routes (`app/api/routes.py`)
- RESTful endpoint definitions
- Request/response validation
- Proper HTTP semantics
- Dependency injection

**Key endpoints:**
- `POST /api/v1/optimize-wing` - Main feature
- `POST /api/v1/find-similar-airfoils` - RAG search
- `GET /api/v1/tools` - List tools
- `POST /api/v1/tools/{name}` - Execute tool

### 6. Application Factory (`main.py`)
- FastAPI app creation
- Lifespan management (startup/shutdown)
- Middleware configuration
- Exception handlers

---

## Development Workflow

### Week 1: Implementation

**Day 2-3: RAG Integration**
- [ ] Implement `RAGEngine.embed_text()` to call OpenAI embeddings API
- [ ] Implement `RAGEngine.search_similar()` to query Chroma
- [ ] Create search query formatter (wing spec → text)
- [ ] Test with manual queries
- [ ] Write unit tests

**Day 2-3: MCP Tools**
- [ ] Implement `DownforceEstimatorTool.execute()` with aerodynamic calculations
- [ ] Implement `FlowInfluencePredictorTool.execute()` with empirical models
- [ ] Add tool validation
- [ ] Write unit tests

**Day 4: Optimization Endpoint**
- [ ] Implement `/api/v1/optimize-wing` main logic
- [ ] Integrate RAG search
- [ ] Call MCP tools for performance estimation
- [ ] Generate reasoning/explanation
- [ ] Test end-to-end flow

**Day 5: Testing & Polish**
- [ ] Write pytest test suite
- [ ] Fix any bugs
- [ ] Validate HTTP status codes
- [ ] Document any changes

### Week 2: Documentation

**Days 1-2: API Documentation**
- [ ] Create `notebooks/api_walkthrough.ipynb`
- [ ] Document endpoint usage with examples
- [ ] Show RAG search examples
- [ ] Test with running API

**Days 3-4: Technical Report**
- [ ] Architecture diagram
- [ ] Design decisions explained
- [ ] RAG/MCP rationale
- [ ] Performance analysis

**Days 5-6: Final Polish**
- [ ] Code review
- [ ] Final testing
- [ ] README completeness
- [ ] Submission preparation

---

## File Reference

### Configuration
| File | Purpose |
|------|---------|
| `.env.example` | Configuration template (commit to git) |
| `.env` | Actual configuration (DO NOT commit) |
| `app/core/config.py` | Settings loader & validator |

### Models
| File | Purpose |
|------|---------|
| `app/models.py` | All Pydantic models for request/response |

### Business Logic
| File | Purpose |
|------|---------|
| `app/rag.py` | Vector search engine |
| `app/mcp_tools.py` | Tool definitions & registry |
| `app/api/routes.py` | API endpoint handlers |

### Application
| File | Purpose |
|------|---------|
| `main.py` | FastAPI app factory |
| `scripts/load_data.py` | Data loading CLI |

### Data
| File | Purpose |
|------|---------|
| `data/uiuc_airfoils.csv` | Sample airfoil dataset |
| `data/chroma_db/` | Vector database (created at runtime) |

### Tests
| File | Purpose |
|------|---------|
| `tests/test_rag.py` | RAG engine tests (stubs) |
| `tests/test_mcp_tools.py` | Tool tests (stubs) |
| `tests/test_api.py` | API endpoint tests (stubs) |

---

## Common Tasks

### Run the API
```bash
uv run uvicorn main:app --reload
```

### Load data (after CSV changes)
```bash
python scripts/load_data.py --clear
```

### Run tests
```bash
pytest                    # All tests
pytest -v                 # Verbose
pytest --cov=app          # With coverage
pytest tests/test_api.py  # Specific file
```

### Check code style
```bash
# Format code
uv run black app

# Sort imports
uv run isort app

# Type checking (optional)
uv run mypy app
```

### Clean environment
```bash
# Clear Chroma database
rm -rf data/chroma_db/

# Reload data
python scripts/load_data.py
```

---

## Troubleshooting

### Issue: "OPENAI_API_KEY not configured"

**Solution:**
```bash
# 1. Check .env exists
ls .env

# 2. Check it has your key
grep OPENAI_API_KEY .env

# 3. Verify key format (should be sk-...)
```

### Issue: "CSV file not found"

**Solution:**
```bash
# Check file exists
ls data/uiuc_airfoils.csv

# Load with explicit path
python scripts/load_data.py --csv-path ./data/uiuc_airfoils.csv
```

### Issue: Port 8000 already in use

**Solution:**
```bash
# Use different port
uv run uvicorn main:app --reload --port 8001
```

### Issue: uv lock file conflicts

**Solution:**
```bash
# Regenerate lock file
uv lock --refresh
uv sync
```

---

## Next Steps

1. **Install dependencies:** `uv sync`
2. **Configure API key:** Update `.env` with your OpenAI key
3. **Load data:** `python scripts/load_data.py`
4. **Start server:** `uv run uvicorn main:app --reload`
5. **Visit docs:** http://localhost:8000/docs
6. **Start building:** Implement RAG and MCP tools (Week 1)

---

## Questions or Issues?

Refer to:
1. [README.md](README.md) - Project overview
2. Code docstrings - Each module is heavily documented
3. [.env.example](.env.example) - Configuration reference
4. [scripts/load_data.py](scripts/load_data.py) - Data loading details

---

**Good luck! You're ready to start development.** 🚀
