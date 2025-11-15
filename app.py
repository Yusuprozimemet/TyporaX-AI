# app.py
import gradio as gr
import os
import json
from dna_engine import DNAPolygenicEngine
from agents.calibrator import run_calibrator
from agents.tracker import run_tracker
from agents.lesson_bot import run_lesson_bot
from tools.pdf import generate_pdf
from tools.anki import export_anki
from tools.audio import generate_audio
from tools.dna_plot import generate_dna_plots
from tools.utils import ensure_dir, get_logger

# === Initialize ===
logger = get_logger("app")
ensure_dir("data")
ensure_dir("data/users")

engine = DNAPolygenicEngine()


def process_user(user_id, dna_file, ancestry, mbti, log_text, photo, voice_file):
    user_id = user_id.strip() or "unknown"
    logger.info(
        f"Starting processing for user: {user_id} | Ancestry: {ancestry} | MBTI: {mbti}")

    user_dir = ensure_dir(f"data/users/{user_id}")

    try:
        # === 1. DNA Processing ===
        dna_report = {"pgs_results": {"percentile": 50, "z_score": 0.0}}
        plot_path = None  # Initialize plot_path

        if dna_file:
            try:
                path = f"{user_dir}/genome.txt"

                # Handle different types of file input from Gradio
                if hasattr(dna_file, 'save'):
                    # File object with save method
                    dna_file.save(path)
                elif hasattr(dna_file, 'name'):
                    # File path string - copy the file
                    import shutil
                    shutil.copy2(dna_file.name, path)
                else:
                    # String content - write directly
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(str(dna_file))

                logger.info(f"DNA file saved: {path}")

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
        else:
            logger.info("No DNA file uploaded — using default score")

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

            logger.info("Running lesson bot agent (this may take a while)...")
            try:
                lesson = run_lesson_bot(log_text or "No log provided")
                logger.info(
                    f"Lesson bot completed - generated {len(lesson.get('words', []))} words and {len(lesson.get('sentences', []))} sentences")
            except Exception as lesson_error:
                logger.error(f"Lesson bot specifically failed: {lesson_error}")
                lesson = {
                    "words": [
                        "今日 (きょう) – today",
                        "勉強 (べんきょう) – study",
                        "日本語 (にほんご) – Japanese"
                    ],
                    "sentences": [
                        "今日は日本語を勉強しました。"
                    ]
                }
            logger.info("AI agents completed")
        except Exception as e:
            logger.error(f"AI agent failed: {e}", exc_info=True)
            method = {"focus": "Balanced", "blocks": [
                "60min study", "30min review"]}
            progress = {"graph": None, "b2_months": 18,
                        "vocab": 150, "cefr": "A1"}
            # Provide meaningful fallback lesson content
            lesson = {
                "words": [
                    "今日 (きょう) – today",
                    "勉強 (べんきょう) – study",
                    "日本語 (にほんご) – Japanese",
                    "ありがとう (ありがとう) – thank you",
                    "こんにちは (こんにちは) – hello"
                ],
                "sentences": [
                    "今日は日本語を勉強しました。",
                    "ありがとうございます。",
                    "こんにちは、元気ですか？"
                ]
            }

        # === 4. Generate Outputs ===
        pdf_path = generate_pdf(dna_report, method, progress, lesson, user_id)
        anki_path = export_anki(lesson, user_id)
        audio_path = generate_audio(lesson["sentences"], user_id)

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


