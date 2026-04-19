"""
Pydantic schemas for AI advice endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class AdviceRequest(BaseModel):
    """Request schema for free-text battery advice."""
    
    device_id: str = Field(
        ...,
        description="Unique device identifier (Android ID)",
        min_length=1,
        max_length=64
    )
    question: str = Field(
        ...,
        description="User's question about their battery",
        min_length=3,
        max_length=500
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "863069505fbdf653",
                "question": "When is the best time to charge my phone?"
            }
        }


class FeatureAdviceRequest(BaseModel):
    """Request schema for feature-based advice."""
    
    device_id: str = Field(
        ...,
        description="Unique device identifier (Android ID)",
        min_length=1,
        max_length=64
    )
    feature: Literal["best_time", "heat", "health", "habits", "fast_charge"] = Field(
        ...,
        description="Feature to get advice for"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "863069505fbdf653",
                "feature": "best_time"
            }
        }


class AdviceResponse(BaseModel):
    """Response schema for AI-generated advice."""
    
    feature: Optional[str] = Field(None, description="Feature that generated this advice")
    question: str = Field(..., description="The question sent to the AI")
    answer: str = Field(..., description="AI-generated personalized advice")
    context_used: str = Field(..., description="Summary of telemetry data used")
    model_used: str = Field(default="gemma4:latest", description="LLM model used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "feature": "best_time",
                "question": "Based on my usage patterns, when is the best time of day for me to charge my phone?",
                "answer": "Based on your data, you're least active between 2-4 AM. This is the ideal charging window.",
                "context_used": "- Battery Health: 95.4%\n- Lowest activity: 3 AM (50mA drain)",
                "model_used": "gemma4:latest"
            }
        }


class AutoAdviceRequest(BaseModel):
    """Request schema for automatic advice based on current state."""
    
    device_id: str = Field(
        ...,
        description="Unique device identifier (Android ID)",
        min_length=1,
        max_length=64
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "863069505fbdf653"
            }
        }


class AutoAdviceResponse(BaseModel):
    """Response schema for automatic advice."""
    
    question_asked: str = Field(
        ...,
        description="The question automatically generated based on current state"
    )
    answer: str = Field(
        ...,
        description="AI-generated personalized advice"
    )
    current_state: dict = Field(
        ...,
        description="Current battery state that triggered this advice"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "question_asked": "My phone is getting hot while charging. What should I do?",
                "answer": "Your battery temperature is 39.5°C which is elevated. Try removing your phone case.",
                "current_state": {
                    "level_percent": 67,
                    "temperature_c": 39.5,
                    "is_charging": True,
                    "health_percent": 94.2
                }
            }
        }


class AdviceHealthResponse(BaseModel):
    """Response schema for advice service health check."""
    
    llm_available: bool = Field(
        ...,
        description="Whether Ollama LLM service is accessible"
    )
    model_name: str = Field(
        ...,
        description="Name of the loaded LLM model"
    )
    status: str = Field(
        ...,
        description="Overall health status"
    )