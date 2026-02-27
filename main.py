"""
FastAPI application factory and configuration.

Entry point for the Wing Aerodynamic Analyzer API.

Usage:
    Development:
        uvicorn main:app --reload --host 0.0.0.0 --port 8000
        
    Production:
        gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# Lifespan Context Manager
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
    
    Startup:
    - Initialize settings
    - Validate API keys
    - Initialize RAG engine and vector database
    - Register MCP tools
    
    Shutdown:
    - Clean up resources
    - Close database connections
    """
    logger.info("=" * 80)
    logger.info("Starting Wing Aerodynamic Analyzer API")
    logger.info("=" * 80)
    
    try:
        settings = get_settings()
        logger.info(f"Environment: {settings.app_env}")
        logger.info(f"Debug mode: {settings.app_debug}")
        logger.info(f"Vector DB path: {settings.chroma_path}")
        logger.info(f"Airfoil data path: {settings.airfoil_data_path}")
        
        # Validate API keys before startup
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY not configured. "
                "Please set it in .env file or environment variables."
            )
        logger.info("✓ OpenAI API key configured")
        
        # Initialize RAG engine (lazy-loaded, but validate here)
        from app.rag import get_rag_engine
        rag_engine = get_rag_engine(settings)
        logger.info("✓ RAG engine initialized")
        
        # Initialize MCP tool registry
        from app.mcp_tools import get_tool_registry
        tool_registry = get_tool_registry()
        logger.info(f"✓ MCP tool registry initialized ({len(tool_registry.list_tools())} tools)")
        
        logger.info("=" * 80)
        logger.info("API startup complete - ready to accept requests")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.critical(f"Startup failed: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("=" * 80)
    logger.info("Shutting down Wing Aerodynamic Analyzer API")
    logger.info("=" * 80)


# =============================================================================
# FastAPI Application
# =============================================================================

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Configuration includes:
    - Metadata and documentation
    - CORS middleware
    - Exception handlers
    - Route registration
    - Lifespan management
    
    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_title,
        description=(
            "API for analyzing front wing aerodynamic impact on downstream components. "
            "Uses RAG (Retrieval-Augmented Generation) to search aerodynamic databases "
            "and MCP tools for performance estimation."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # =========================================================================
    # CORS Middleware
    # =========================================================================
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_debug else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # =========================================================================
    # Exception Handlers
    # =========================================================================
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        """Handle validation errors gracefully."""
        logger.warning(f"Validation error: {exc}")
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Handle unexpected errors."""
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # =========================================================================
    # Route Registration
    # =========================================================================
    
    app.include_router(router)
    
    # =========================================================================
    # Root Endpoint
    # =========================================================================
    
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Wing Aerodynamic Analyzer API",
            "version": settings.app_version,
            "docs": "/docs",
            "status_url": "/api/v1/health"
        }
    
    logger.info("FastAPI application created successfully")
    return app


# Create application instance
app = create_app()


# =============================================================================
# Development Server Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        log_level=settings.log_level.lower()
    )
