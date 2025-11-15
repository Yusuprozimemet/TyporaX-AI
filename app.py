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
