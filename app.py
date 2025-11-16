from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import json
from datetime import datetime
from dna_engine import DNAPolygenicEngine
from agents.calibrator import run_calibrator
from agents.tracker import run_tracker
from agents.lesson_bot import run_lesson_bot
from tools.pdf import generate_pdf
from tools.anki import export_anki
from tools.audio import generate_audio
from tools.dna_plot import generate_dna_plots
from tools.utils import ensure_dir, get_logger
import shutil
from typing import Optional
import httpx

# Import expert systems and assessment
try:
    import sys
    sys.path.append('other_experts')
    from healthcare_expert import generate_patient_response as healthcare_response
    from it_backend_interviewer import generate_interviewer_response as interview_response
    from assessment import RealTimeAssessment, save_assessment_data
except ImportError as e:
    logger = get_logger(__name__)
    logger.warning(f"Could not import expert systems: {e}")
    healthcare_response = None
    interview_response = None
    RealTimeAssessment = None
    save_assessment_data = None

# === Initialize FastAPI ===
app = FastAPI(title="GENELINGUA - DNA + AI Language Coach")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# === Initialize ===
logger = get_logger("app")
ensure_dir("data")
ensure_dir("data/users")

engine = DNAPolygenicEngine()

# Initialize assessment system
HF_TOKEN = os.getenv("HF_TOKEN", "hf_your_token_here")
DEFAULT_MODEL = "google/gemma-2-9b-it"
FALLBACK_MODEL = "deepseek-ai/DeepSeek-R1:together"
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

assessment_engine = None
if RealTimeAssessment:
    assessment_engine = RealTimeAssessment(HF_TOKEN, HF_API_URL, DEFAULT_MODEL, FALLBACK_MODEL)

# === User Profile Management ===