# === Gradio UI ===
with gr.Blocks(
    title="GENELINGUA v7 — DNA + AI Language Coach",
    theme=gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="emerald",
        neutral_hue="slate",
    ),
    css="""
    .gradio-container {
        max-width: 1200px !important;
        margin: auto !important;
    }
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .input-section {
        background: rgba(255,255,255,0.8);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.05);
        border: 1px solid rgba(255,255,255,0.2);
    }
    .output-section {
        background: rgba(248,250,252,0.9);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.05);
        border: 1px solid rgba(226,232,240,0.8);
    }
    .generate-btn {
        background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%) !important;
        border: none !important;
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        padding: 0.8rem 2rem !important;
        border-radius: 25px !important;
        box-shadow: 0 4px 16px rgba(34,197,94,0.3) !important;
        transition: all 0.3s ease !important;
    }
    .generate-btn:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(34,197,94,0.4) !important;
    }
    .download-section {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-top: 2rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.05);
    }
    .section-title {
        color: #1e293b;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .info-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border-left: 4px solid #3b82f6;
    }
    """
) as demo:
    # Header
    with gr.Row():
        gr.HTML("""
        <div class="main-header">
            <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700;">
                🧬 GENELINGUA v7
            </h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
                Your Personalized DNA + AI Language Learning Coach
            </p>
            <p style="margin: 0.5rem 0 0 0; font-size: 1rem; opacity: 0.8;">
                Upload your 23andMe data and get a customized Japanese learning plan based on your genetics
            </p>
        </div>
        """)

    # Input Section
    with gr.Group():
        gr.HTML('<div class="section-title">👤 Personal Information</div>')
        with gr.Row():
            with gr.Column(scale=2):
                user_id = gr.Textbox(
                    value="alex",
                    label="🏷️ Your Name/ID",
                    placeholder="Enter your name or unique ID"
                )
            with gr.Column(scale=2):
                ancestry = gr.Dropdown(
                    choices=[
                        ("European", "EUR"),
                        ("East Asian", "EAS"),
                        ("South Asian", "SAS"),
                        ("African", "AFR"),
                        ("American", "AMR"),
                        ("Middle Eastern/North African", "MENA"),
                        ("Other", "OTH")
                    ],
                    value="EAS",
                    label="🌍 Ancestry Background"
                )
            with gr.Column(scale=2):
                mbti = gr.Dropdown(
                    choices=[
                        "INTJ", "INTP", "ENTJ", "ENTP",
                        "INFJ", "INFP", "ENFJ", "ENFP",
                        "ISTJ", "ISFJ", "ESTJ", "ESFJ",
                        "ISTP", "ISFP", "ESTP", "ESFP"
                    ],
                    value="INTJ",
                    label="🧠 MBTI Personality Type"
                )

    with gr.Group():
        gr.HTML('<div class="section-title">🧬 Genetic Data & Learning Context</div>')
        with gr.Row():
            with gr.Column(scale=2):
                dna_file = gr.File(
                    label="📁 Upload 23andMe DNA File",
                    file_types=[".txt", ".zip"]
                )
            with gr.Column(scale=3):
                log_text = gr.Textbox(
                    value="Team meeting, ate sushi",
                    label="📝 Today's Activities",
                    placeholder="What did you do today? (e.g., work meeting, dinner with friends, watched anime)",
                    lines=3
                )

    with gr.Group():
        gr.HTML('<div class="section-title">📸 Optional Inputs</div>')
        with gr.Row():
            photo = gr.Image(
                label="📷 Daily Photo (Optional)",
                type="filepath"
            )
            voice_file = gr.Audio(
                label="🎤 Voice Log (Optional)",
                type="filepath"
            )    # Generate Button
    with gr.Row():
        btn = gr.Button(
            "🚀 Generate My Personalized Language Plan",
            variant="primary",
            size="lg",
            elem_classes=["generate-btn"]
        )

    # Results Section
    gr.HTML('<div class="section-title" style="margin-top: 2rem;">📊 Your Personalized Results</div>')

    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                gr.HTML('<div class="section-title">🧬 DNA Analysis</div>')
                dna_out = gr.Markdown(elem_classes=["info-card"])

            with gr.Group():
                gr.HTML('<div class="section-title">📚 Study Method</div>')
                method_out = gr.Markdown(elem_classes=["info-card"])

            with gr.Group():
                gr.HTML('<div class="section-title">📈 Progress Tracker</div>')
                progress_plot = gr.Image(
                    label="Your Learning Progress Chart",
                    show_label=False
                )

        with gr.Column(scale=1):
            with gr.Group():
                gr.HTML(
                    '<div class="section-title">🎌 Today\'s Japanese Lesson</div>')
                words_out = gr.Markdown(
                    label="Vocabulary Words",
                    elem_classes=["info-card"]
                )
                sentences_out = gr.Markdown(
                    label="Practice Sentences",
                    elem_classes=["info-card"]
                )

            with gr.Group():
                gr.HTML('<div class="section-title">📊 Detailed DNA Report</div>')
                dna_plot = gr.Image(
                    label="Genetic Analysis Visualization",
                    show_label=False
                )

    # Download Section
    with gr.Group():
        gr.HTML("""
        <div class="download-section">
            <div class="section-title">💾 Download Your Resources</div>
            <p style="margin: 0 0 1rem 0; color: #64748b;">
                Get your personalized learning materials in multiple formats
            </p>
        </div>
        """)
        with gr.Row():
            pdf_out = gr.File(
                label="📄 Complete PDF Report",
                file_count="single"
            )
            anki_out = gr.File(
                label="🎴 Anki Flashcard Deck",
                file_count="single"
            )
            audio_out = gr.File(
                label="🔊 Audio Pronunciation Guide",
                file_count="single"
            )

    # === Button Action ===
    btn.click(
        fn=process_user,
        inputs=[user_id, dna_file, ancestry,
                mbti, log_text, photo, voice_file],
        outputs=[
            dna_out, method_out, progress_plot,
            words_out, sentences_out, dna_plot,
            pdf_out, anki_out, audio_out
        ]
    )

# === Launch ===
if __name__ == "__main__":
    logger.info("Launching GENELINGUA v7 Gradio app...")

    # Serve static files
    import os
    static_path = os.path.join(os.getcwd(), "static")

    demo.launch(
        share=True,
        server_name="0.0.0.0",
        server_port=7860,
        favicon_path="static/favicon.ico" if os.path.exists(
            "static/favicon.ico") else None,
        show_error=True
    )
