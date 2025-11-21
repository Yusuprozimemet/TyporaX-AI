"""
Simple scenario expert for medical-practice phone-call simulations.

This is a text-only scaffold: it loads prompt templates from `prompts/` and
provides a minimal session lifecycle: start_session, respond_to_text, score_attempt.

The scoring is heuristic-based (keyword presence) so it's usable offline
for testing and early UX work. Replace scoring with LLM-based evaluation later.
"""
from config.settings import config
import os
import json
import uuid
import re
from datetime import datetime

from dotenv import load_dotenv
import httpx

# Ensure environment variables are loaded (for HF/GROQ tokens)
load_dotenv()

# === CONFIG ===

DEFAULT_MODEL = config.DEFAULT_MODEL
FALLBACK_MODEL = config.FALLBACK_MODEL
HF_API_URL = config.HF_API_URL
HF_TOKEN = config.HF_TOKEN


class MedicalCallExpert:
    def __init__(self, scenario_id: str):
        self.scenario_id = scenario_id
        self.prompt = self._load_prompt(scenario_id)

    def _load_prompt(self, scenario_id: str):
        path = os.path.join("prompts", f"{scenario_id}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Prompt not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def start_session(self, user_id: str):
        session = {
            "session_id": str(uuid.uuid4()),
            "user_id": user_id,
            "scenario_id": self.scenario_id,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "history": []
        }
        # Use the first agent sample phrase as the greeting
        agent_greeting = None
        try:
            agent_greeting = self.prompt.get(
                "sample_phrases", {}).get("agent", [])[0]
        except Exception:
            agent_greeting = "Hello, how can I help you today?"

        session["history"].append({"role": "agent", "text": agent_greeting})
        session["last_agent"] = agent_greeting
        return session

    def respond_to_text(self, session: dict, user_text: str):
        # Append learner turn
        session["history"].append({"role": "learner", "text": user_text})

        # Try to generate a natural response via configured HF/Groq API when a token is available
        if HF_TOKEN:
            try:
                system_prompt = self.prompt.get("system") or self.prompt.get(
                    "agent_instructions") or "You are a helpful medical receptionist."

                # Build a messages array using recent session history
                messages = [{"role": "system", "content": system_prompt}]
                for h in session.get("history", [])[-8:]:
                    role = "user" if h.get("role") in (
                        "learner", "user") else "assistant"
                    messages.append({"role": role, "content": h.get("text")})

                messages.append({"role": "user", "content": user_text})

                payload = {
                    "model": DEFAULT_MODEL or FALLBACK_MODEL,
                    "messages": messages,
                    "max_tokens": 200,
                    "temperature": 0.6
                }

                headers = {"Authorization": f"Bearer {HF_TOKEN}",
                           "Content-Type": "application/json"}

                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(
                        HF_API_URL, json=payload, headers=headers)
                    resp.raise_for_status()
                    result = resp.json()

                assistant_text = None
                if isinstance(result, dict):
                    choices = result.get("choices") or []
                    if choices and isinstance(choices, list):
                        assistant_text = choices[0].get("message", {}).get(
                            "content") or choices[0].get("text")
                    if not assistant_text and "output" in result:
                        assistant_text = result.get("output")

                if assistant_text:
                    reply = assistant_text.strip()
                    session["history"].append({"role": "agent", "text": reply})
                    session["last_agent"] = reply
                    return reply
            except Exception as e:
                # API call failed; log and fall back to local heuristics
                print(
                    f"Warning: model API call failed in MedicalCallExpert: {e}")

        # Offline fallback heuristics
        lower = user_text.lower()
        if any(k in lower for k in ["appointment", "afspraak", "afspraak maken", "make an appointment", "rendez-vous", "预约"]):
            reply = "I can offer you an appointment. May I have your full name and date of birth, please?"
        elif any(k in lower for k in ["name", "naam", "my name", "je m'appelle", "我叫"]):
            reply = "Thank you. Can you also tell me your date of birth and a short description of the problem?"
        elif any(k in lower for k in ["thank", "dank", "dankjewel", "merci", "谢谢"]):
            reply = "You're welcome. Is there anything else I can help with?"
        else:
            samples = self.prompt.get("sample_phrases", {}).get("agent", [])
            reply = samples[len(session.get("history", [])) % max(
                1, len(samples))] if samples else "I see. Could you please clarify?"

        session["history"].append({"role": "agent", "text": reply})
        session["last_agent"] = reply
        return reply

    def score_attempt(self, transcript: str):
        # Very small heuristic scorer based on prompt.rubric.required_items
        rubric = self.prompt.get("rubric", {})
        required = rubric.get("required_items", [])

        lower = transcript.lower()
        found = 0
        found_items = []
        for item in required:
            key = item.lower()
            # map some common synonyms
            checks = [key]
            if key in ["name", "naam", "nom", "姓名"]:
                checks += ["name", "naam", "nom", "姓名", "叫"]
            if key in ["date of birth", "date de naissance", "geboortedatum", "出生日期"]:
                checks += ["date", "birth", "dob",
                           "geboortedatum", "date of birth", "出生"]
            if key in ["reason/symptoms", "symptômes", "症状"]:
                checks += ["symptom", "symptoms", "cough",
                           "fever", "hoofdpijn", "koorts", "pijn", "症状"]

            matched = any(ch.lower() in lower for ch in checks)
            if matched:
                found += 1
                found_items.append(item)

        # Clarity: count words as rough proxy
        word_count = len(re.findall(r"\w+", transcript))
        clarity_score = min(5, max(1, word_count // 8))

        # Politeness: check for common polite tokens
        politeness = 5 if any(t in lower for t in [
                              "please", "alstublieft", "dank", "thank"]) else 3

        required_score = int((found / max(1, len(required))) * 5)

        scores = {
            "required_items_found": found_items,
            "required_score": required_score,
            "clarity_score": clarity_score,
            "politeness_score": politeness
        }

        # Normalize to 0-100
        total_raw = required_score + clarity_score + politeness
        total = int((total_raw / 15.0) * 100)

        return {"scores": scores, "total": total}
