"""
Main router for core application endpoints (index, file uploads, etc.)
"""
from fastapi import APIRouter, Request, Form, File, UploadFile, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import os
import json
from datetime import datetime

from src.services.calibrator import run_calibrator
from src.services.lesson_bot import run_lesson_bot
from src.utils.pdf import generate_pdf
from src.utils.anki import export_anki
from src.utils.audio import generate_audio
from src.utils.utils import ensure_dir, get_logger

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = get_logger("main_router")

# Initialize services
ensure_dir("data")
ensure_dir("data/users")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main application page"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/load_profile")
async def load_profile(user_id: str):
    """Load user profile data"""
    try:
        user_dir = os.path.join("data", "users", user_id)
        profile_path = os.path.join(user_dir, "profile.json")

        if not os.path.exists(profile_path):
            return JSONResponse({"error": "Profile not found"}, status_code=404)

        with open(profile_path, "r") as f:
            profile = json.load(f)

        return JSONResponse(profile)
    except Exception as e:
        logger.error(f"Error loading profile: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools_well_known():
    """Respond to Chrome DevTools well-known appspecific request.

    Chrome sometimes requests this file when DevTools are open (source maps
    / appspecific settings). Return a minimal JSON to avoid 404 noise in logs.
    """
    payload = {
        "name": "com.chrome.devtools",
        "description": "DevTools app-specific config placeholder",
        "version": "1"
    }
    return JSONResponse(payload)


@router.post("/api/generate-lesson")
async def generate_lesson(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    ancestry: str = Form("EAS"),
    mbti: str = Form("INTJ"),
    target_language: str = Form(...),
    log_text: str = Form("")
):
    """Generate lesson content based on daily activities"""
    try:
        logger.info(f"Generating lesson for user: {user_id}")

        user_dir = os.path.join("data", "users", user_id)
        ensure_dir(user_dir)

        # Check if user profile exists, create or update it
        profile_path = os.path.join(user_dir, "profile.json")
        if os.path.exists(profile_path):
            with open(profile_path, "r") as f:
                profile = json.load(f)
        else:
            profile = {
                "user_id": user_id,
                "created_at": str(datetime.utcnow())
            }

        # Update profile
        profile["ancestry"] = ancestry
        profile["mbti"] = mbti
        profile["target_language"] = target_language
        profile["last_lesson_at"] = str(datetime.utcnow())

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

        # Generate personalized learning method based on MBTI
        # Using default percentile without DNA
        method = run_calibrator(50, mbti)

        # Generate lesson content
        lesson_result = run_lesson_bot(log_text, target_language)
        words = lesson_result["words"]
        sentences = lesson_result["sentences"]

        # Prepare results
        results = {
            "method": method,
            "words": words,
            "sentences": sentences,
            "user_id": user_id
        }

        # Generate files in background
        background_tasks.add_task(generate_lesson_outputs, user_id, results)

        return JSONResponse(results)

    except Exception as e:
        logger.error(f"Error generating lesson for {user_id}: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def generate_lesson_outputs(user_id: str, results: dict):
    """Generate Anki deck and audio for lesson content"""
    try:
        user_dir = os.path.join("data", "users", user_id)

        # Generate Anki deck
        if "words" in results and "sentences" in results:
            lesson_data = {
                "words": results["words"],
                "sentences": results["sentences"]
            }
            anki_path = export_anki(lesson_data, user_id)
            results["anki_path"] = convert_path_to_url(anki_path)
            logger.info(f"Generated Anki: {anki_path}")

        # Generate audio
        if "sentences" in results:
            audio_path = generate_audio(results["sentences"], user_id, "dutch")
            results["audio_path"] = convert_path_to_url(audio_path)
            logger.info(f"Generated Audio: {audio_path}")

    except Exception as e:
        logger.error(f"Error generating lesson outputs for {user_id}: {e}")


def convert_path_to_url(file_path: str) -> str:
    """Convert local file path to HTTP URL"""
    if file_path and os.path.exists(file_path):
        # Convert Windows path separators to URL separators
        url_path = file_path.replace("\\", "/")
        return f"/{url_path}"
    return None


@router.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """Get user profile"""
    try:
        profile_path = os.path.join("data", "users", user_id, "profile.json")
        if os.path.exists(profile_path):
            with open(profile_path, "r") as f:
                profile = json.load(f)

            return JSONResponse({
                "exists": True,
                "profile": profile
            })
        else:
            return JSONResponse({"exists": False})

    except Exception as e:
        logger.error(f"Error getting profile for {user_id}: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/download/pdf/{user_id}")
async def download_pdf(user_id: str):
    """Download PDF report for user"""
    logger.info(f"PDF download request for user: {user_id}")
    try:
        # Support multiple possible filenames (legacy/name variations)
        candidates = [
            os.path.join("data", "users", user_id,
                         "TYPORAX_COMPREHENSIVE_REPORT.pdf"),
            os.path.join("data", "users", user_id,
                         "GENELINGUA_COMPREHENSIVE_REPORT.pdf"),
            os.path.join("data", "users", user_id, "GENELINGUA_Report.pdf"),
        ]

        for path in candidates:
            if os.path.exists(path):
                # Use a friendly download filename based on existing file
                return FileResponse(
                    path,
                    media_type="application/pdf",
                    filename=f"GeneLingua_Report_{user_id}.pdf"
                )

        return JSONResponse({"error": "PDF not found"}, status_code=404)
    except Exception as e:
        logger.error(f"Error downloading PDF for {user_id}: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/download/anki/{user_id}")
async def download_anki(user_id: str):
    """Download Anki CSV for user"""
    try:
        # Accept multiple possible Anki filenames produced by different modules
        candidates = [
            os.path.join("data", "users", user_id, "typorax_anki.csv"),
            os.path.join("data", "users", user_id, "genelingua_anki.csv"),
            os.path.join("data", "users", user_id, "anki_deck.csv"),
        ]

        for path in candidates:
            if os.path.exists(path):
                return FileResponse(
                    path,
                    media_type="text/csv",
                    filename=f"GeneLingua_Anki_{user_id}.csv"
                )

        return JSONResponse({"error": "Anki file not found"}, status_code=404)
    except Exception as e:
        logger.error(f"Error downloading Anki for {user_id}: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/download/audio/{user_id}")
async def download_audio(user_id: str):
    """Download audio guide for user"""
    try:
        audio_path = os.path.join("data", "users", user_id, "lesson_audio.mp3")
        if os.path.exists(audio_path):
            return FileResponse(
                audio_path,
                media_type="audio/mpeg",
                filename=f"TyporaX_Audio_{user_id}.mp3"
            )
        else:
            return JSONResponse({"error": "Audio file not found"}, status_code=404)
    except Exception as e:
        logger.error(f"Error downloading audio for {user_id}: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
