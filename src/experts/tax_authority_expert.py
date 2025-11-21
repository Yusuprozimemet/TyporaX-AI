"""
Tax Authority Expert for practicing Dutch phone calls with Belastingdienst.
Mirrors healthcare_expert.py architecture: synchronous, dict-based scenarios, API generation with fallbacks.
"""

from typing import Dict, List
from config.settings import config
import re
import requests
from datetime import datetime

DEFAULT_MODEL = config.DEFAULT_MODEL
FALLBACK_MODEL = config.FALLBACK_MODEL
HF_API_URL = config.HF_API_URL
HF_TOKEN = config.HF_TOKEN


# === TAX AUTHORITY SCENARIOS (dict-based, like healthcare expert) ===
TAX_AUTHORITY_SCENARIOS = {
    "tax_authority": {
        "title": "Belastingdienst Phone Call",
        "description": "Practice calling the Dutch tax authority (Belastingdienst) to inquire about tax returns, refunds, and filing deadlines",
        "context": "You are calling the tax authority's main line to ask about your tax return filing",
        "system_prompt": "Je bent een professionele receptionist van de Belastingdienst. Je helpt een leerder Nederlands spreken via een telefoongesprek. Spreek uitsluitend Nederlands. Stel vragen over belastingaangiften, BSN-nummers en geboortedatum. Geef duidelijke, bondige antwoorden geschikt voor telefoonverkeer.",
        "agent_instructions": "Gedraag je als een beleefde Belastingdienst-receptionist.\n1) Spreek uitsluitend Nederlands.\n2) Vraag naam, geboortedatum of BSN-nummer als nodig.\n3) Stel ophelderingsvragen over de belastingvraag (aangifte, teruggave, toeslagen, etc.).\n4) Geef bondige en professionele antwoorden.\n5) Hou antwoorden kort en geschikt voor telefoon.",
        "sample_agent_responses": [
            "Goedemorgen, u spreekt met de Belastingdienst. Waarmee kan ik u helpen?",
            "Kunt u uw naam en geboortedatum doorgeven?",
            "Voor welke aangifte heeft u hulp nodig: inkomstenbelasting of toeslagen?",
            "De uiterste datum voor de aangifte is 1 mei.",
            "Ik zal dat voor u controleren, een ogenblik alstublieft."
        ],
        "rubric": {
            "required_items": [
                "name",
                "date_of_birth",
                "state_reason_for_call",
                "ask_for_next_steps_or_followup"
            ],
            "scoring_notes": "Beoordeel op basis van aanwezigheid van verplichte onderdelen, duidelijkheid van Nederlands, beleefdheid en correct gebruik van data/nummers."
        }
    }
}


# === VOCABULARY BANKS (like healthcare expert) ===
VOCABULARY_BANKS = {
    "tax_terms": [
        "aangifte – tax return",
        "teruggave – refund",
        "toeslagen – allowances",
        "BSN – citizen service number",
        "belasting – tax",
        "geboortedatum – date of birth",
        "inkomstenbelasting – income tax",
        "loonbelasting – wage tax",
        "deadline – deadline",
        "document – document"
    ],
    "administrative": [
        "formulier – form",
        "bewijs – proof",
        "verificatie – verification",
        "registratie – registration",
        "bewaargeving – statement",
        "bevestiging – confirmation"
    ],
    "communication": [
        "kunt u – can you",
        "zou u – would you",
        "alstublieft – please",
        "dank u – thank you",
        "nogmaals – again",
        "duidelijk – clear"
    ]
}


def try_generate(system_prompt: str, user_input: str, scenario: str) -> str:
    """
    Try to generate a response using HF API, with fallback model
    Mirrors healthcare_expert.py try_generate pattern
    """
    if not HF_TOKEN or not HF_API_URL:
        return None

    for model in [DEFAULT_MODEL, FALLBACK_MODEL]:
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                "max_tokens": 200,
                "temperature": 0.5
            }

            headers = {
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                HF_API_URL,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, dict):
                    choices = result.get("choices", [])
                    if choices and isinstance(choices, list):
                        reply = choices[0].get("message", {}).get("content")
                        if reply:
                            return reply.strip()

        except Exception as e:
            print(f"Warning: Model {model} failed: {e}")
            continue

    return None


