"""
Router for scenario-based lessons (text-only scaffold).

Endpoints:
 - POST /api/scenario/start  -> start a scenario session
 - POST /api/scenario/submit -> submit learner text and receive agent response
 - POST /api/scenario/finish -> finish the session, score attempt and save progress

This file uses file-based progress storage consistent with the rest of the project.
"""
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import os
import json
from datetime import datetime

from src.experts.medical_call_expert import MedicalCallExpert
from src.experts.tax_authority_expert import run_tax_authority_conversation
from src.utils.utils import ensure_dir, get_logger

router = APIRouter()
logger = get_logger("scenario_router")


@router.post("/start")
async def start_scenario(user_id: str = Form(...), scenario_id: str = Form(...)):
    try:
        # Tax authority scenarios use new synchronous function
        if scenario_id == "tax_authority":
            greeting = "Goedemorgen, u spreekt met de Belastingdienst. Waarmee kan ik u helpen?"
            session = {
                "session_id": f"tax_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "scenario_id": scenario_id,
                "user_id": user_id,
                "started_at": datetime.now().isoformat(),
                "agent_greeting": greeting,
                "last_agent": greeting,
                "scenario_name": "Belastingdienst — Nederlandse Belastingaangiftetraining",
                "history": []
            }
        elif scenario_id.startswith("medical_"):
            expert = MedicalCallExpert(scenario_id)
            session = expert.start_session(user_id)
        else:
            raise ValueError(f"Unknown scenario type: {scenario_id}")

        # Ensure user dir
        user_dir = os.path.join("data", "users", user_id)
        ensure_dir(user_dir)

        return JSONResponse({"ok": True, "session": session})
    except Exception as e:
        logger.error(
            f"Error starting scenario {scenario_id} for {user_id}: {e}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@router.post("/submit")
async def submit_turn(user_id: str = Form(...), scenario_id: str = Form(...), session_id: str = Form(""), text_input: str = Form(...)):
    try:
        # Tax authority scenarios use new synchronous function
        if scenario_id == "tax_authority":
            result = run_tax_authority_conversation(
                scenario="tax_authority",
                user_input=text_input,
                conversation_history=[]
            )
            agent_reply = result.get("agent_response", "")
            feedback = result.get("feedback", {})
        elif scenario_id.startswith("medical_"):
            expert = MedicalCallExpert(scenario_id)
            session = {"session_id": session_id or str(datetime.utcnow().timestamp(
            )), "user_id": user_id, "scenario_id": scenario_id, "history": []}
            agent_reply = expert.respond_to_text(session, text_input)
            feedback = {}
        else:
            raise ValueError(f"Unknown scenario type: {scenario_id}")

        session = {"session_id": session_id or str(datetime.utcnow().timestamp(
        )), "user_id": user_id, "scenario_id": scenario_id, "history": [], "feedback": feedback}

        return JSONResponse({"ok": True, "agent_reply": agent_reply, "session": session})
    except Exception as e:
        logger.error(f"Error submitting turn: {e}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@router.post("/finish")
async def finish_scenario(user_id: str = Form(...), scenario_id: str = Form(...), transcript: str = Form(...)):
    try:
        # Score attempt based on scenario type
        if scenario_id == "tax_authority":
            # Use rubric-based scoring for tax authority
            rubric_items = ["name", "date_of_birth",
                            "state_reason_for_call", "ask_for_next_steps_or_followup"]
            lower = transcript.lower()
            found = sum(1 for item in rubric_items if any(
                w in lower for w in [item, "name", "geboortedatum", "reden", "volgende"]))
            word_count = len(transcript.split())

            result = {
                "score": min(100, max(0, (found / len(rubric_items)) * 100)),
                "items_found": found,
                "word_count": word_count,
                "feedback": "Good practice session!" if found >= 2 else "Try to include all required information."
            }
        elif scenario_id.startswith("medical_"):
            expert = MedicalCallExpert(scenario_id)
            result = expert.score_attempt(transcript)
        else:
            raise ValueError(f"Unknown scenario type: {scenario_id}")

        # Save attempt to user's progress
        user_dir = os.path.join("data", "users", user_id)
        ensure_dir(user_dir)
        progress_path = os.path.join(user_dir, "progress.json")

        if os.path.exists(progress_path):
            with open(progress_path, "r", encoding="utf-8") as f:
                try:
                    progress = json.load(f)
                except Exception:
                    progress = {"attempts": []}
        else:
            progress = {"attempts": []}

        attempt = {
            "scenario_id": scenario_id,
            "transcript": transcript,
            "result": result,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        progress["attempts"].append(attempt)

        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)

        return JSONResponse({"ok": True, "result": result})
    except Exception as e:
        logger.error(f"Error finishing scenario: {e}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@router.get("/progress/{user_id}")
async def get_user_progress(user_id: str):
    """Get user's comprehensive progress data for analytics"""
    try:
        from src.services.tracker import AssessmentTracker

        tracker = AssessmentTracker(user_id)
        progress = tracker.get_progress_summary()

        # Load weekly summary if available
        weekly_path = os.path.join(
            "data", "users", user_id, "analytics", "weekly_summary.json")
        weekly_summary = {}
        if os.path.exists(weekly_path):
            with open(weekly_path, "r", encoding="utf-8") as f:
                weekly_summary = json.load(f)

        # Load error patterns if available
        error_path = os.path.join(
            "data", "users", user_id, "analytics", "error_patterns.json")
        error_patterns = {}
        if os.path.exists(error_path):
            with open(error_path, "r", encoding="utf-8") as f:
                error_patterns = json.load(f)

        # Load all sessions for charts
        sessions_dir = os.path.join("data", "users", user_id, "sessions")
        sessions = []
        if os.path.exists(sessions_dir):
            for session_file in os.listdir(sessions_dir):
                if session_file.endswith(".json") and "_metadata" not in session_file:
                    with open(os.path.join(sessions_dir, session_file), "r", encoding="utf-8") as f:
                        try:
                            session_data = json.load(f)
                            # Ensure expert field exists for backward compatibility
                            if "expert" not in session_data:
                                session_data["expert"] = session_data.get("assessments", [{}])[0].get(
                                    "expert", "healthcare") if session_data.get("assessments") else "healthcare"
                            sessions.append(session_data)
                        except:
                            pass

        return JSONResponse({
            "ok": True,
            "progress": progress,
            "weekly_summary": weekly_summary,
            "error_patterns": error_patterns,
            "sessions": sessions[-20:] if sessions else []  # Last 20 sessions
        })
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
