"""
Assessment API router for real-time language analysis
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

from src.services.assessment import RealTimeAssessment, save_assessment_data
from src.utils.utils import get_logger
from config.settings import config

router = APIRouter()
logger = get_logger("assessment_router")


class AssessmentRequest(BaseModel):
    user_id: str
    expert: str
    conversation_history: List[Dict[str, str]]
    current_message: str
    language: str = "dutch"  # Language for assessment feedback


@router.post("/assessment")
async def get_assessment(request: AssessmentRequest):
    """Get real-time assessment of user's Dutch language usage"""
    try:
        logger.info(
            f"Assessment request for user {request.user_id}, expert {request.expert}")

        # Initialize assessment system
        from config.settings import config
        assessment_system = RealTimeAssessment(
            hf_token=config.HF_TOKEN or "dummy",
            api_url=config.HF_API_URL,
            default_model=config.DEFAULT_MODEL,
            fallback_model=config.FALLBACK_MODEL
        )

        # Get comprehensive assessment
        assessment = await assessment_system.analyze_conversation(
            user_id=request.user_id,
            expert=request.expert,
            conversation_history=request.conversation_history,
            current_message=request.current_message,
            language=request.language
        )

        # Save assessment data for analytics
        await save_assessment_data(request.user_id, assessment)

        return JSONResponse(assessment)

    except Exception as e:
        logger.error(f"Assessment error: {e}")

        # Return fallback assessment
        fallback_assessment = {
            "timestamp": "error",
            "expert": request.expert,
            "language_analysis": {
                "grammar_score": 5,
                "vocabulary_level": "intermediate",
                "fluency_score": 5,
                "errors": [],
                "corrections": [],
                "improved_version": request.current_message,
                "explanation": "Assessment temporarily unavailable",
                "strengths": ["Keep practicing!"]
            },
            "conversation_flow": {
                "engagement_level": "medium",
                "turn_count": len([msg for msg in request.conversation_history if msg.get("role") == "user"]),
                "avg_message_length": len(request.current_message),
                "topic_consistency": "consistent"
            },
            "expert_specific": {
                "domain": request.expert,
                "scenario_relevance": "medium"
            },
            "learning_progress": {
                "session_messages": 1,
                "learning_momentum": "steady"
            },
            "hints": {
                "language_tips": ["Keep speaking Dutch", "Practice daily"],
                "conversation_tips": ["Ask follow-up questions", "Stay engaged"],
                "expert_tips": ["Use domain-specific vocabulary"],
                "quick_suggestions": ["Speak clearly", "Take your time"]
            },
            "overall_score": {
                "overall_score": 5.0,
                "performance_level": "developing",
                "key_strengths": ["Good effort!"],
                "focus_areas": ["Keep practicing"]
            }
        }

        return JSONResponse({
            "error": str(e),
            "fallback_assessment": fallback_assessment
        }, status_code=200)  # Return 200 to avoid breaking the frontend
