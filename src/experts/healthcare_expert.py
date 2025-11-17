# agents/healthcare_expert.py
# ================================================
# Dutch Healthcare Expert AI - B1→B2 Medical Dutch
# For foreign healthcare professionals preparing for BIG registration
# ================================================

import re
import os
import json
import requests
from typing import Optional, List, Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
DEFAULT_MODEL = "google/gemma-2-9b-it"
FALLBACK_MODEL = "deepseek-ai/DeepSeek-R1:together"
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

# === SCENARIOS ===
HEALTHCARE_SCENARIOS = {
    "anamnese": {
        "title": "Patient History Taking (Anamnese)",
        "description": "Practice taking a patient's medical history",
        "context": "A 45-year-old patient comes to your consultation with chest complaints.",
        "ai_role": "You are the patient with chest pain for 2 days.",
        "learning_goals": ["Ask about symptom onset", "Assess pain characteristics", "Check for risk factors"]
    },
    "symptom_assessment": {
        "title": "Symptom Assessment",
        "description": "Practice detailed symptom evaluation",
        "context": "A patient describes abdominal pain. You need to assess the nature, location, and severity.",
        "ai_role": "You are a patient with lower right abdominal pain.",
        "learning_goals": ["Pain location terminology", "Severity assessment", "Associated symptoms"]
    },
    "diagnosis_explanation": {
        "title": "Explaining Diagnosis",
        "description": "Explain a medical condition to a patient",
        "context": "You need to explain to a patient they have high blood pressure (hypertension).",
        "ai_role": "You are a worried patient who just received test results.",
        "learning_goals": ["Simple medical explanations", "Avoiding jargon", "Reassurance language"]
    },
    "medication_instructions": {
        "title": "Medication Instructions",
        "description": "Provide clear medication guidance",
        "context": "Prescribe antibiotics to a patient with a bacterial infection.",
        "ai_role": "You are a patient who needs clear instructions on taking medication.",
        "learning_goals": ["Dosage instructions", "Timing vocabulary", "Side effects explanation"]
    },
    "emergency_assessment": {
        "title": "Emergency Assessment",
        "description": "Handle an emergency situation",
        "context": "A patient arrives with acute breathing difficulty (dyspneu).",
        "ai_role": "You are a patient struggling to breathe, answer briefly.",
        "learning_goals": ["Rapid assessment questions", "Emergency terminology", "Calm but urgent communication"]
    },
    "phone_pharmacy": {
        "title": "Phone Call with Pharmacy",
        "description": "Coordinate medication with pharmacy",
        "context": "Call the pharmacy to verify a prescription for a patient.",
        "ai_role": "You are a pharmacy assistant.",
        "learning_goals": ["Professional phone language", "Prescription terminology", "Verification protocol"]
    }
}

# === MEDICAL VOCABULARY BANKS ===
VOCABULARY_BANKS = {
    "cardiology": [
        "hartritmestoornis – cardiac arrhythmia",
        "benauwdheid – shortness of breath",
        "hartfalen – heart failure",
        "pijn op de borst – chest pain",
        "hartkloppingen – palpitations",
        "bloeddruk – blood pressure",
        "verhoogd cholesterol – high cholesterol",
        "hartaanval – heart attack"
    ],
    "general_symptoms": [
        "klachten – complaints",
        "pijn – pain",
        "koorts – fever",
        "misselijkheid – nausea",
        "duizeligheid – dizziness",
        "vermoeidheid – fatigue",
        "hoofdpijn – headache",
        "braken – vomiting"
    ],
    "examination": [
        "onderzoek – examination",
        "bloedonderzoek – blood test",
        "röntgenfoto – X-ray",
        "ECG – ECG/EKG",
        "lichamelijk onderzoek – physical examination",
        "diagnose – diagnosis",
        "behandeling – treatment",
        "doorverwijzing – referral"
    ],
    "pain_descriptors": [
        "stekend – stabbing",
        "drukkend – pressing",
        "schietend – shooting",
        "dof – dull",
        "kloppend – throbbing",
        "brandend – burning",
        "krampachtig – cramping",
        "constant – constant"
    ]
}

