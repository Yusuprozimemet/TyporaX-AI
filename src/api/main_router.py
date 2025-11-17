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

from src.services.dna_engine import DNAPolygenicEngine
from src.services.calibrator import run_calibrator
from src.services.tracker import run_tracker
from src.services.lesson_bot import run_lesson_bot
from src.utils.pdf import generate_pdf
from src.utils.anki import export_anki
from src.utils.audio import generate_audio
from src.utils.dna_plot import generate_dna_plots
from src.utils.utils import ensure_dir, get_logger

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = get_logger("main_router")

# Initialize services
engine = DNAPolygenicEngine()
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


@router.post("/api/process")
async def process_user_data(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    ancestry: str = Form(...),
    mbti: str = Form(...),
    target_language: str = Form(...),
    log_text: str = Form(""),
    dna_file: Optional[UploadFile] = File(None)
):
    """Process user data and generate personalized learning plan"""
    try:
        logger.info(f"Processing request for user: {user_id}")

        # Create user directory
        user_dir = os.path.join("data", "users", user_id)
        ensure_dir(user_dir)

        # Save user profile
        profile = {
            "user_id": user_id,
            "ancestry": ancestry,
            "mbti": mbti,
            "target_language": target_language,
            "created_at": str(datetime.utcnow())
        }

        with open(os.path.join(user_dir, "profile.json"), "w") as f:
            json.dump(profile, f, indent=2)

        # Process DNA file if provided
        dna_report = None
        if dna_file and dna_file.filename:
            dna_path = os.path.join(user_dir, "genome.txt")
            with open(dna_path, "wb") as f:
                content = await dna_file.read()
                f.write(content)

            dna_report = engine.generate_report(dna_path, ancestry)

        # Generate learning components
        # Extract DNA percentile from report or use default
        dna_percentile = 50  # default
        if dna_report and 'pgs_results' in dna_report and 'percentile' in dna_report['pgs_results']:
            dna_percentile = dna_report['pgs_results']['percentile']

        method = run_calibrator(dna_percentile, mbti)

        progress = run_tracker(user_dir)
        lesson_result = run_lesson_bot(log_text, target_language)
        words = lesson_result["words"]
        sentences = lesson_result["sentences"]

        # Generate outputs
        results = {}

        if dna_report:
            results["dna_report"] = dna_report

        results["method"] = method
        results["words"] = words
        results["sentences"] = sentences
        results["user_id"] = user_id

        # Generate files synchronously so all results are available
        await generate_outputs(user_id, results)

        return JSONResponse(results)

    except Exception as e:
        logger.error(f"Error processing user data: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/analyze-dna")
async def analyze_dna(
    user_id: str = Form(...),
    ancestry: str = Form(...),
    mbti: str = Form(...),
    dna_file: Optional[UploadFile] = File(None)
):
    """Analyze DNA and generate personalized learning method"""
    try:
        logger.info(f"Analyzing DNA for user: {user_id}")

        # Create user directory
        user_dir = os.path.join("data", "users", user_id)
        ensure_dir(user_dir)

        # Save user profile
        profile = {
            "user_id": user_id,
            "ancestry": ancestry,
            "mbti": mbti,
            "dna_analyzed": True,
            "analyzed_at": str(datetime.utcnow())
        }

        with open(os.path.join(user_dir, "profile.json"), "w") as f:
            json.dump(profile, f, indent=2)

        # Process DNA file
        dna_report = None
        if dna_file and dna_file.filename:
            dna_path = os.path.join(user_dir, "genome.txt")
            with open(dna_path, "wb") as f:
                content = await dna_file.read()
                f.write(content)

            dna_report = engine.generate_report(dna_path, ancestry)
        else:
            return JSONResponse({"error": "DNA file is required"}, status_code=400)

        # Generate personalized learning method
        dna_percentile = 50  # default
        if dna_report and 'pgs_results' in dna_report and 'percentile' in dna_report['pgs_results']:
            dna_percentile = dna_report['pgs_results']['percentile']

        method = run_calibrator(dna_percentile, mbti)

        # Save method to user directory
        method_data = {
            "method": method,
            "dna_percentile": dna_percentile,
            "generated_at": str(datetime.utcnow())
        }
        
        with open(os.path.join(user_dir, "method.json"), "w") as f:
            json.dump(method_data, f, indent=2)

        return JSONResponse({
            "dna_report": dna_report,
            "method": method,
            "user_id": user_id
        })

    except Exception as e:
        logger.error(f"Error analyzing DNA for {user_id}: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/generate-lesson")
