"""
AI Advice Endpoints.
Uses local Ollama LLM to generate personalized battery advice.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database.connection import get_db
from app.services.llm_service import OllamaLLMService
from app.services.telemetry_summary import get_telemetry_summary
from app.api.v1.schemas.advice import (
    AdviceRequest,
    AdviceResponse,
    FeatureAdviceRequest,
    AutoAdviceRequest,
    AutoAdviceResponse,
    AdviceHealthResponse,
)

router = APIRouter(prefix="/advice", tags=["advice"])

# Initialize LLM service
llm = OllamaLLMService(model="gemma4:latest")

# Feature to question mapping
FEATURE_QUESTIONS = {
    "best_time": "Based on my usage patterns and battery data, when is the best time of day for me to charge my phone? Give a specific time window.",
    "heat": "Why does my battery get hot and what specific steps can I take to prevent overheating based on my actual usage data?",
    "health": "Is my battery health declining at a normal rate? What can I do to preserve my current battery health?",
    "habits": "Based on my charging habits, what am I doing well and what should I change to extend battery life?",
    "fast_charge": "Is fast charging damaging my battery? Based on my usage patterns, should I use fast charging or switch to slower charging?",
}


@router.post(
    "/feature",
    response_model=AdviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get feature-based personalized advice",
    description="Get AI-generated advice for a specific battery feature.",
)
async def get_feature_advice(
    request: FeatureAdviceRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate personalized battery advice for a specific feature.
    
    Available features:
    - **best_time**: Best time of day to charge
    - **heat**: Battery overheating analysis
    - **health**: Battery health assessment
    - **habits**: Charging habit analysis
    - **fast_charge**: Fast charging impact
    """
    try:
        # Get the question for this feature
        question = FEATURE_QUESTIONS.get(request.feature)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown feature: {request.feature}"
            )
        
        # Get user's telemetry summary
        context = await get_telemetry_summary(db, request.device_id, days=7)
        
        # Generate response with Ollama
        answer = await llm.generate(question, context)
        
        return AdviceResponse(
            feature=request.feature,
            question=question,
            answer=answer,
            context_used=context,
            model_used=llm.model,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate advice: {str(e)}",
        )


@router.get(
    "/features",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get available advice features",
    description="Returns the list of available feature buttons and their descriptions.",
)
async def get_available_features():
    """
    Get all available advice features.
    """
    return {
        "features": [
            {
                "id": "best_time",
                "title": "Best Time to Charge",
                "description": "Find the optimal time of day to charge your phone",
                "icon": "schedule"
            },
            {
                "id": "heat",
                "title": "Battery Heat Analysis",
                "description": "Understand why your battery gets hot and how to prevent it",
                "icon": "thermostat"
            },
            {
                "id": "health",
                "title": "Health Check",
                "description": "Check if your battery is aging normally",
                "icon": "favorite"
            },
            {
                "id": "habits",
                "title": "Charging Habits",
                "description": "Get personalized feedback on your charging habits",
                "icon": "battery_charging_full"
            },
            {
                "id": "fast_charge",
                "title": "Fast Charging Impact",
                "description": "See if fast charging is affecting your battery",
                "icon": "bolt"
            }
        ]
    }


@router.post(
    "/ask",
    response_model=AdviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask free-text battery question",
    description="Ask any question about battery usage and get AI-generated advice based on your telemetry data.",
)
async def ask_advice(
    request: AdviceRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate personalized battery advice using local LLM.
    
    - **device_id**: Your device's unique identifier
    - **question**: Any question about battery usage, charging, or health
    """
    try:
        # Get user's telemetry summary
        context = await get_telemetry_summary(db, request.device_id, days=7)
        
        # Generate response with Ollama
        answer = await llm.generate(request.question, context)
        
        return AdviceResponse(
            feature=None,
            question=request.question,
            answer=answer,
            context_used=context,
            model_used=llm.model,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate advice: {str(e)}",
        )


@router.get(
    "/auto/{device_id}",
    response_model=AutoAdviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get automatic battery advice",
    description="Automatically generates advice based on the current battery state.",
)
async def auto_advice(
    device_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Automatically generate advice based on current battery conditions.
    
    - **device_id**: Your device's unique identifier
    """
    try:
        # Get current battery state
        query = text("""
            SELECT 
                level_percent,
                temperature_c,
                is_charging,
                health_percent,
                current_ma,
                voltage_v,
                actual_capacity_mah
            FROM battery_data.battery_telemetry_raw
            WHERE device_id = :device_id
            ORDER BY time DESC
            LIMIT 1
        """)
        
        result = await db.execute(query, {"device_id": device_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for device: {device_id}",
            )
        
        current_state = {
            "level_percent": int(row.level_percent) if row.level_percent else 0,
            "temperature_c": float(row.temperature_c) if row.temperature_c else 0,
            "is_charging": bool(row.is_charging),
            "health_percent": float(row.health_percent) if row.health_percent else 100,
        }
        
        # Determine automatic question based on current state
        if current_state["temperature_c"] > 38:
            question = "My phone battery is getting hot. What should I do?"
        elif current_state["level_percent"] < 20 and not current_state["is_charging"]:
            question = "My battery is critically low. Should I charge it now or wait?"
        elif current_state["is_charging"] and current_state["level_percent"] > 90:
            question = "My battery is almost full. Should I unplug it now?"
        elif current_state["health_percent"] < 80:
            question = "My battery health is declining. How can I preserve it?"
        else:
            question = "What can I do to maintain good battery health?"
        
        # Get context and generate answer
        context = await get_telemetry_summary(db, device_id, days=7)
        answer = await llm.generate(question, context)
        
        return AutoAdviceResponse(
            question_asked=question,
            answer=answer,
            current_state=current_state,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate automatic advice: {str(e)}",
        )


@router.get(
    "/health",
    response_model=AdviceHealthResponse,
    summary="Check advice service health",
    description="Check if the LLM service is available and ready.",
)
async def advice_health_check():
    """
    Health check for the advice service.
    """
    llm_available = await llm.health_check()
    
    return AdviceHealthResponse(
        llm_available=llm_available,
        model_name=llm.model,
        status="healthy" if llm_available else "degraded",
    )