# === API FUNCTIONS ===


def generate_with_api(messages: List[Dict], max_tokens: int = 400, model: str = DEFAULT_MODEL) -> Optional[str]:
    try:
        print(f"[API] Using {model}...")
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True,
            "stop": None
        }

        headers = {"Content-Type": "application/json"}
        token = os.getenv("HF_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = requests.post(
            HF_API_URL, json=payload, headers=headers, timeout=40)

        if response.status_code == 503:
            print("[API] Model loading, retrying in 15s...")
            import time
            time.sleep(15)
            response = requests.post(
                HF_API_URL, json=payload, headers=headers, timeout=40)

        if response.status_code in (401, 403):
            headers.pop("Authorization", None)
            response = requests.post(
                HF_API_URL, json=payload, headers=headers, timeout=40)

        if response.status_code != 200:
            print(f"[API] Error {response.status_code}: {response.text[:200]}")
            return None

        text = response.json()["choices"][0]["message"]["content"].strip()
        print(f"[API] Success ({len(text)} chars)")
        return text

    except Exception as e:
        print(f"[API] Exception: {e}")
        return None


def try_generate(system: str, user: str, max_tokens: int = 400) -> Optional[str]:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]

    raw = generate_with_api(messages, max_tokens, DEFAULT_MODEL)
    if raw:
        return raw

    print("[API] Gemma failed, trying DeepSeek...")
    raw = generate_with_api(messages, max_tokens, FALLBACK_MODEL)
    if raw and "<think>" in raw:
        raw = raw.split("</think>")[-1].strip()
    return raw


# === CONVERSATION ENGINE ===
def generate_patient_response(
    scenario: str,
    conversation_history: List[Dict],
    user_input: str
) -> str:
    """Generate AI patient response in Dutch"""

    scenario_info = HEALTHCARE_SCENARIOS.get(
        scenario, HEALTHCARE_SCENARIOS["anamnese"])

    system_prompt = f"""Je bent een Nederlandse patiënt in een medisch rollenspel. {scenario_info['ai_role']}

BELANGRIJK:
- Antwoord ALLEEN in het Nederlands
- Blijf in je rol als patiënt
- Geef realistische medische details
- Wees soms vaag of onzeker (zoals echte patiënten)
- Gebruik informele taal (geen medische jargon tenzij je arts ben)
- Houd antwoorden kort (2-3 zinnen maximaal)

Context van dit gesprek: {scenario_info['context']}"""

    # Build conversation context
    history_text = "\n".join([
        f"{'Arts' if msg['role'] == 'user' else 'Patiënt'}: {msg['content']}"
        for msg in conversation_history[-6:]  # Last 3 exchanges
    ])

    user_prompt = f"""Vorige gesprek:
{history_text}

Arts: {user_input}

Antwoord als patiënt (kort en natuurlijk in Nederlands):"""

    response = try_generate(system_prompt, user_prompt, 300)
    return response if response else "Ik begrijp het niet helemaal. Kunt u het anders uitleggen?"