def save_user_profile(user_id, ancestry, mbti, target_language):
    """Save user preferences to avoid re-entering each time"""
    try:
        user_dir = f"data/users/{user_id}"
        os.makedirs(user_dir, exist_ok=True)

        profile = {
            "user_id": user_id,
            "ancestry": ancestry,
            "mbti": mbti,
            "target_language": target_language,
            "last_updated": str(datetime.now())
        }

        with open(f"{user_dir}/profile.json", "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

        logger.info(f"User profile saved for {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to save profile: {e}")
        return False


def load_user_profile(user_id):
    """Load user preferences if they exist"""
    try:
        profile_path = f"data/users/{user_id}/profile.json"
        if os.path.exists(profile_path):
            with open(profile_path, "r", encoding="utf-8") as f:
                profile = json.load(f)
            logger.info(f"User profile loaded for {user_id}")
            return profile
    except Exception as e:
        logger.error(f"Failed to load profile: {e}")

    return {
        "user_id": user_id,
        "ancestry": "EAS",
        "mbti": "INTJ",
        "target_language": "japanese"
    }


def check_dna_file_exists(user_id):
    """Check if DNA file already exists for user"""
    return os.path.exists(f"data/users/{user_id}/genome.txt")


def load_profile_on_name_change(user_id):
    """Load user profile when name is entered and update UI components"""
    if not user_id or not user_id.strip():
        return (
            "EAS",
            "INTJ",
            "japanese",
            "Enter your name to load saved settings"
        )

    profile = load_user_profile(user_id.strip())
    dna_exists = check_dna_file_exists(user_id.strip())

    status_msg = f"✅ Profile loaded for {user_id.strip()}"
    if dna_exists:
        status_msg += " | DNA file found - no need to re-upload"
    else:
        status_msg += " | Please upload your DNA file"

    return (
        profile["ancestry"],
        profile["mbti"],
        profile["target_language"],
        status_msg
    )


def process_user(user_id, dna_file, ancestry, mbti, target_language, log_text, photo, voice_file):
    user_id = user_id.strip() or "unknown"
    logger.info(
        f"Starting processing for user: {user_id} | Ancestry: {ancestry} | MBTI: {mbti} | Language: {target_language}")

    user_dir = ensure_dir(f"data/users/{user_id}")
    save_user_profile(user_id, ancestry, mbti, target_language)

    try:
        # === 1. DNA Processing ===
        dna_report = {"pgs_results": {"percentile": 50, "z_score": 0.0}}
        plot_path = None

        existing_dna_path = f"{user_dir}/genome.txt"
        dna_exists = os.path.exists(existing_dna_path)

        if dna_file:
            try:
                path = f"{user_dir}/genome.txt"
                if hasattr(dna_file, 'save'):
                    dna_file.save(path)
                elif hasattr(dna_file, 'name'):
                    import shutil
                    shutil.copy2(dna_file.name, path)
                else:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(str(dna_file))

                logger.info(f"New DNA file saved: {path}")
                dna_report = engine.generate_report(path, ancestry)
                logger.info(
                    f"DNA report generated | Percentile: {dna_report['pgs_results']['percentile']}")

                plot_path = generate_dna_plots(dna_report, user_dir)
                if plot_path:
                    logger.debug(f"DNA plot generated: {plot_path}")
                else:
                    logger.warning("DNA plot generation failed")
                    plot_path = None
            except Exception as e:
                logger.error(f"DNA processing failed: {e}", exc_info=True)
                dna_report = {"pgs_results": {
                    "percentile": 50, "z_score": 0.0}}
                plot_path = None
        elif dna_exists:
            try:
                logger.info(f"Using existing DNA file for {user_id}")
                dna_report = engine.generate_report(
                    existing_dna_path, ancestry)
                logger.info(
                    f"DNA report generated from existing file | Percentile: {dna_report['pgs_results']['percentile']}")

                plot_path = generate_dna_plots(dna_report, user_dir)
                if plot_path:
                    logger.debug(f"DNA plot generated: {plot_path}")
                else:
                    logger.warning("DNA plot generation failed")
                    plot_path = None
            except Exception as e:
                logger.error(f"DNA processing failed: {e}", exc_info=True)
                dna_report = {"pgs_results": {
                    "percentile": 50, "z_score": 0.0}}
                plot_path = None
        else:
            logger.info(
                "No DNA file uploaded and none found — using default score")

        # === 2. Save MBTI + Log ===
        try:
            with open(f"{user_dir}/mbti.json", "w", encoding="utf-8") as f:
                json.dump({"type": mbti}, f, indent=2)
            with open(f"{user_dir}/logs.txt", "w", encoding="utf-8") as f:
                f.write(log_text or "")
            logger.debug("MBTI and log saved")
        except Exception as e:
            logger.error(f"Failed to save MBTI/log: {e}")

        # === 3. AI Agents ===
        try:
            logger.info("Running calibrator agent...")
            method = run_calibrator(
                dna_report['pgs_results']['percentile'], mbti)
            logger.info("Calibrator completed")

            logger.info("Running tracker agent...")
            progress = run_tracker(user_dir)
            logger.info("Tracker completed")

            logger.info(
                f"Running lesson bot agent for {target_language} (this may take a while)...")
            try:
                lesson = run_lesson_bot(
                    log_text or "No log provided", target_language)
                logger.info(
                    f"Lesson bot completed - generated {len(lesson.get('words', []))} words and {len(lesson.get('sentences', []))} sentences in {target_language}")
            except Exception as lesson_error:
                logger.error(
                    f"Lesson bot specifically failed: {lesson_error}", exc_info=True)
                fallback_lessons = {
                    "japanese": {
                        "words": ["今日 (きょう) – today", "勉強 (べんきょう) – study", "日本語 (にほんご) – Japanese"],
                        "sentences": ["今日は日本語を勉強しました。"]
                    },
                    "dutch": {
                        "words": ["vandaag – today", "studeren – study", "Nederlands – Dutch"],
                        "sentences": ["Vandaag heb ik Nederlands gestudeerd."]
                    },
                    "chinese": {
                        "words": ["今天 (jīntiān) – today", "学习 (xuéxí) – study", "中文 (zhōngwén) – Chinese"],
                        "sentences": ["今天我学习了中文。"]
                    }
                }
                lesson = fallback_lessons.get(
                    target_language, fallback_lessons["japanese"])
                lesson["language"] = target_language
            logger.info("AI agents completed")
        except Exception as e:
            logger.error(f"AI agent failed: {e}", exc_info=True)
            method = {"focus": "Balanced", "blocks": [
                "60min study", "30min review"]}
            progress = {"graph": None, "b2_months": 18,
                        "vocab": 150, "cefr": "A1"}
            fallback_lessons = {
                "japanese": {
                    "words": ["今日 (きょう) – today", "勉強 (べんきょう) – study", "日本語 (にほんご) – Japanese", "ありがとう (ありがとう) – thank you", "こんにちは (こんにちは) – hello"],
                    "sentences": ["今日は日本語を勉強しました。", "ありがとうございます。", "こんにちは、元気ですか？"]
                },
                "dutch": {
                    "words": ["vandaag – today", "studeren – study", "Nederlands – Dutch", "dank je – thank you", "hallo – hello"],
                    "sentences": ["Vandaag heb ik Nederlands gestudeerd.", "Dank je wel.", "Hallo, hoe gaat het?"]
                },
                "chinese": {
                    "words": ["今天 (jīntiān) – today", "学习 (xuéxí) – study", "中文 (zhōngwén) – Chinese", "谢谢 (xièxiè) – thank you", "你好 (nǐ hǎo) – hello"],
                    "sentences": ["今天我学习了中文。", "谢谢。", "你好，你好吗？"]
                }
            }
            lesson_data = fallback_lessons.get(
                target_language, fallback_lessons["japanese"])
            lesson = {
                "words": lesson_data["words"],
                "sentences": lesson_data["sentences"],
                "language": target_language
            }

        # === 4. Generate Outputs ===
        pdf_path = generate_pdf(dna_report, method, progress, lesson, user_id)
        anki_path = export_anki(lesson, user_id)
        audio_path = generate_audio(
            lesson["sentences"], user_id, target_language)

        logger.info(
            f"Outputs generated | PDF: {os.path.exists(pdf_path)} | Anki: {os.path.exists(anki_path)}")

        # === 5. Return ===
        return (
            f"DNA: {dna_report['pgs_results']['percentile']}th %ile | Z: {dna_report['pgs_results']['z_score']:+.2f}",
            f"**Method:** {method['focus']}\n" +
            "\n".join([f"- {b}" for b in method['blocks']]),
            progress.get("graph"),
            "\n".join(lesson.get("words", [])),
            "\n".join(lesson.get("sentences", [])),
            plot_path if plot_path and os.path.exists(plot_path) else None,
            pdf_path if pdf_path and os.path.exists(pdf_path) else None,
            anki_path if anki_path and os.path.exists(anki_path) else None,
            audio_path if audio_path and os.path.exists(audio_path) else None,
        )

    except Exception as e:
        logger.critical(
            f"Unexpected error for user {user_id}: {e}", exc_info=True)
        return (
            "Critical Error: Check logs.",
            "", None, "Error", "Error", None, None, None, None
        )


# === FastAPI Routes ===

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon or return 204 if not found"""
    favicon_path = "static/favicon.ico"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    # Return empty response to avoid 404 logs
    return Response(status_code=204)


@app.get("/api/load_profile")
async def load_profile(user_id: str):
    """Load user profile and check if DNA file exists"""
    try:
        profile = load_user_profile(user_id)
        dna_exists = check_dna_file_exists(user_id)
        return JSONResponse({
            "profile": profile,
            "dna_exists": dna_exists
        })
    except Exception as e:
        logger.error(f"Error loading profile: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/process")
async def process(
    user_id: str = Form(...),
    ancestry: str = Form(...),
    mbti: str = Form(...),
    target_language: str = Form(...),
    log_text: str = Form(""),
    dna_file: Optional[UploadFile] = File(None)
):
    """Process user data and generate learning plan"""
    try:
        user_id = user_id.strip() or "unknown"
        logger.info(
            f"Starting processing for user: {user_id} | Ancestry: {ancestry} | MBTI: {mbti} | Language: {target_language}")

        user_dir = ensure_dir(f"data/users/{user_id}")
        save_user_profile(user_id, ancestry, mbti, target_language)

        # === 1. DNA Processing ===
        dna_report = {"pgs_results": {"percentile": 50, "z_score": 0.0}}
        plot_path = None

        existing_dna_path = f"{user_dir}/genome.txt"
        dna_exists = os.path.exists(existing_dna_path)

        if dna_file:
            try:
                path = f"{user_dir}/genome.txt"
                with open(path, 'wb') as f:
                    shutil.copyfileobj(dna_file.file, f)

                logger.info(f"New DNA file saved: {path}")
                dna_report = engine.generate_report(path, ancestry)
                logger.info(
                    f"DNA report generated | Percentile: {dna_report['pgs_results']['percentile']}")

                plot_path = generate_dna_plots(dna_report, user_dir)
                if plot_path:
                    logger.debug(f"DNA plot generated: {plot_path}")
                else:
                    logger.warning("DNA plot generation failed")
                    plot_path = None
            except Exception as e:
                logger.error(f"DNA processing failed: {e}", exc_info=True)
                dna_report = {"pgs_results": {
                    "percentile": 50, "z_score": 0.0}}
                plot_path = None
        elif dna_exists:
            try:
                logger.info(f"Using existing DNA file for {user_id}")
                dna_report = engine.generate_report(
                    existing_dna_path, ancestry)
                logger.info(
                    f"DNA report generated from existing file | Percentile: {dna_report['pgs_results']['percentile']}")

                plot_path = generate_dna_plots(dna_report, user_dir)
                if plot_path:
                    logger.debug(f"DNA plot generated: {plot_path}")
                else:
                    logger.warning("DNA plot generation failed")
                    plot_path = None
            except Exception as e:
                logger.error(f"DNA processing failed: {e}", exc_info=True)
                dna_report = {"pgs_results": {
                    "percentile": 50, "z_score": 0.0}}
                plot_path = None
        else:
            logger.info(
                "No DNA file uploaded and none found — using default score")

        # === 2. Save MBTI + Log ===
        try:
            with open(f"{user_dir}/mbti.json", "w", encoding="utf-8") as f:
                json.dump({"type": mbti}, f, indent=2)
            with open(f"{user_dir}/logs.txt", "w", encoding="utf-8") as f:
                f.write(log_text or "")
            logger.debug("MBTI and log saved")
        except Exception as e:
            logger.error(f"Failed to save MBTI/log: {e}")

        # === 3. AI Agents ===
        try:
            logger.info("Running calibrator agent...")
            method = run_calibrator(
                dna_report['pgs_results']['percentile'], mbti)
            logger.info("Calibrator completed")

            logger.info("Running tracker agent...")
            progress = run_tracker(user_dir)
            logger.info("Tracker completed")

            logger.info(
                f"Running lesson bot agent for {target_language} (this may take a while)...")
            try:
                lesson = run_lesson_bot(
                    log_text or "No log provided", target_language)
                logger.info(
                    f"Lesson bot completed - generated {len(lesson.get('words', []))} words and {len(lesson.get('sentences', []))} sentences in {target_language}")
            except Exception as lesson_error:
                logger.error(
                    f"Lesson bot specifically failed: {lesson_error}", exc_info=True)
                fallback_lessons = {
                    "japanese": {
                        "words": ["今日 (きょう) – today", "勉強 (べんきょう) – study", "日本語 (にほんご) – Japanese"],
                        "sentences": ["今日は日本語を勉強しました。"]
                    },
                    "dutch": {
                        "words": ["vandaag – today", "studeren – study", "Nederlands – Dutch"],
                        "sentences": ["Vandaag heb ik Nederlands gestudeerd."]
                    },
                    "chinese": {
                        "words": ["今天 (jīntiān) – today", "学习 (xuéxí) – study", "中文 (zhōngwén) – Chinese"],
                        "sentences": ["今天我学习了中文。"]
                    }
                }
                lesson = fallback_lessons.get(
                    target_language, fallback_lessons["japanese"])
                lesson["language"] = target_language
            logger.info("AI agents completed")
        except Exception as e:
            logger.error(f"AI agent failed: {e}", exc_info=True)
            method = {"focus": "Balanced", "blocks": [
                "60min study", "30min review"]}
            progress = {"graph": None, "b2_months": 18,
                        "vocab": 150, "cefr": "A1"}
            fallback_lessons = {
                "japanese": {
                    "words": ["今日 (きょう) – today", "勉強 (べんきょう) – study", "日本語 (にほんご) – Japanese", "ありがとう (ありがとう) – thank you", "こんにちは (こんにちは) – hello"],
                    "sentences": ["今日は日本語を勉強しました。", "ありがとうございます。", "こんにちは、元気ですか？"]
                },
                "dutch": {
                    "words": ["vandaag – today", "studeren – study", "Nederlands – Dutch", "dank je – thank you", "hallo – hello"],
                    "sentences": ["Vandaag heb ik Nederlands gestudeerd.", "Dank je wel.", "Hallo, hoe gaat het?"]
                },
                "chinese": {
                    "words": ["今天 (jīntiān) – today", "学习 (xuéxí) – study", "中文 (zhōngwén) – Chinese", "谢谢 (xièxiè) – thank you", "你好 (nǐ hǎo) – hello"],
                    "sentences": ["今天我学习了中文。", "谢谢。", "你好，你好吗？"]
                }
            }
            lesson_data = fallback_lessons.get(
                target_language, fallback_lessons["japanese"])
            lesson = {
                "words": lesson_data["words"],
                "sentences": lesson_data["sentences"],
                "language": target_language
            }

        # === 4. Generate Outputs ===
        pdf_path = generate_pdf(dna_report, method, progress, lesson, user_id)
        anki_path = export_anki(lesson, user_id)
        audio_path = generate_audio(
            lesson["sentences"], user_id, target_language)

        logger.info(
            f"Outputs generated | PDF: {os.path.exists(pdf_path)} | Anki: {os.path.exists(anki_path)}")

        # === 5. Return JSON Response ===
        return JSONResponse({
            "dna_report": f"DNA: {dna_report['pgs_results']['percentile']}th %ile | Z: {dna_report['pgs_results']['z_score']:+.2f}",
            "method": f"**Method:** {method['focus']}\n" + "\n".join([f"- {b}" for b in method['blocks']]),
            "words": lesson.get("words", []),
            "sentences": lesson.get("sentences", []),
            "dna_plot_path": f"/files/{user_id}/dna_report.png" if plot_path and os.path.exists(plot_path) else None,
            "progress_plot_path": f"/files/{user_id}/progress.png" if progress.get("graph") and os.path.exists(f"{user_dir}/progress.png") else None,
            "pdf_path": f"/files/{user_id}/GENELINGUA_COMPREHENSIVE_REPORT.pdf" if pdf_path and os.path.exists(pdf_path) else None,
            "anki_path": f"/files/{user_id}/genelingua_anki.csv" if anki_path and os.path.exists(anki_path) else None,
            "audio_path": f"/files/{user_id}/lesson_audio.mp3" if audio_path and os.path.exists(audio_path) else None,
        })

    except Exception as e:
        logger.critical(
            f"Unexpected error for user {user_id}: {e}", exc_info=True)
        return JSONResponse({
            "error": "Critical Error: Check logs.",
            "dna_report": "Error",
            "method": "",
            "words": [],
            "sentences": []
        }, status_code=500)


@app.get("/files/{user_id}/{filename}")
async def get_file(user_id: str, filename: str):
    """Serve user files (plots, PDFs, audio, etc.)"""
    file_path = f"data/users/{user_id}/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse({"error": "File not found"}, status_code=404)


def clean_response_for_audio(text):
    """Remove emojis, markdown, and other formatting for natural audio synthesis"""
    import re

    # Remove emojis
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)

    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'`(.*?)`', r'\1', text)        # Code
    text = re.sub(r'#{1,6}\s', '', text)          # Headers
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Links

    # Clean up multiple spaces and newlines
    text = re.sub(r'\n+', '. ', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


async def generate_language_coach_response(message, conversation_history):
    """Fallback language coach for general Dutch learning"""
    system_prompt = """Je bent een Nederlandse taalcoach. Help studenten met:
- Nederlandse grammatica en uitspraak
- Woordenschat uitbreiding
- Conversatie oefening
- Nederlandse cultuur

Spreek altijd Nederlands, tenzij uitleg in het Engels nodig is.
Wees geduldig, ondersteunend en corrigeer fouten vriendelijk."""

    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history
    messages.extend(conversation_history[-10:])  # Last 10 messages
    messages.append({"role": "user", "content": message})

    # Try models with fallback
    models_to_try = [DEFAULT_MODEL, FALLBACK_MODEL]
    
    for model in models_to_try:
        try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 800,
                "temperature": 0.7
            }

            headers = {"Authorization": f"Bearer {HF_TOKEN}"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(HF_API_URL, json=payload, headers=headers)
                response.raise_for_status()

                result = response.json()
                return result["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.warning(f"Language coach with {model} failed: {e}")
            if model == models_to_try[-1]:  # Last model failed
                raise


def generate_fallback_response(expert, message):
    """Generate a simple fallback response when expert systems fail"""
    responses = {
        "healthcare": "Ik kan je helpen met medische Nederlandse taal. Stel je vraag opnieuw.",
        "interview": "Ik kan je helpen voorbereiden op Nederlandse IT interviews. Wat wil je oefenen?",
        "general": "Ik ben hier om je te helpen met Nederlands leren. Hoe kan ik je helpen?"
    }
    return responses.get(expert, responses["general"])


def log_chat_interaction(user_id, expert, user_message, ai_response):
    """Log chat interactions for learning analytics"""
    try:
        user_dir = f"data/users/{user_id}"
        os.makedirs(user_dir, exist_ok=True)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "expert": expert,
            "user_message": user_message,
            "ai_response": ai_response,
            "session_type": "chat"
        }

        logs_file = f"{user_dir}/logs.txt"
        with open(logs_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    except Exception as e:
        logger.error(f"Failed to log chat interaction: {e}")


@app.post("/api/assessment")
async def get_real_time_assessment(request: Request):
    """Get real-time assessment for ongoing conversation"""
    try:
        data = await request.json()
        user_id = data.get("user_id", "unknown")
        expert = data.get("expert", "language")
        conversation_history = data.get("conversation_history", [])
        current_message = data.get("current_message", "")

        if not assessment_engine:
            return JSONResponse({
                "error": "Assessment engine not available",
                "fallback_assessment": {
                    "overall_score": {"performance_level": "developing"},
                    "hints": {"quick_suggestions": ["Blijf oefenen!", "Probeer meer Nederlandse woorden"]}
                }
            }, status_code=200)

        # Generate real-time assessment
        assessment = await assessment_engine.analyze_conversation(
            user_id, expert, conversation_history, current_message
        )

        # Save assessment data asynchronously
        if save_assessment_data:
            try:
                await save_assessment_data(user_id, assessment)
            except Exception as e:
                logger.error(f"Failed to save assessment: {e}")

        return JSONResponse(assessment)

    except Exception as e:
        logger.error(f"Assessment error: {e}")
        return JSONResponse({
            "error": "Assessment failed",
            "fallback_assessment": {
                "overall_score": {"performance_level": "developing"},
                "hints": {"quick_suggestions": ["Technische problemen", "Probeer het opnieuw"]}
            }
        }, status_code=500)


@app.post("/api/generate_speech")
async def generate_speech(request: Request):
    """Generate high-quality speech using edge-tts"""
    try:
        data = await request.json()
        text = data.get("text", "")
        language = data.get("language", "dutch")
        user_id = data.get("user_id", "anonymous")

        if not text.strip():
            return JSONResponse({"error": "Text cannot be empty"}, status_code=400)

        # Import AudioEngine
        from tools.audio import AudioEngine

        # Create audio engine instance
        audio_engine = AudioEngine()

        # Generate unique filename for this speech
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        audio_filename = f"chat_speech_{text_hash}.mp3"

        # Create user directory
        user_dir = f"data/users/{user_id}"
        os.makedirs(user_dir, exist_ok=True)

        # Generate audio path
        audio_path = f"{user_dir}/{audio_filename}"

        # Generate speech using edge-tts
        result_path = await audio_engine.text_to_speech_async(
            text=text,
            output_path=audio_path,
            language=language
        )

        if result_path and os.path.exists(result_path):
            # Return the URL to access the audio file
            audio_url = f"/files/{user_id}/{audio_filename}"
            return JSONResponse({
                "success": True,
                "audio_url": audio_url,
                "language": language
            })
        else:
            return JSONResponse({
                "error": "Failed to generate audio"
            }, status_code=500)

    except Exception as e:
        logger.error(f"Speech generation error: {e}")
        return JSONResponse({
            "error": "Failed to generate speech"
        }, status_code=500)


@app.post("/api/chat")
async def chat_with_expert(request: Request):
    """Handle chat messages with different experts using specialized expert systems"""
    try:
        data = await request.json()
        message = data.get("message", "")
        expert = data.get("expert", "healthcare")
        user_id = data.get("user_id", "anonymous")

        if not message.strip():
            return JSONResponse({"error": "Message cannot be empty"}, status_code=400)

        # Simple language detection
        def detect_message_language(text):
            dutch_words = ['de', 'het', 'en', 'van', 'is', 'dat', 'een', 'te', 'zijn', 'op', 'met', 'voor', 'als', 'aan', 'door', 'over', 'om', 'niet', 'maar', 'zo', 'ook', 'wel', 'nog', 'bij', 'tot', 'onder', 'naar', 'waar', 'wat', 'wie', 'hoe', 'waarom', 'wanneer', 'omdat', 'hoewel', 'toen', 'terwijl', 'indien', 'tenzij', 'hallo', 'dag', 'goedemorgen',
                           'goedemiddag', 'goedenavond', 'goedenacht', 'dankjewel', 'bedankt', 'alsjeblieft', 'sorry', 'excuses', 'pardon', 'ja', 'nee', 'misschien', 'wellicht', 'natuurlijk', 'zeker', 'absoluut', 'precies', 'inderdaad', 'werkelijk', 'echt', 'heel', 'erg', 'zeer', 'nogal', 'vrij', 'tamelijk', 'redelijk', 'behoorlijk', 'enigszins', 'ietwat', 'lichtelijk']
            english_words = ['the', 'and', 'is', 'that', 'to', 'of', 'in', 'it', 'you', 'for', 'with', 'on', 'as', 'be', 'at', 'by', 'this', 'have', 'from', 'or', 'one', 'had', 'but', 'word', 'not', 'what', 'all', 'were', 'they', 'we', 'when', 'your', 'can', 'said', 'there', 'each', 'which', 'she', 'do', 'how', 'their', 'if', 'will', 'up', 'other', 'about', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like', 'into', 'him', 'has', 'two', 'more', 'go', 'no', 'way', 'could', 'my', 'than', 'first', 'water', 'been', 'call', 'who', 'its', 'now', 'find', 'long', 'down', 'day', 'did', 'get', 'come', 'made', 'may', 'part', 'over', 'new', 'sound', 'take', 'only', 'little', 'work', 'know', 'place', 'year', 'live', 'me', 'back', 'give', 'most', 'very', 'after', 'thing', 'our', 'just', 'name', 'good', 'sentence', 'man', 'think', 'say', 'great', 'where', 'help', 'through', 'much', 'before', 'line', 'right', 'too', 'mean', 'old',
                             'any', 'same', 'tell', 'boy', 'follow', 'came', 'want', 'show', 'also', 'around', 'form', 'three', 'small', 'set', 'put', 'end', 'why', 'again', 'turn', 'here', 'move', 'well', 'asked', 'went', 'men', 'read', 'need', 'land', 'different', 'home', 'us', 'picture', 'try', 'kind', 'hand', 'head', 'high', 'every', 'near', 'add', 'food', 'between', 'own', 'below', 'country', 'plant', 'last', 'school', 'father', 'keep', 'tree', 'never', 'start', 'city', 'earth', 'eye', 'light', 'thought', 'open', 'example', 'begin', 'life', 'always', 'those', 'both', 'paper', 'together', 'got', 'group', 'often', 'run', 'important', 'until', 'hello', 'hi', 'good', 'morning', 'afternoon', 'evening', 'night', 'thank', 'thanks', 'please', 'sorry', 'excuse', 'yes', 'no', 'maybe', 'perhaps', 'of', 'course', 'sure', 'absolutely', 'exactly', 'indeed', 'really', 'truly', 'very', 'quite', 'rather', 'fairly', 'reasonably', 'considerably', 'somewhat', 'slightly', 'a', 'bit']

            text_lower = message.lower()
            dutch_count = sum(1 for word in dutch_words if word in text_lower)
            english_count = sum(
                1 for word in english_words if word in text_lower)

            return 'dutch' if dutch_count > english_count else 'english'

        detected_language = detect_message_language(message)

        # Define Dutch-focused expert prompts for language learning
        # All experts are primarily Dutch language learning assistants
        expert_prompts = {
            "healthcare": """Je bent een Nederlandse zorgverlener en welzijnsadviseur die helpt met Nederlandse taalverwerving. 
            Je primaire doel is om gebruikers te helpen hun Nederlands te verbeteren door gesprekken over gezondheid en welzijn.
            Spreek ALTIJD in het Nederlands, tenzij de gebruiker expliciet om Engels vraagt voor verduidelijking.
            Geef behulpzame, accurate gezondheidsinformatie in correct Nederlands en help de gebruiker medische Nederlandse vocabulaire te leren.
            Verbeter hun Nederlands door natuurlijke gesprekken over gezondheidsonderwerpen.
            Wees geduldig, correctief waar nodig, en gebruik gevarieerde Nederlandse uitdrukkingen.
            Als de gebruiker fouten maakt in het Nederlands, corrigeer ze vriendelijk en leg uit waarom.
            BELANGRIJK: Gebruik GEEN emojis, sterretjes, markdown opmaak of speciale tekens in je antwoorden. Alleen pure tekst zonder opmaak.""",

            "interview": """Je bent een Nederlandse IT-sollicitatiecoach die helpt met Nederlandse taalverwerving.
            Je primaire doel is om gebruikers te helpen hun Nederlands te verbeteren door gesprekken over IT en sollicitatiegesprekken.
            Spreek ALTIJD in het Nederlands, tenzij de gebruiker expliciet om Engels vraagt voor verduidelijking.
            Help gebruikers zich voor te bereiden op Nederlandse IT-sollicitatiegesprekken en leer ze technische Nederlandse vocabulaire.
            Verbeter hun Nederlands door natuurlijke gesprekken over technologie, programmeren en carrière.
            Wees geduldig, correctief waar nodig, en gebruik gevarieerde Nederlandse uitdrukkingen.
            Als de gebruiker fouten maakt in het Nederlands, corrigeer ze vriendelijk en leg uit waarom.
            BELANGRIJK: Gebruik GEEN emojis, sterretjes, markdown opmaak of speciale tekens in je antwoorden. Alleen pure tekst zonder opmaak.""",

            "language": """Je bent een Nederlandse taalcoach en polyglot die gespecialiseerd is in het onderwijzen van Nederlands.
            Je primaire doel is om gebruikers te helpen hun Nederlands te verbeteren door natuurlijke gesprekken.
            Spreek ALTIJD in het Nederlands, tenzij de gebruiker expliciet om Engels vraagt voor verduidelijking.
            Help gebruikers met grammatica, uitspraak, Nederlandse cultuur, en idiomatische uitdrukkingen.
            Verbeter hun Nederlands door boeiende gesprekken over verschillende onderwerpen.
            Wees geduldig, correctief waar nodig, en gebruik gevarieerde Nederlandse uitdrukkingen en vocabulaire.
            Als de gebruiker fouten maakt in het Nederlands, corrigeer ze vriendelijk en leg uit waarom.
            Geef concrete voorbeelden en oefen verschillende Nederlandse grammaticale structuren.
            BELANGRIJK: Gebruik GEEN emojis, sterretjes, markdown opmaak of speciale tekens in je antwoorden. Alleen pure tekst zonder opmaak."""
        }

        system_prompt = expert_prompts.get(
            expert, expert_prompts["healthcare"])

        # Use HuggingFace API for response generation
        token = os.getenv("HF_TOKEN")
        if not token:
            logger.warning("No HF_TOKEN found - using fallback response")
            fallback_response = generate_fallback_response(expert, message)
            return JSONResponse({"response": fallback_response})

        API_URL = "https://router.huggingface.co/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Use chat completions format
        payload = {
            "model": "google/gemma-2-9b-it",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "max_tokens": 150,
            "temperature": 0.7,
            "stream": False
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(API_URL, headers=headers, json=payload, timeout=30.0)

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    assistant_response = result["choices"][0]["message"]["content"].strip(
                    )

                    # Log the conversation
                    log_chat_interaction(
                        user_id, expert, message, assistant_response)

                    return JSONResponse({"response": assistant_response})
                else:
                    # Fallback response
                    fallback_response = generate_fallback_response(
                        expert, message)
                    return JSONResponse({"response": fallback_response})
            else:
                logger.error(f"HuggingFace API error: {response.status_code}")
                fallback_response = generate_fallback_response(expert, message)
                return JSONResponse({"response": fallback_response})

        # Get or create conversation history for this user and expert
        conversation_key = f"{user_id}_{expert}"

        # Load conversation history
        try:
            user_dir = f"data/users/{user_id}"
            os.makedirs(user_dir, exist_ok=True)

            history_file = f"{user_dir}/chat_history_{expert}.json"
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    conversation_history = json.load(f)
            else:
                conversation_history = []
        except Exception as e:
            logger.error(f"Failed to load conversation history: {e}")
            conversation_history = []

        # Generate response using specialized expert systems
        try:
            if expert == "healthcare" and healthcare_response:
                # Use specialized healthcare expert
                response = healthcare_response(
                    scenario="general_consultation",  # Default scenario
                    conversation_history=conversation_history,
                    user_input=message
                )
            elif expert == "interview" and interview_response:
                # Use specialized IT interview expert
                response = interview_response(
                    scenario="technical_screening",  # Default scenario
                    conversation_history=conversation_history,
                    user_input=message
                )
            else:
                # Fallback to general language coach
                response = await generate_language_coach_response(message, conversation_history)

            # Clean response of emojis and markdown
            response = clean_response_for_audio(response)

            # Update conversation history
            conversation_history.append({"role": "user", "content": message})
            conversation_history.append(
                {"role": "assistant", "content": response})

            # Keep only last 20 messages
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]

            # Save conversation history
            try:
                with open(history_file, "w", encoding="utf-8") as f:
                    json.dump(conversation_history, f,
                              indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Failed to save conversation history: {e}")

            # Log the conversation
            log_chat_interaction(user_id, expert, message, response)

            # Trigger assessment update (non-blocking)
            assessment_data = None
            if assessment_engine:
                try:
                    assessment_data = await assessment_engine.analyze_conversation(
                        user_id, expert, conversation_history, message
                    )
                    if save_assessment_data:
                        await save_assessment_data(user_id, assessment_data)
                except Exception as e:
                    logger.error(f"Assessment update failed: {e}")

            response_data = {"response": response}
            if assessment_data:
                response_data["assessment_trigger"] = True

            return JSONResponse(response_data)
            
        except Exception as e:
            logger.error(f"Expert system error: {e}")
            # Fallback to simple response
            fallback_response = generate_fallback_response(expert, message)
            return JSONResponse({"response": fallback_response})

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return JSONResponse({
            "response": "Ik heb momenteel technische problemen. Probeer het over een paar seconden opnieuw."
        }, status_code=500)


def generate_fallback_response(expert: str, message: str) -> str:
    """Generate fallback responses when API fails"""

    # Simple language detection for fallback
    def detect_language(text):
        dutch_indicators = ['de', 'het', 'en', 'van', 'is', 'dat', 'een', 'te', 'zijn', 'op', 'met', 'voor', 'hallo', 'dag', 'goedemorgen', 'dankjewel', 'bedankt', 'sorry', 'ja', 'nee', 'wat', 'wie', 'waar', 'wanneer', 'waarom', 'hoe',
                            'omdat', 'maar', 'ook', 'nog', 'wel', 'niet', 'zo', 'heel', 'erg', 'zeer', 'kan', 'moet', 'wil', 'zou', 'zal', 'heeft', 'had', 'wordt', 'werd', 'zijn', 'was', 'waren', 'ben', 'bent', 'is', 'doe', 'doet', 'doen', 'deed', 'gedaan']
        text_lower = text.lower()
        dutch_count = sum(1 for word in dutch_indicators if word in text_lower)
        return 'dutch' if dutch_count > 2 else 'english'

    detected_lang = detect_language(message)

    if detected_lang == 'dutch':
        fallback_responses = {
            "healthcare": [
                "Bedankt voor je gezondheidsvraag. Hoewel ik graag specifiek advies zou geven, raad ik aan om een zorgverlener te raadplegen voor persoonlijk advies.",
                "Dat is een interessant gezondheidsonderwerp. Voor de meest accurate informatie kun je het beste met je dokter of een gekwalificeerde zorgverlener praten.",
                "Gezondheid is zo belangrijk! Voor specifieke medische zorgen is het altijd het beste om een zorgverlener te raadplegen die persoonlijk advies kan geven."
            ],
            "interview": [
                "Dat is een geweldige vraag voor sollicitatievoorbereiding! Laat me nadenken over de beste aanpak voor dit onderwerp.",
                "Uitstekende vraag voor interview-voorbereiding! Dit komt zeker vaak voor in technische gesprekken.",
                "Goed nagedacht over sollicitatievoorbreiding! Dit type vraag vereist een gestructureerde aanpak om effectief te beantwoorden."
            ],
            "language": [
                "Dat is een prachtige taalleervraag! Oefening en consistentie zijn de sleutel tot verbetering in elke taal.",
                "Geweldige vraag over taalleren! Onderdompeling en regelmatige oefening helpen je snel vooruit te gaan.",
                "Uitstekende taalleer-vraag! De beste manier om te verbeteren is door consistente oefening en blootstelling."
            ]
        }
    else:
        fallback_responses = {
            "healthcare": [
                "Thank you for your health question. While I'd love to provide specific advice, I recommend consulting with a healthcare professional for personalized guidance.",
                "That's an interesting health topic. For the most accurate information, please speak with your doctor or a qualified healthcare provider.",
                "Health is so important! For specific medical concerns, it's always best to consult with a healthcare professional who can provide personalized advice."
            ],
            "interview": [
                "That's a great interview preparation question! Let me think about the best approach to tackle this topic systematically.",
                "Excellent question for interview prep! This is definitely something that comes up frequently in technical interviews.",
                "Good thinking on interview preparation! This type question requires a structured approach to answer effectively."
            ],
            "language": [
                "That's a wonderful language learning question! Practice and consistency are key to improving in any language.",
                "Great question about language learning! Immersion and regular practice will help you progress quickly.",
                "Excellent language learning inquiry! The best way to improve is through consistent practice and exposure."
            ]
        }

    import random
    responses = fallback_responses.get(
        expert, fallback_responses["healthcare"])
    return random.choice(responses)


def log_chat_interaction(user_id: str, expert: str, user_message: str, assistant_response: str):
    """Log chat interactions for user history"""
    try:
        user_dir = f"data/users/{user_id}"
        os.makedirs(user_dir, exist_ok=True)

        chat_log = {
            "timestamp": datetime.now().isoformat(),
            "expert": expert,
            "user_message": user_message,
            "assistant_response": assistant_response
        }

        # Append to chat history file
        chat_file = f"{user_dir}/chat_history.json"
        if os.path.exists(chat_file):
            with open(chat_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []

        history.append(chat_log)

        # Keep only last 100 interactions
        if len(history) > 100:
            history = history[-100:]

        with open(chat_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Failed to log chat interaction: {e}")


# === Launch ===
if __name__ == "__main__":
    import uvicorn
    logger.info("Launching GENELINGUA FastAPI app...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7860,
        log_level="info"
    )
