# agents/lesson_bot.py
# ================================================
# GeneLingua Lesson Bot – FINAL, BULLETPROOF
# Author: @Yusufrozimemet (NL) – November 15, 2025
# Time: 03:40 PM CET
# FIXED: re.Match → .group(1), Gemma parsing, dedupe, output
# ================================================

import re
import os
import requests
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
DEFAULT_MODEL = "google/gemma-2-9b-it"
FALLBACK_MODEL = "deepseek-ai/DeepSeek-R1:together"
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"


def generate_with_api(messages: List[Dict], max_tokens: int = 300, model: str = DEFAULT_MODEL) -> Optional[str]:
    try:
        print(f"Using HF API ({model})...")
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "top_p": 0.9,
            "do_sample": True,
            "stop": None
        }

        headers = {"Content-Type": "application/json"}
        token = os.getenv("HF_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
            print("Using authenticated token")
        else:
            print("No HF_TOKEN – anonymous mode")

        response = requests.post(
            HF_API_URL, json=payload, headers=headers, timeout=40)

        if response.status_code == 503:
            print("Model loading… retry in 15s")
            import time
            time.sleep(15)
            response = requests.post(
                HF_API_URL, json=payload, headers=headers, timeout=40)

        if response.status_code in (401, 403):
            headers.pop("Authorization", None)
            response = requests.post(
                HF_API_URL, json=payload, headers=headers, timeout=40)

        if response.status_code != 200:
            print(f"API error {response.status_code}: {response.text[:150]}")
            return None

        text = response.json()["choices"][0]["message"]["content"].strip()
        print(f"API success ({len(text)} chars)")
        return text

    except Exception as e:
        print(f"API exception: {e}")
        return None


def try_generate(system: str, user: str, max_tokens: int = 300) -> Optional[str]:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]

    raw = generate_with_api(messages, max_tokens, DEFAULT_MODEL)
    if raw:
        return raw

    print("Gemma failed → trying DeepSeek")
    raw = generate_with_api(messages, max_tokens, FALLBACK_MODEL)
    if raw and "<think>" in raw:
        raw = raw.split("</think>")[-1].strip()
    return raw


def extract_lines_with_pattern(text: str, pattern: str) -> List[str]:
    """Extract .group(1) from regex matches."""
    if not text:
        return []
    return [m.group(1).strip() for m in re.finditer(pattern, text, re.MULTILINE) if m.group(1)]


# ----------------------------------------------------------------------
# VOCABULARY
# ----------------------------------------------------------------------
def extract_contextual_vocabulary(daily_log: str, target_language: str) -> List[str]:
    log = daily_log.strip()

    system_prompt = (
        "You are a strict language formatter. "
        "Output ONLY the list. "
        "NO reasoning, NO intro, NO numbers. "
        "Format: 'target_word – english_translation' per line."
    )

    user_prompts = {
        "dutch": f"List 10 Dutch words related to: {log}. Format: 'dutch – english'. Start now.",
        "japanese": f"List 10 Japanese words related to: {log}. Format: '日本語 (hiragana) – English'. Start now.",
        "chinese": f"List 10 Chinese words related to: {log}. Format: '中文 (pinyin) – English'. Start now."
    }

    raw = try_generate(system_prompt, user_prompts.get(
        target_language.lower(), user_prompts["dutch"]), 400)
    if not raw:
        return []

    print(f"DEBUG Vocab Raw: {raw[:500]}...")

    # Try numbered lines
    lines = extract_lines_with_pattern(
        raw, r"^\d+[\.\)]\s*(.+?)(?=\n\d+[\.\)]|\n*$)")
    if not lines:
        lines = [line.strip() for line in raw.split('\n') if ' – ' in line]

    vocab = []
    seen = set()

    for line in lines:
        clean = re.sub(r"^\d+[\.\)\]\:\-\*•]\s*", "", line).strip()
        clean = re.sub(r"\s*[-–—:]\s*", " – ", clean)

        if " – " not in clean:
            continue
        parts = [p.strip() for p in clean.split(" – ", 1)]
        if len(parts) != 2 or not parts[0] or not parts[1]:
            continue

        key = parts[0].lower()
        if key in seen:
            continue
        seen.add(key)

        if target_language.lower() == "dutch" and not re.search(r"[a-z]", parts[0], re.I):
            continue
        if target_language.lower() == "japanese" and not re.search(r"[\u3040-\u9FFF]", parts[0]):
            continue
        if target_language.lower() == "chinese" and not re.search(r"[\u4E00-\u9FFF]", parts[0]):
            continue

        vocab.append(f"{parts[0]} – {parts[1]}")

    print(f"Found {len(vocab)} vocabulary words")
    return vocab[:15]