def analyze_medical_dutch(user_input: str, scenario: str) -> Dict:
    """Analyze user's Dutch and provide B1→B2 feedback"""

    system_prompt = """Je bent een Nederlandse taalcoach voor medisch Nederlands.
Analyseer de zin van de arts en geef feedback.

FORMAAT (gebruik EXACT deze structuur):
NIVEAU: [B1/B2/C1]
GRAMMATICA: [correctie als nodig, anders "✓ Correct"]
B2_VERBETERING: [verbeterde versie van de zin]
MEDISCH_VOCABULAIRE: [1-2 nieuwe medische woorden, formaat: "nederlands – english"]
PROFESSIONAL_TIP: [1 tip voor professionelere medische communicatie]

Wees constructief maar eerlijk."""

    user_prompt = f"""Scenario: {HEALTHCARE_SCENARIOS.get(scenario, {}).get('title', 'Medical consultation')}

Arts zegt: "{user_input}"

Geef feedback:"""

    raw = try_generate(system_prompt, user_prompt, 450)

    if not raw:
        return {
            "level": "B1",
            "grammar": "Kon niet analyseren",
            "b2_improvement": user_input,
            "vocabulary": [],
            "tip": "Probeer meer specifieke medische termen te gebruiken."
        }

    # Parse feedback
    level_match = re.search(r"NIVEAU:\s*(\w+)", raw)
    grammar_match = re.search(
        r"GRAMMATICA:\s*(.+?)(?=\n[A-Z_]+:|$)", raw, re.DOTALL)
    b2_match = re.search(
        r"B2_VERBETERING:\s*(.+?)(?=\n[A-Z_]+:|$)", raw, re.DOTALL)
    vocab_match = re.search(
        r"MEDISCH_VOCABULAIRE:\s*(.+?)(?=\n[A-Z_]+:|$)", raw, re.DOTALL)
    tip_match = re.search(
        r"PROFESSIONAL_TIP:\s*(.+?)(?=\n[A-Z_]+:|$)", raw, re.DOTALL)

    # Extract vocabulary items
    vocab_items = []
    if vocab_match:
        vocab_text = vocab_match.group(1).strip()
        for line in vocab_text.split("\n"):
            if "–" in line or "-" in line:
                clean = re.sub(r"^[-•\*\d\.\)]\s*", "", line).strip()
                if clean:
                    vocab_items.append(clean)

    return {
        "level": level_match.group(1) if level_match else "B1",
        "grammar": grammar_match.group(1).strip() if grammar_match else "✓ Correct",
        "b2_improvement": b2_match.group(1).strip() if b2_match else user_input,
        "vocabulary": vocab_items[:2],
        "tip": tip_match.group(1).strip() if tip_match else "Blijf oefenen!"
    }


def get_scenario_vocabulary(scenario: str) -> List[str]:
    """Get relevant vocabulary for the scenario"""

    # Map scenarios to vocabulary categories
    scenario_vocab_map = {
        "anamnese": ["general_symptoms", "examination"],
        "symptom_assessment": ["pain_descriptors", "general_symptoms"],
        "diagnosis_explanation": ["examination", "cardiology"],
        "medication_instructions": ["examination"],
        "emergency_assessment": ["cardiology", "general_symptoms"],
        "phone_pharmacy": ["examination"]
    }

    categories = scenario_vocab_map.get(scenario, ["general_symptoms"])
    vocab = []

    for cat in categories:
        vocab.extend(VOCABULARY_BANKS.get(cat, [])[:4])

    return vocab[:8]


# === MAIN CONVERSATION FUNCTION ===
def run_healthcare_conversation(
    scenario: str,
    user_input: str,
    conversation_history: List[Dict] = None
) -> Dict:
    """
    Main function to handle healthcare roleplay conversation

    Args:
        scenario: One of HEALTHCARE_SCENARIOS keys
        user_input: What the healthcare professional says
        conversation_history: Previous messages [{"role": "user/assistant", "content": "..."}]

    Returns:
        {
            "patient_response": "Dutch response from AI patient",
            "feedback": {
                "level": "B1/B2",
                "grammar": "correction or ✓",
                "b2_improvement": "improved version",
                "vocabulary": ["word – translation", ...],
                "tip": "professional communication tip"
            },
            "scenario_vocab": ["relevant medical vocabulary"],
            "history": updated_conversation_history
        }
    """

    if conversation_history is None:
        conversation_history = []

    print(f"\n{'='*60}")
    print(f"HEALTHCARE EXPERT AI - Scenario: {scenario.upper()}")
    print(f"{'='*60}\n")

    if not user_input.strip():
        return {
            "error": "Leeg bericht ontvangen",
            "patient_response": None,
            "feedback": None
        }

    # Generate patient response
    print("[1/3] Generating patient response...")
    patient_response = generate_patient_response(
        scenario, conversation_history, user_input)

    # Analyze user's Dutch
    print("[2/3] Analyzing your Dutch...")
    feedback = analyze_medical_dutch(user_input, scenario)

    # Get scenario vocabulary
    print("[3/3] Fetching scenario vocabulary...")
    scenario_vocab = get_scenario_vocabulary(scenario)

    # Update history
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append(
        {"role": "assistant", "content": patient_response})

    print("\n✓ Conversation turn complete\n")

    return {
        "patient_response": patient_response,
        "feedback": feedback,
        "scenario_vocab": scenario_vocab,
        "history": conversation_history
    }