async def generate_lesson(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    target_language: str = Form(...),
    log_text: str = Form("")
):
    """Generate lesson content based on daily activities"""
    try:
        logger.info(f"Generating lesson for user: {user_id}")

        user_dir = os.path.join("data", "users", user_id)
        
        # Check if user exists and has completed DNA analysis
        profile_path = os.path.join(user_dir, "profile.json")
        if not os.path.exists(profile_path):
            return JSONResponse({"error": "User profile not found. Please complete DNA analysis first."}, status_code=400)

        # Update profile with target language
        with open(profile_path, "r") as f:
            profile = json.load(f)
        
        profile["target_language"] = target_language
        profile["last_lesson_at"] = str(datetime.utcnow())
        
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

        # Generate lesson content
        lesson_result = run_lesson_bot(log_text, target_language)
        words = lesson_result["words"]
        sentences = lesson_result["sentences"]

        # Prepare results
        results = {
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


async def generate_outputs(user_id: str, results: dict):
    """Generate PDF, Anki, audio, and plots in background"""
    try:
        user_dir = os.path.join("data", "users", user_id)

        # Generate PDF
        if "method" in results:
            # PDF generation needs: (dna_report, method, progress, lesson, user_id)
            # We need to create missing data structures
            dna_report = results.get("dna_report")
            method = results.get("method")
            # Create a basic progress structure since run_tracker returns a dict
            progress = {"progress": "Generated successfully"}
            # Create a basic lesson structure from words/sentences
            lesson = {
                "words": results.get("words", []),
                "sentences": results.get("sentences", [])
            }
            pdf_path = generate_pdf(
                dna_report, method, progress, lesson, user_id)
            results["pdf_path"] = convert_path_to_url(pdf_path)
            logger.info(f"Generated PDF: {pdf_path}")

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

        # Generate plots
        if "dna_report" in results:
            dna_plot_path, progress_plot_path = generate_dna_plots(
                user_id, results)
            results["dna_plot_path"] = convert_path_to_url(dna_plot_path)
            results["progress_plot_path"] = convert_path_to_url(
                progress_plot_path)

    except Exception as e:
        logger.error(f"Error generating outputs for {user_id}: {e}")


@router.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """Get user profile"""
    try:
        profile_path = os.path.join("data", "users", user_id, "profile.json")
        if os.path.exists(profile_path):
            with open(profile_path, "r") as f:
                profile = json.load(f)

            # Check if DNA file exists
            dna_path = os.path.join("data", "users", user_id, "genome.txt")
            dna_exists = os.path.exists(dna_path)

            return JSONResponse({
                "exists": True,
                "profile": profile,
                "dna_exists": dna_exists
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
        pdf_path = os.path.join("data", "users", user_id,
                                "GENELINGUA_COMPREHENSIVE_REPORT.pdf")
        if os.path.exists(pdf_path):
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=f"GeneLingua_Report_{user_id}.pdf"
            )
        else:
            return JSONResponse({"error": "PDF not found"}, status_code=404)
    except Exception as e:
        logger.error(f"Error downloading PDF for {user_id}: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/download/anki/{user_id}")
async def download_anki(user_id: str):
    """Download Anki CSV for user"""
    try:
        anki_path = os.path.join(
            "data", "users", user_id, "genelingua_anki.csv")
        if os.path.exists(anki_path):
            return FileResponse(
                anki_path,
                media_type="text/csv",
                filename=f"GeneLingua_Anki_{user_id}.csv"
            )
        else:
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
                filename=f"GeneLingua_Audio_{user_id}.mp3"
            )
        else:
            return JSONResponse({"error": "Audio file not found"}, status_code=404)
    except Exception as e:
        logger.error(f"Error downloading audio for {user_id}: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
