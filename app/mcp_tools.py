"""
MCP (Model Context Protocol) tool definitions and execution.

This module defines the tools available through the MCP interface:
- Tool schemas for Claude/LLM integration
- Tool execution implementations
- Tool result formatting

Design pattern: Strategy pattern for pluggable tool implementations

These tools are exposed via:
1. Direct API endpoints (POST /api/v1/tools/{tool_name})
2. Through Claude as MCP tools for agentic workflows
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from app.models import DownforceEstimateInput, ToolOutput

logger = logging.getLogger(__name__)


class MCPTool(ABC):
    """
    Abstract base class for MCP tool implementations.
    
    All MCP tools must implement this interface to ensure:
    - Consistent input/output formats
    - Proper error handling
    - Tool metadata for schema generation
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> dict:
        """
        JSON schema for tool input validation.
        
        Returns:
            dict: Pydantic schema for input parameters
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> dict:
        """
        Execute the tool with provided arguments.
        
        Args:
            **kwargs: Tool-specific input parameters
            
        Returns:
            dict: Tool-specific result
            
        Raises:
            ValueError: If input validation fails
            Exception: If execution fails
        """
        pass


class DownforceEstimatorTool(MCPTool):
    """
    Tool for estimating downforce produced by a wing configuration.
    
    Uses aerodynamic data from UIUC airfoil database and interpolation
    to estimate downforce at given speed and geometry.
    
    Workflow:
    1. Look up airfoil in database
    2. Get coefficients for airfoil
    3. Calculate downforce based on speed, area, and coefficients
    4. Return estimate with confidence bounds
    """

    @property
    def name(self) -> str:
        """Tool identifier."""
        return "estimate_downforce"

    @property
    def description(self) -> str:
        """Tool description."""
        return (
            "Estimate downforce production for a wing configuration. "
            "Takes airfoil name, speed, and geometry, returns expected downforce. "
            "Uses aerodynamic coefficients from reference database."
        )

    @property
    def input_schema(self) -> dict:
        """
        Input schema for downforce estimation.
        
        Returns:
            dict: Pydantic schema
        """
        return DownforceEstimateInput.model_json_schema()

    async def execute(self, **kwargs) -> dict:
        """
        Execute downforce estimation.
        
        Args:
            airfoil (str): Airfoil designation
            speed_kph (float): Operating speed
            chord_mm (float): Chord length
            span_mm (float): Span length
            
        Returns:
            dict: Estimated downforce and characteristics
            
        Implementation placeholder - to be filled in development
        """
        logger.info(f"Executing downforce estimation: {kwargs}")
        
        # Placeholder implementation
        # In Week 1 development, this will:
        # 1. Query aerodynamic database for airfoil
        # 2. Interpolate coefficients
        # 3. Calculate lift/downforce using: L = 0.5 * rho * v^2 * S * CL
        
        return {
            "airfoil": kwargs.get("airfoil"),
            "estimated_downforce_kg": 45.2,
            "confidence_percent": 85.0,
            "calculation_method": "database_lookup"
        }


class FlowInfluencePredictorTool(MCPTool):
    """
    Tool for predicting how upstream wing affects downstream components.
    
    Predicts:
    - Wake deficit downstream
    - Vortex strength
    - Effective angle of attack on downstream elements
    
    Uses empirical models based on wing geometry and operating conditions.
    """

    @property
    def name(self) -> str:
        """Tool identifier."""
        return "predict_flow_influence"

    @property
    def description(self) -> str:
        """Tool description."""
        return (
            "Predict downstream flow effects from a wing configuration. "
            "Returns wake deficit, vortex characteristics, and impact on "
            "downstream elements like splitter and diffuser."
        )

    @property
    def input_schema(self) -> dict:
        """
        Input schema for flow influence prediction.
        
        Returns:
            dict: Pydantic schema describing required inputs
        """
        # Placeholder - to be defined in development
        return {
            "type": "object",
            "properties": {
                "wing_chord_mm": {"type": "number"},
                "wing_span_mm": {"type": "number"},
                "downstream_distance_mm": {"type": "number"},
                "geometry": {"type": "string"}
            },
            "required": ["wing_chord_mm", "wing_span_mm"]
        }

    async def execute(self, **kwargs) -> dict:
        """
        Execute flow influence prediction.
        
        Returns:
            dict: Flow field characteristics downstream
            
        Implementation placeholder - to be filled in development
        """
        logger.info(f"Executing flow influence prediction: {kwargs}")
        
        # Placeholder implementation
        # In development, this will use empirical models or lookup tables
        
        return {
            "wake_deficit_percent": 15.0,
            "vortex_strength": 3.2,
            "downstream_cl_change": -0.08,
            "confidence_percent": 72.0
        }


class MCPToolRegistry:
    """
    Registry and executor for MCP tools.
    
    Responsibilities:
    - Maintain catalog of available tools
    - Execute tools with validation
    - Format errors and results consistently
    - Provide tool schemas for LLM integration
    
    Design pattern: Registry pattern
    """

    def __init__(self):
        """Initialize tool registry with default tools."""
        self._tools: dict[str, MCPTool] = {}
        self._register_default_tools()
        logger.info("MCP Tool Registry initialized")

    def _register_default_tools(self) -> None:
        """Register built-in tools."""
        self.register(DownforceEstimatorTool())
        self.register(FlowInfluencePredictorTool())

    def register(self, tool: MCPTool) -> None:
        """
        Register a new tool in the registry.
        
        Args:
            tool: Tool implementation to register
            
        Raises:
            ValueError: If tool name already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[MCPTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool identifier
            
        Returns:
            MCPTool or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        """
        List all available tools with schemas.
        
        Returns:
            list[dict]: Tool metadata for client discovery
            
        Example:
            >>> registry.list_tools()
            [
                {
                    "name": "estimate_downforce",
                    "description": "...",
                    "input_schema": {...}
                },
                ...
            ]
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in self._tools.values()
        ]

    async def execute_tool(self, tool_name: str, **kwargs) -> ToolOutput:
        """
        Execute a tool and return formatted output.
        
        Args:
            tool_name: Identifier of tool to execute
            **kwargs: Tool-specific arguments
            
        Returns:
            ToolOutput: Execution result with metadata
            
        Raises:
            ValueError: If tool not found or input invalid
        """
        tool = self.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' not found")

        start_time = time.time()
        try:
            result = await tool.execute(**kwargs)
            execution_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            return ToolOutput(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time_ms=execution_time_ms
            )
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Tool '{tool_name}' failed: {e}")
            return ToolOutput(
                tool_name=tool_name,
                success=False,
                result=None,
                error_message=str(e),
                execution_time_ms=execution_time_ms
            )


# Global tool registry instance
_tool_registry: Optional[MCPToolRegistry] = None


def get_tool_registry() -> MCPToolRegistry:
    """
    Get or initialize the global MCP tool registry (singleton).
    
    Returns:
        MCPToolRegistry: Initialized registry
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = MCPToolRegistry()
    return _tool_registry


def reset_tool_registry() -> None:
    """Reset the global tool registry (primarily for testing)."""
    global _tool_registry
    _tool_registry = None