# === CLI INTERFACE ===
def print_scenario_menu():
    print("\n" + "="*60)
    print("AVAILABLE SCENARIOS".center(60))
    print("="*60 + "\n")

    for idx, (key, info) in enumerate(HEALTHCARE_SCENARIOS.items(), 1):
        print(f"{idx}. {info['title']}")
        print(f"   {info['description']}")
        print(f"   Context: {info['context']}\n")


def format_feedback(feedback: Dict):
    print("\n" + "─"*60)
    print("📊 FEEDBACK".center(60))
    print("─"*60)
    print(f"\n🎯 Your Level: {feedback['level']}")
    print(f"\n✏️  Grammar: {feedback['grammar']}")
    print(f"\n📈 B2 Improvement:\n   {feedback['b2_improvement']}")

    if feedback['vocabulary']:
        print(f"\n📚 New Vocabulary:")
        for word in feedback['vocabulary']:
            print(f"   • {word}")

    print(f"\n💡 Professional Tip:\n   {feedback['tip']}")
    print("\n" + "─"*60 + "\n")


def run_interactive_session():
    """Interactive CLI for testing"""

    print("\n🏥 DUTCH HEALTHCARE EXPERT AI - B1→B2 Medical Dutch")
    print("="*60)

    print_scenario_menu()

    choice = input("Select scenario (1-6) or 'q' to quit: ").strip()

    if choice.lower() == 'q':
        return

    try:
        scenario_idx = int(choice) - 1
        scenario_key = list(HEALTHCARE_SCENARIOS.keys())[scenario_idx]
    except (ValueError, IndexError):
        print("❌ Invalid choice")
        return

    scenario_info = HEALTHCARE_SCENARIOS[scenario_key]
    conversation_history = []

    print(f"\n{'='*60}")
    print(f"SCENARIO: {scenario_info['title']}")
    print(f"{'='*60}")
    print(f"\n📋 Context: {scenario_info['context']}")
    print(f"🎭 Your role: Healthcare professional")
    print(f"🤖 AI role: {scenario_info['ai_role']}")
    print(f"\n📝 Learning goals:")
    for goal in scenario_info['learning_goals']:
        print(f"   • {goal}")
    print("\nType 'end' to finish, 'vocab' for vocabulary, 'new' for new scenario\n")

    turn = 1
    while True:
        user_input = input(f"\n[Turn {turn}] You (Arts): ").strip()

        if user_input.lower() == 'end':
            print("\n✓ Session ended. Bedankt voor het oefenen!")
            break

        if user_input.lower() == 'vocab':
            vocab = get_scenario_vocabulary(scenario_key)
            print("\n📚 Relevant vocabulary for this scenario:")
            for item in vocab:
                print(f"   • {item}")
            continue

        if user_input.lower() == 'new':
            run_interactive_session()
            return

        if not user_input:
            continue

        result = run_healthcare_conversation(
            scenario_key,
            user_input,
            conversation_history
        )

        if "error" in result:
            print(f"❌ Error: {result['error']}")
            continue

        print(f"\n🤖 Patient: {result['patient_response']}")

        format_feedback(result['feedback'])

        conversation_history = result['history']
        turn += 1


# === MAIN ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Quick test mode
        print("\n🧪 QUICK TEST MODE\n")

        test_input = "Goedemorgen, wat kan ik voor u doen vandaag?"

        result = run_healthcare_conversation(
            "anamnese",
            test_input,
            []
        )

        print(f"You: {test_input}")
        print(f"\nPatient: {result['patient_response']}")
        format_feedback(result['feedback'])

        print("\n📚 Scenario Vocabulary:")
        for vocab in result['scenario_vocab']:
            print(f"   • {vocab}")
    else:
        # Interactive mode
        run_interactive_session()