def generate_tax_authority_response(scenario: str, conversation_history: List[Dict], user_input: str) -> str:
    """
    Generate a response from the tax authority representative
    Mirrors healthcare_expert.py generate_patient_response pattern
    """
    if scenario not in TAX_AUTHORITY_SCENARIOS:
        scenario = "tax_authority"

    scenario_data = TAX_AUTHORITY_SCENARIOS[scenario]
    system_prompt = scenario_data.get(
        "system_prompt", "Je bent een Belastingdienst receptionist")

    # Build conversation context
    messages = system_prompt + "\n\n"
    for h in conversation_history[-6:]:
        role = h.get("role", "").title()
        messages += f"{role}: {h.get('content', '')}\n"

    messages += f"\nLeaner: {user_input}\n\nRespond as tax authority:"

    # Try API generation
    api_response = try_generate(system_prompt, user_input, scenario)
    if api_response:
        return api_response

    # Fallback heuristics
    lower = user_input.lower()

    tax_responses = {
        "teruggave": "Ik zal uw gegevens controleren. Kunt u uw BSN nummer geven?",
        "aangifte": "Welke soort aangifte? Inkomstenbelasting of toeslagen?",
        "deadline": "De uiterste datum is 1 mei. Heeft u nog vragen?",
        "toeslagen": "Kunt u uw geboortedatum geven voor verificatie?",
        "bsn": "Bedankt. Ik zal dat voor u naslaan.",
        "document": "Welke documenten heeft u nodig? Ik kan dat uitleggen.",
    }

    for keyword, response in tax_responses.items():
        if keyword in lower:
            return response

    # Default fallback
    samples = scenario_data.get("sample_agent_responses", [])
    return samples[len(conversation_history) % max(1, len(samples))] if samples else "Hoe kan ik u verder helpen?"


def analyze_tax_dutch(user_input: str, scenario: str) -> Dict:
    """
    Analyze user's Dutch in tax authority context
    Mirrors healthcare_expert.py analyze_medical_dutch pattern
    """
    raw = f"Analyzing: {user_input}"

    # Check politeness
    politeness_phrases = ["alstublieft", "dank u", "toe", "zou u",
                          "kunt u", "graag", "dank", "a.u.b"]
    has_politeness = any(p in user_input.lower() for p in politeness_phrases)

    # Check for required elements
    has_subject = any(w in user_input.lower() for w in [
                      "aangifte", "teruggave", "toeslagen", "belasting", "bsn"])
    has_question = "?" in user_input or any(
        w in user_input.lower() for w in ["wat", "hoe", "wanneer", "waar", "wie"])

    # Simple grammar feedback
    if len(user_input) < 5:
        grammar_fb = "✓ Brief, maar helder"
    elif "ik ben" in user_input.lower() or "mijn naam" in user_input.lower():
        grammar_fb = "✓ Goed gebruik van persoonsvorm"
    else:
        grammar_fb = "✓ Correct Nederlands"

    level = "B2" if (has_question and has_subject and
                     len(user_input) > 20) else "B1"

    return {
        "level": level,
        "grammar": grammar_fb,
        "b2_improvement": user_input if len(user_input) > 15 else f"Uitgebreider: {user_input}...",
        "vocabulary": ["aangifte – tax return", "teruggave – refund", "toeslagen – allowances"][:2],
        "tip": "Beleefde toon gebruiken: 'zou u kunnen...' of 'kunt u...' helpt!" if not has_politeness else "Goede beleefdheidstoon! Ga zo door."
    }


def get_scenario_vocabulary(scenario: str) -> List[str]:
    """Get relevant vocabulary for the scenario"""
    vocab = []
    vocab.extend(VOCABULARY_BANKS.get("tax_terms", [])[:4])
    vocab.extend(VOCABULARY_BANKS.get("communication", [])[:2])
    return vocab[:8]


# === MAIN CONVERSATION FUNCTION ===
def run_tax_authority_conversation(
    scenario: str,
    user_input: str,
    conversation_history: List[Dict] = None
) -> Dict:
    """
    Main function to handle tax authority roleplay conversation
    Mirrors healthcare_expert.py run_healthcare_conversation pattern

    Args:
        scenario: One of TAX_AUTHORITY_SCENARIOS keys
        user_input: What the caller says
        conversation_history: Previous messages [{"role": "user/assistant", "content": "..."}]

    Returns:
        {
            "agent_response": "Dutch response from tax authority",
            "feedback": {
                "level": "B1/B2",
                "grammar": "correction or ✓",
                "b2_improvement": "improved version",
                "vocabulary": ["word – translation", ...],
                "tip": "communication tip"
            },
            "scenario_vocab": ["relevant tax vocabulary"],
            "history": updated_conversation_history
        }
    """

    if conversation_history is None:
        conversation_history = []

    print(f"\n{'='*60}")
    print(f"TAX AUTHORITY EXPERT - Scenario: {scenario.upper()}")
    print(f"{'='*60}\n")

    if not user_input.strip():
        return {
            "error": "Leeg bericht ontvangen",
            "agent_response": None,
            "feedback": None
        }

    # Generate agent response
    print("[1/3] Generating tax authority response...")
    agent_response = generate_tax_authority_response(
        scenario, conversation_history, user_input)

    # Analyze user's Dutch
    print("[2/3] Analyzing your Dutch...")
    feedback = analyze_tax_dutch(user_input, scenario)

    # Get scenario vocabulary
    print("[3/3] Fetching scenario vocabulary...")
    scenario_vocab = get_scenario_vocabulary(scenario)

    # Update history
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append(
        {"role": "assistant", "content": agent_response})

    print("\n✓ Conversation turn complete\n")

    return {
        "agent_response": agent_response,
        "feedback": feedback,
        "scenario_vocab": scenario_vocab,
        "history": conversation_history
    }