# ----------------------------------------------------------------------
# SENTENCES
# ----------------------------------------------------------------------
def generate_contextual_sentences(daily_log: str, target_language: str) -> List[str]:
    log = daily_log.strip()

    system_prompt = (
        "You are a language tutor. "
        "Write exactly 6 short sentences in the target language. "
        "Number them 1-6. One per line. NO English, NO explanation."
    )

    user_prompts = {
        "dutch": f"Write 6 short Dutch sentences about: {log}. Number 1-6.",
        "japanese": f"Write 6 short Japanese sentences about: {log}. Number 1-6.",
        "chinese": f"Write 6 short Chinese sentences about: {log}. Number 1-6."
    }

    raw = try_generate(system_prompt, user_prompts.get(
        target_language.lower(), user_prompts["dutch"]), 450)
    if not raw:
        return []

    print(f"DEBUG Sentences Raw: {raw[:500]}...")

    matches = extract_lines_with_pattern(
        raw, r"^\d+[\.\)]\s*(.+?)(?=\n\d+[\.\)]|\n*$)")
    sentences = []
    seen = set()

    for s in matches:
        if len(s) < 10 or any(kw in s.lower() for kw in ["here", "sentence", "write", "reason", "english"]):
            continue
        if s not in seen:
            seen.add(s)
            sentences.append(s)

    print(f"Generated {len(sentences)} sentences")
    return sentences[:8]


# ----------------------------------------------------------------------
# FALLBACK & RUN
# ----------------------------------------------------------------------
def generate_fallback_content(daily_log: str, target_language: str) -> Dict:
    first = daily_log.split(",")[0].strip().split()[-1]
    if target_language.lower() == "dutch":
        return {
            "words": [
                "vandaag – today", "lab – lab", "meeting – meeting",
                "supervisor – supervisor", "experiment – experiment"
            ],
            "sentences": [
                f"Vandaag werkte ik aan {first}.",
                "Het lab was druk.",
                "De meeting was nuttig.",
                "Mijn supervisor gaf feedback.",
                "Morgen doen we een nieuw experiment."
            ]
        }
    return {"words": [], "sentences": []}


def run_lesson_bot(daily_log: str, target_language: str = "dutch") -> Dict:
    print(f"\n{'='*50}")
    print(f"Processing: '{daily_log}' → {target_language.upper()}")
    print(f"{'='*50}\n")

    if not daily_log.strip():
        raise ValueError("Empty log")

    vocab = extract_contextual_vocabulary(daily_log, target_language)
    sentences = generate_contextual_sentences(daily_log, target_language)

    if len(vocab) < 3 or len(sentences) < 3:
        print("Using fallback")
        fb = generate_fallback_content(daily_log, target_language)
        vocab = vocab or fb["words"]
        sentences = sentences or fb["sentences"]

    # Dedupe properly
    vocab = list(dict.fromkeys(vocab))[:15]
    sentences = list(dict.fromkeys(sentences))[:8]

    result = {"words": vocab, "sentences": sentences,
              "language": target_language}
    print(f"\nFINAL: {len(vocab)} words, {len(sentences)} sentences")
    return result


# === TEST ===
if __name__ == "__main__":
    result = run_lesson_bot("python, developer, job interview", "dutch")
    print("\nRESULT:")
    print("Words:")
    for w in result["words"]:
        print(f"  • {w}")
    print("\nSentences:")
    for s in result["sentences"]:
        print(f"  • {s}")
