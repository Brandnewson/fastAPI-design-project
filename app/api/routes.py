"""
API route definitions for the Wing Aerodynamic Analyzer.

Routes are organized by domain:
- /api/v1/ - Core optimization endpoints
- /api/v1/tools/ - MCP tool endpoints
- /api/v1/health - System health check

Design principles:
- RESTful semantics (GET, POST, etc.)
- Proper HTTP status codes
- Consistent error responses
- Request/response validation via Pydantic
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.mcp_tools import get_tool_registry
from app.models import (
    OptimizationResponse,
    SimilarAirfoilRequest,
    SimilarAirfoilResponse,
    WingSpecification,
)
from app.rag import get_rag_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["aerodynamic-analysis"])


# Dependency injection
def get_rag_engine_dep():
    """Dependency to inject RAG engine."""
    return get_rag_engine()


def get_tool_registry_dep():
    """Dependency to inject tool registry."""
    return get_tool_registry()


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@router.get(
    "/health",
    response_model=dict,
    summary="Health Check",
    description="Check if the API is running and accessible"
)
async def health_check(settings: Annotated[Settings, Depends(get_settings)]) -> dict:
    """
    Health check endpoint.
    
    Returns:
        dict: Status and version information
    """
    return {
        "status": "healthy",
        "app_name": settings.app_title,
        "version": settings.app_version,
        "environment": settings.app_env
    }


# ============================================================================
# Optimization Endpoints
# ============================================================================

@router.post(
    "/optimize-wing",
    response_model=OptimizationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Optimize Wing Configuration",
    description="Submit a wing specification for aerodynamic optimization analysis"
)
async def optimize_wing(
    request: WingSpecification,
    rag_engine=Depends(get_rag_engine_dep)
) -> OptimizationResponse:
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
        
    Status Codes:
        202: Accepted - Analysis will proceed
        400: Bad Request - Invalid wing specification
        422: Unprocessable Entity - Validation error
        503: Service Unavailable - OpenAI API error
        
    Example:
        POST /api/v1/optimize-wing
        {
            "wing_type": "single_element",
            "chord_mm": 350,
            "span_mm": 1400,
            "target_downforce_kg": 45,
            "operating_speed_kph": 200
        }
    """
    logger.info(f"Optimization request: {request}")
    
    try:
        # Placeholder implementation - to be filled in Week 1 development
        # This will:
        # 1. Call RAG search for similar designs
        # 2. Call MCP tools for performance estimation
        # 3. Aggregate results and reasoning
        # 4. Return OptimizationResponse
        
        raise NotImplementedError("Optimization endpoint implementation pending")
        
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Optimization service not yet implemented"
        )
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Optimization service error"
        )


# ============================================================================
# RAG Search Endpoints
# ============================================================================

@router.post(
    "/find-similar-airfoils",
    response_model=SimilarAirfoilResponse,
    summary="Find Similar Airfoil Designs",
    description="Search for aerodynamic designs similar to your specification"
)
async def find_similar_airfoils(
    request: SimilarAirfoilRequest,
    rag_engine=Depends(get_rag_engine_dep)
) -> SimilarAirfoilResponse:
    """
    Find airfoil profiles similar to the provided wing specification.
    
    Uses RAG (Retrieval-Augmented Generation) to search the aerodynamic
    knowledge base for comparable designs.
    
    Args:
        request: Wing specification and search parameters
        rag_engine: Injected RAG engine instance
        
    Returns:
        SimilarAirfoilResponse: List of similar designs with relevance scores
        
    Example:
        POST /api/v1/find-similar-airfoils
        {
            "wing_spec": {
                "wing_type": "single_element",
                "chord_mm": 350,
                "span_mm": 1400,
                "target_downforce_kg": 45,
                "operating_speed_kph": 200
            },
            "limit": 5
        }
    """
    logger.info(f"Similar airfoil search: {request}")
    
    try:
        # Placeholder implementation - to be filled in Week 1 development
        # This will:
        # 1. Format wing spec as search query
        # 2. Call RAG engine to find similar designs
        # 3. Parse results and format as SimilarAirfoilResponse
        
        raise NotImplementedError("RAG search implementation pending")
        
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG search not yet implemented"
        )
    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service error"
        )


# ============================================================================
# MCP Tool Endpoints
# ============================================================================

@router.get(
    "/tools",
    summary="List Available Tools",
    description="Get list of available MCP tools with schemas"
)
async def list_tools(
    tool_registry=Depends(get_tool_registry_dep)
) -> dict:
    """
    List all available MCP tools.
    
    Returns tool metadata including input schemas for client integration.
    
    Returns:
        dict: Tool catalog with schemas
        
    Example Response:
        {
            "tools": [
                {
                    "name": "estimate_downforce",
                    "description": "Estimate downforce...",
                    "input_schema": {...}
                },
                ...
            ]
        }
    """
    return {
        "tools": tool_registry.list_tools(),
        "count": len(tool_registry.list_tools())
    }


@router.post(
    "/tools/{tool_name}",
    summary="Execute MCP Tool",
    description="Execute a specific MCP tool with provided inputs"
)
async def execute_tool(
    tool_name: str,
    inputs: dict,
    tool_registry=Depends(get_tool_registry_dep)
) -> JSONResponse:
    """
    Execute an MCP tool and return results.
    
    Args:
        tool_name: Identifier of the tool to execute
        inputs: Tool-specific input parameters
        tool_registry: Injected tool registry
        
    Returns:
        JSONResponse: Tool execution result
        
    Status Codes:
        200: Success
        400: Invalid tool or inputs
        503: Tool execution error
        
    Example:
        POST /api/v1/tools/estimate_downforce
        {
            "airfoil": "NACA 23012",
            "speed_kph": 200,
            "chord_mm": 350,
            "span_mm": 1400
        }
    """
    logger.info(f"Tool execution request: {tool_name} with inputs: {inputs}")
    
    try:
        # Placeholder implementation
        # This will:
        # 1. Validate tool exists
        # 2. Execute tool with inputs
        # 3. Return formatted result
        
        raise NotImplementedError("Tool execution implementation pending")
        
    except ValueError as e:
        logger.warning(f"Invalid tool request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tool execution not yet implemented"
        )
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tool execution error"
        )


# ============================================================================
# Management Endpoints
# ============================================================================

@router.post(
    "/admin/clear-cache",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear Vector Database Cache",
    description="Clear all documents from RAG vector store (development only)"
)
async def clear_rag_cache(
    rag_engine=Depends(get_rag_engine_dep),
    settings: Annotated[Settings, Depends(get_settings)] = None
) -> None:
    """
    Clear the RAG vector database cache.
    
    CAUTION: This is destructive and should only be used in development.
    
    Returns:
        None (204 No Content)
        
    Status Codes:
        204: Cache cleared successfully
        403: Operation not allowed (production environment)
    """
    if settings.app_env == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cache clear not allowed in production"
        )
    
    try:
        rag_engine.clear_collection()
        logger.warning("RAG cache cleared")
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache clear failed"
        )
