# Wing Aerodynamic Analyzer API

A FastAPI-based REST API for analyzing front wing aerodynamic impact on downstream components. Uses RAG (Retrieval-Augmented Generation) to search aerodynamic knowledge bases and MCP tools for performance estimation.

## Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key (for embeddings)
- Poetry (for dependency management)

### 1. Setup Environment

```bash
cd c:\Code\fastAPI-design-project
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Install Dependencies

```bash
pip install poetry
poetry install
poetry shell
```

### 3. Load Aerodynamic Data

```bash
python scripts/load_data.py
```

### 4. Run API Server

```bash
poetry run uvicorn main:app --reload
# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

## Project Structure

The codebase follows a clean, modular architecture:

```
fastapi-wing-optimizer/
├── main.py                    # FastAPI app entry point
├── pyproject.toml             # Dependencies (Poetry)
├── .env.example               # Configuration template
├── app/
│   ├── models.py              # Pydantic schemas
│   ├── rag.py                 # RAG engine & vector search
│   ├── mcp_tools.py           # MCP tool definitions
│   ├── core/config.py         # Settings management
│   └── api/routes.py          # API endpoints
├── scripts/load_data.py       # Data loader
├── data/uiuc_airfoils.csv     # Aerodynamic dataset
└── tests/                      # Test suite
```

## Key Design Principles

### 1. Configuration Management
- Environment variables via `.env`
- Pydantic v2 `BaseSettings` for validation
- Singleton pattern with caching

### 2. Dependency Injection
- FastAPI `Depends()` for service injection
- Loose coupling between components

### 3. RAG Architecture
- OpenAI embeddings for semantic search
- Chroma vector database (local, zero-setup)
- LLM-powered design retrieval

### 4. MCP Tools Pattern
- Abstract base class for tool interface
- Tool registry for discovery
- Consistent schemas

### 5. API Design
- RESTful semantics with proper HTTP codes
- Pydantic validation on all endpoints
- Auto-generated Swagger docs

## Environment Configuration

Create `.env` from `.env.example` and add your OpenAI key:

```bash
OPENAI_API_KEY=sk-your-key-here
APP_ENV=development
```

## Getting Started

1. `pip install poetry`
2. `poetry install`
3. `poetry shell`
4. Copy `.env.example` to `.env` and add API key
5. `python scripts/load_data.py`
6. `poetry run uvicorn main:app --reload`
7. Visit `http://localhost:8000/docs`

## Core Endpoints

- `GET /api/v1/health` - Health check
- `POST /api/v1/optimize-wing` - Wing optimization
- `POST /api/v1/find-similar-airfoils` - RAG search
- `GET /api/v1/tools` - List MCP tools
- `POST /api/v1/tools/{tool_name}` - Execute tool

## Implementation Status

✅ **Day 1 Complete:**
- Project structure & scaffolding
- Configuration management
- Pydantic models with validation
- RAG engine framework
- MCP tool architecture
- API routes (stubs)
- Data loader script
- Sample dataset

🚧 **Week 1 Tasks:**
- Implement RAG retrieval
- Build MCP tools
- Optimization endpoint logic
- Unit tests

📚 **Week 2 Tasks:**
- API documentation
- Jupyter notebook examples
- Technical report