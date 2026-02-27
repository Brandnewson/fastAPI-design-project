"""
Pydantic models for request/response validation.

These models define the contract for all API endpoints and internal communication.
They provide automatic validation, documentation, and type safety.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class WingType(str, Enum):
    """Enumeration of supported wing types."""
    SINGLE_ELEMENT = "single_element"
    DOUBLE_ELEMENT = "double_element"
    TRIPLE_ELEMENT = "triple_element"
    CUSTOM = "custom"


class AirfoilProfile(BaseModel):
    """
    Represents an airfoil profile from the database.
    
    Attributes:
        name: NACA/other designation (e.g., "NACA 23012")
        description: Brief description of the airfoil characteristics
        thickness_percent: Maximum thickness as % of chord
        camber_percent: Maximum camber as % of chord
    """
    name: str = Field(..., description="Airfoil designation")
    description: Optional[str] = Field(None, description="Airfoil characteristics")
    thickness_percent: float = Field(..., description="Max thickness (% of chord)")
    camber_percent: float = Field(..., description="Max camber (% of chord)")


class WingSpecification(BaseModel):
    """
    Input specification for a wing design.
    
    Attributes:
        wing_type: Type of wing element configuration
        chord_mm: Chord length in millimeters
        span_mm: Span length in millimeters
        target_downforce_kg: Desired downforce target in kilograms
        operating_speed_kph: Operating speed in kilometers per hour
    """
    wing_type: WingType = Field(..., description="Wing configuration type")
    chord_mm: float = Field(
        ..., 
        gt=50,
        lt=2000,
        description="Chord length (mm), must be 50-2000mm"
    )
    span_mm: float = Field(
        ...,
        gt=100,
        lt=3000,
        description="Span length (mm), must be 100-3000mm"
    )
    target_downforce_kg: float = Field(
        ...,
        gt=1,
        lt=500,
        description="Target downforce (kg), must be 1-500kg"
    )
    operating_speed_kph: float = Field(
        ...,
        gt=10,
        lt=400,
        description="Operating speed (kph), must be 10-400kph"
    )

    @field_validator("chord_mm", "span_mm", "target_downforce_kg", "operating_speed_kph")
    @classmethod
    def validate_positive(cls, v):
        """Ensure all numeric fields are positive."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v


class AeroPerformanceEstimate(BaseModel):
    """
    Estimated aerodynamic performance for a configuration.
    
    Attributes:
        downforce_kg: Estimated downforce in kilograms
        downforce_variance_percent: Estimated variance / uncertainty
        drag_coefficient: Estimated drag coefficient
        efficiency_ratio: Downforce to drag ratio (higher is better)
    """
    downforce_kg: float = Field(..., description="Estimated downforce")
    downforce_variance_percent: float = Field(..., description="Uncertainty margin")
    drag_coefficient: float = Field(..., description="Estimated drag coefficient")
    efficiency_ratio: float = Field(..., description="Downforce/drag ratio")


class SimilarConfigurationResult(BaseModel):
    """
    Result from similarity search for comparable wing configurations.
    
    Attributes:
        rank: Position in results (1-based)
        airfoil_name: Name of matched airfoil
        similarity_score: 0-1 similarity metric
        performance: Associated performance metrics
        source: Where this data comes from (database, literature, etc.)
    """
    rank: int = Field(..., description="Result ranking")
    airfoil_name: str = Field(..., description="Matched airfoil name")
    similarity_score: float = Field(..., ge=0, le=1, description="Similarity metric 0-1")
    performance: AeroPerformanceEstimate
    source: str = Field(..., description="Data source")


class OptimizationResponse(BaseModel):
    """
    Response from optimization endpoint.
    
    Attributes:
        job_id: Unique identifier for this optimization job
        status: Current processing status
        recommended_airfoil: Best matching airfoil profile
        estimated_performance: Predicted aerodynamic characteristics
        similar_configurations: List of comparable reference designs
        reasoning: Explanation of optimization approach
        timestamp: When optimization was completed
    """
    job_id: UUID = Field(default_factory=uuid4, description="Unique job identifier")
    status: str = Field(..., description="Processing status")
    recommended_airfoil: AirfoilProfile
    estimated_performance: AeroPerformanceEstimate
    similar_configurations: list[SimilarConfigurationResult] = Field(
        default_factory=list,
        description="Reference configurations from database"
    )
    reasoning: str = Field(..., description="Explanation of recommendations")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ToolInput(BaseModel):
    """
    Generic input for MCP tool invocation.
    
    Base class for specific tool inputs.
    """
    pass


class DownforceEstimateInput(ToolInput):
    """
    Input for downforce estimation MCP tool.
    
    Attributes:
        airfoil: Airfoil profile name
        speed_kph: Operating speed
        chord_mm: Wing chord length
        span_mm: Wing span length
    """
    airfoil: str = Field(..., description="Airfoil name")
    speed_kph: float = Field(..., gt=0, description="Operating speed")
    chord_mm: float = Field(..., gt=0, description="Chord length")
    span_mm: float = Field(..., gt=0, description="Span length")


class ToolOutput(BaseModel):
    """
    Output response from MCP tool execution.
    
    Attributes:
        tool_name: Name of the tool that was executed
        success: Whether execution succeeded
        result: The computed result
        error_message: Error description if execution failed
        execution_time_ms: Time taken to execute (milliseconds)
    """
    tool_name: str
    success: bool
    result: Optional[dict] = None
    error_message: Optional[str] = None
    execution_time_ms: float


class SimilarAirfoilRequest(BaseModel):
    """
    Request for finding similar airfoil profiles via RAG.
    
    Attributes:
        wing_spec: Wing specification to match against
        limit: Maximum number of results to return
    """
    wing_spec: WingSpecification
    limit: int = Field(default=5, ge=1, le=20, description="Result limit")


class SimilarAirfoilResponse(BaseModel):
    """
    Response containing similar airfoil matches from RAG search.
    
    Attributes:
        query_spec: Original query specification
        results: List of similar airfoils with relevance scores
        search_time_ms: Time taken for search
    """
    query_spec: WingSpecification
    results: list[SimilarConfigurationResult]
    search_time_ms: float
