# agents/it_backend_interviewer.py
# ================================================
# Dutch IT Backend Interview AI - B1→B2 Technical Dutch
# For foreign software engineers preparing for Dutch tech interviews
# ================================================

import re
import os
import json
import requests
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
DEFAULT_MODEL = "google/gemma-2-9b-it"
FALLBACK_MODEL = "deepseek-ai/DeepSeek-R1:together"
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

# === INTERVIEW SCENARIOS ===
INTERVIEW_SCENARIOS = {
    "system_design": {
        "title": "System Design Discussion",
        "description": "Design a scalable backend system",
        "context": "You're asked to design a REST API that handles 10,000 requests/second.",
        "ai_role": "Senior Backend Architect asking probing questions",
        "difficulty": "Hard",
        "learning_goals": ["Scalability terms", "Architecture vocabulary", "Design justification"]
    },
    "database_design": {
        "title": "Database Architecture",
        "description": "Explain database choices",
        "context": "Why did you choose PostgreSQL over MongoDB for this project?",
        "ai_role": "Technical interviewer challenging your database decisions",
        "difficulty": "Medium",
        "learning_goals": ["Database terminology", "Trade-off explanation", "Technical reasoning"]
    },
    "code_review": {
        "title": "Code Review Discussion",
        "description": "Discuss code quality and improvements",
        "context": "Review a pull request with performance issues",
        "ai_role": "Senior developer asking about code choices",
        "difficulty": "Medium",
        "learning_goals": ["Code quality terms", "Refactoring vocabulary", "Constructive feedback"]
    },
    "debugging_scenario": {
        "title": "Production Bug Investigation",
        "description": "Debug a production issue",
        "context": "There's a memory leak in production causing crashes every 6 hours.",
        "ai_role": "Stressed team lead needing your debugging approach",
        "difficulty": "Hard",
        "learning_goals": ["Debugging process terms", "Problem-solving vocabulary", "Technical communication"]
    },
    "behavioral_conflict": {
        "title": "Team Conflict Resolution",
        "description": "STAR method behavioral question",
        "context": "Tell me about a time you disagreed with a team member about technical approach.",
        "ai_role": "HR interviewer assessing soft skills",
        "difficulty": "Easy",
        "learning_goals": ["STAR method in Dutch", "Conflict resolution terms", "Professional storytelling"]
    },
    "salary_negotiation": {
        "title": "Salary Discussion",
        "description": "Negotiate compensation",
        "context": "We'd like to offer you €55,000 for this senior backend role.",
        "ai_role": "Hiring manager with some flexibility",
        "difficulty": "Medium",
        "learning_goals": ["Negotiation phrases", "Compensation terminology", "Professional pushback"]
    },
    "technical_screening": {
        "title": "Phone Screening Questions",
        "description": "Quick technical questions",
        "context": "Rapid-fire basic technical questions to assess knowledge.",
        "ai_role": "Recruiter doing initial technical screening",
        "difficulty": "Easy",
        "learning_goals": ["Quick explanations", "Fundamental concepts", "Concise Dutch"]
    },
    "architecture_discussion": {
        "title": "Microservices vs Monolith",
        "description": "Discuss architectural trade-offs",
        "context": "When would you choose microservices over a monolith?",
        "ai_role": "CTO evaluating architectural thinking",
        "difficulty": "Hard",
        "learning_goals": ["Architecture terms", "Trade-off analysis", "Strategic thinking"]
    }
}

# === TECHNICAL VOCABULARY BANKS ===
VOCABULARY_BANKS = {
    "backend_core": [
        "schaalbaarheid – scalability",
        "doorvoer – throughput",
        "vertraging – latency",
        "knelpunt – bottleneck",
        "gegevensmodel – data model",
        "API-eindpunt – API endpoint",
        "foutafhandeling – error handling",
        "prestatieverbetering – performance improvement"
    ],
    "database": [
        "normalisatie – normalization",
        "indexering – indexing",
        "queryoptimalisatie – query optimization",
        "transacties – transactions",
        "databaseschema – database schema",
        "relaties – relationships",
        "opgeslagen procedures – stored procedures",
        "back-upstrategie – backup strategy"
    ],
    "devops": [
        "containerbeheer – container management",
        "pijplijn – pipeline",
        "implementatie – deployment",
        "terugdraaien – rollback",
        "monitoring – monitoring",
        "loggen – logging",
        "continue integratie – continuous integration",
        "geautomatiseerd testen – automated testing"
    ],
    "code_quality": [
        "leesbaarheid – readability",
        "onderhoudbaarheid – maintainability",
        "technische schuld – technical debt",
        "herbruikbaarheid – reusability",
        "testdekking – test coverage",
        "code review – code review",
        "refactoren – refactoring",
        "ontwerppatronen – design patterns"
    ],
    "security": [
        "authenticatie – authentication",
        "autorisatie – authorization",
        "versleuteling – encryption",
        "kwetsbaarheid – vulnerability",
        "beveiligingslek – security flaw",
        "SQL-injectie – SQL injection",
        "cross-site scripting – cross-site scripting",
        "veilige gegevensopslag – secure data storage"
    ],
    "soft_skills": [
        "samenwerking – collaboration",
        "communicatie – communication",
        "tijdsbeheer – time management",
        "prioriteiten stellen – prioritization",
        "feedback geven – giving feedback",
        "probleemoplossing – problem-solving",
        "zelfstandig werken – working independently",
        "stakeholder management – stakeholder management"
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
def generate_interviewer_response(
    scenario: str,
    conversation_history: List[Dict],
    user_input: str
) -> str:
    """Generate AI interviewer response in Dutch"""

    scenario_info = INTERVIEW_SCENARIOS.get(
        scenario, INTERVIEW_SCENARIOS["technical_screening"])

    system_prompt = f"""Je bent een Nederlandse tech interviewer. {scenario_info['ai_role']}

BELANGRIJK:
- Spreek ALLEEN Nederlands
- Stel technische vragen passend bij de context
- Daag de kandidaat uit met verdiepende vragen
- Wees professioneel maar vriendelijk
- Voor behavioral vragen: vraag door op details (STAR method)
- Voor technical vragen: vraag "waarom?" en "hoe zou je..." 
- Houd antwoorden kort (2-3 zinnen per vraag)

Moeilijkheidsgraad: {scenario_info['difficulty']}
Context van dit interview: {scenario_info['context']}"""

    # Build conversation context
    history_text = "\n".join([
        f"{'Kandidaat' if msg['role'] == 'user' else 'Interviewer'}: {msg['content']}"
        for msg in conversation_history[-6:]  # Last 3 exchanges
    ])

    user_prompt = f"""Eerdere gesprek:
{history_text}

Kandidaat: {user_input}

Reageer als interviewer (stel vervolgvraag of geef feedback, in Nederlands):"""

    response = try_generate(system_prompt, user_prompt, 350)
    return response if response else "Interessant. Kun je dat verder uitleggen?"


def analyze_technical_dutch(user_input: str, scenario: str) -> Dict:
    """Analyze candidate's Dutch and provide B1→B2 feedback"""

    system_prompt = """Je bent een Nederlandse taalcoach voor technisch Nederlands.
Analyseer de kandidaat's antwoord en geef feedback.

FORMAAT (gebruik EXACT deze structuur):
NIVEAU: [B1/B2/C1]
GRAMMATICA: [correctie als nodig, anders "✓ Correct"]
B2_VERBETERING: [professionelere/technischere versie]
TECH_VOCABULAIRE: [1-2 nieuwe tech woorden, formaat: "nederlands – english"]
INTERVIEW_TIP: [1 tip voor betere interview-communicatie]

Wees constructief maar kritisch waar nodig."""

    user_prompt = f"""Interview scenario: {INTERVIEW_SCENARIOS.get(scenario, {}).get('title', 'Technical interview')}

Kandidaat zegt: "{user_input}"

Geef feedback:"""

    raw = try_generate(system_prompt, user_prompt, 450)

    if not raw:
        return {
            "level": "B1",
            "grammar": "Kon niet analyseren",
            "b2_improvement": user_input,
            "vocabulary": [],
            "tip": "Gebruik meer specifieke technische terminologie."
        }

    # Parse feedback
    level_match = re.search(r"NIVEAU:\s*(\w+)", raw)
    grammar_match = re.search(
        r"GRAMMATICA:\s*(.+?)(?=\n[A-Z_]+:|$)", raw, re.DOTALL)
    b2_match = re.search(
        r"B2_VERBETERING:\s*(.+?)(?=\n[A-Z_]+:|$)", raw, re.DOTALL)
    vocab_match = re.search(
        r"TECH_VOCABULAIRE:\s*(.+?)(?=\n[A-Z_]+:|$)", raw, re.DOTALL)
    tip_match = re.search(
        r"INTERVIEW_TIP:\s*(.+?)(?=\n[A-Z_]+:|$)", raw, re.DOTALL)

    # Extract vocabulary
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
        "tip": tip_match.group(1).strip() if tip_match else "Blijf technisch blijven communiceren!"
    }


def get_scenario_vocabulary(scenario: str) -> List[str]:
    """Get relevant vocabulary for the scenario"""

    scenario_vocab_map = {
        "system_design": ["backend_core", "devops"],
        "database_design": ["database", "backend_core"],
        "code_review": ["code_quality", "backend_core"],
        "debugging_scenario": ["backend_core", "devops"],
        "behavioral_conflict": ["soft_skills"],
        "salary_negotiation": ["soft_skills"],
        "technical_screening": ["backend_core"],
        "architecture_discussion": ["backend_core", "code_quality"]
    }

    categories = scenario_vocab_map.get(scenario, ["backend_core"])
    vocab = []

    for cat in categories:
        vocab.extend(VOCABULARY_BANKS.get(cat, [])[:4])

    return vocab[:8]


def calculate_interview_score(feedback: Dict, scenario_difficulty: str) -> int:
    """Calculate interview performance score 0-100"""

    base_score = 70  # Assume competent baseline

    # Level bonus
    level_bonus = {"B1": 0, "B2": 15, "C1": 25}
    base_score += level_bonus.get(feedback["level"], 0)

    # Grammar penalty
    if "✓" not in feedback["grammar"]:
        base_score -= 10

    # Difficulty adjustment
    difficulty_multiplier = {"Easy": 1.0, "Medium": 0.95, "Hard": 0.9}
    base_score *= difficulty_multiplier.get(scenario_difficulty, 1.0)

    return min(100, max(0, int(base_score)))


# === MAIN CONVERSATION FUNCTION ===
def run_backend_interview(
    scenario: str,
    user_input: str,
    conversation_history: List[Dict] = None
) -> Dict:
    """
    Main function to handle backend interview conversation

    Args:
        scenario: One of INTERVIEW_SCENARIOS keys
        user_input: Candidate's answer in Dutch
        conversation_history: Previous messages

    Returns:
        {
            "interviewer_response": "Dutch response from AI interviewer",
            "feedback": {
                "level": "B1/B2/C1",
                "grammar": "correction or ✓",
                "b2_improvement": "more professional version",
                "vocabulary": ["tech term – translation", ...],
                "tip": "interview communication tip"
            },
            "scenario_vocab": ["relevant technical vocabulary"],
            "interview_score": 0-100,
            "history": updated_conversation_history
        }
    """

    if conversation_history is None:
        conversation_history = []

    print(f"\n{'='*60}")
    print(f"IT BACKEND INTERVIEWER AI - Scenario: {scenario.upper()}")
    print(f"{'='*60}\n")

    if not user_input.strip():
        return {
            "error": "Leeg antwoord ontvangen",
            "interviewer_response": None,
            "feedback": None
        }

    # Generate interviewer response
    print("[1/4] Generating interviewer response...")
    interviewer_response = generate_interviewer_response(
        scenario, conversation_history, user_input)

    # Analyze candidate's Dutch
    print("[2/4] Analyzing your technical Dutch...")
    feedback = analyze_technical_dutch(user_input, scenario)

    # Get scenario vocabulary
    print("[3/4] Fetching technical vocabulary...")
    scenario_vocab = get_scenario_vocabulary(scenario)

    # Calculate interview score
    print("[4/4] Calculating interview performance...")
    scenario_info = INTERVIEW_SCENARIOS[scenario]
    interview_score = calculate_interview_score(
        feedback, scenario_info["difficulty"])

    # Update history
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append(
        {"role": "assistant", "content": interviewer_response})

    print("\n✓ Interview turn complete\n")

    return {
        "interviewer_response": interviewer_response,
        "feedback": feedback,
        "scenario_vocab": scenario_vocab,
        "interview_score": interview_score,
        "history": conversation_history
    }


# === CLI INTERFACE ===
def print_scenario_menu():
    print("\n" + "="*60)
    print("AVAILABLE INTERVIEW SCENARIOS".center(60))
    print("="*60 + "\n")

    for idx, (key, info) in enumerate(INTERVIEW_SCENARIOS.items(), 1):
        difficulty_emoji = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}
        emoji = difficulty_emoji.get(info['difficulty'], "⚪")
        print(f"{idx}. {info['title']} {emoji}")
        print(f"   {info['description']}")
        print(f"   Difficulty: {info['difficulty']}\n")


def format_feedback(feedback: Dict, interview_score: int):
    print("\n" + "─"*60)
    print("📊 INTERVIEW FEEDBACK".center(60))
    print("─"*60)

    # Score with color
    score_color = "🟢" if interview_score >= 80 else "🟡" if interview_score >= 65 else "🔴"
    print(f"\n{score_color} Interview Score: {interview_score}/100")
    print(f"\n🎯 Your Dutch Level: {feedback['level']}")
    print(f"\n✏️  Grammar: {feedback['grammar']}")
    print(f"\n📈 B2 Professional Version:\n   {feedback['b2_improvement']}")

    if feedback['vocabulary']:
        print(f"\n📚 Technical Vocabulary to Learn:")
        for word in feedback['vocabulary']:
            print(f"   • {word}")

    print(f"\n💡 Interview Communication Tip:\n   {feedback['tip']}")
    print("\n" + "─"*60 + "\n")


def run_interactive_session():
    """Interactive CLI for testing"""

    print("\n💼 DUTCH IT BACKEND INTERVIEWER AI - B1→B2 Technical Dutch")
    print("="*60)

    print_scenario_menu()

    choice = input("Select scenario (1-8) or 'q' to quit: ").strip()

    if choice.lower() == 'q':
        return

    try:
        scenario_idx = int(choice) - 1
        scenario_key = list(INTERVIEW_SCENARIOS.keys())[scenario_idx]
    except (ValueError, IndexError):
        print("❌ Invalid choice")
        return

    scenario_info = INTERVIEW_SCENARIOS[scenario_key]
    conversation_history = []

    print(f"\n{'='*60}")
    print(f"INTERVIEW: {scenario_info['title']}")
    print(f"{'='*60}")
    print(f"\n📋 Scenario: {scenario_info['context']}")
    print(f"🎭 Interviewer role: {scenario_info['ai_role']}")
    print(f"⚡ Difficulty: {scenario_info['difficulty']}")
    print(f"\n📝 Learning goals:")
    for goal in scenario_info['learning_goals']:
        print(f"   • {goal}")
    print("\nType 'end' to finish, 'vocab' for vocabulary, 'new' for new scenario\n")

    # Opening question from interviewer
    opening_questions = {
        "system_design": "Hoe zou je een REST API ontwerpen die 10.000 verzoeken per seconde aankan?",
        "database_design": "Waarom heb je gekozen voor PostgreSQL in plaats van MongoDB?",
        "code_review": "Ik zie dat je async/await gebruikt. Kun je uitleggen waarom?",
        "debugging_scenario": "Er is een geheugenlek in productie. Wat is je aanpak?",
        "behavioral_conflict": "Vertel eens over een situatie waar je het oneens was met een teamlid.",
        "salary_negotiation": "We kunnen je €55.000 bruto per jaar aanbieden. Wat vind je daarvan?",
        "technical_screening": "Kun je in 30 seconden uitleggen wat RESTful betekent?",
        "architecture_discussion": "Wanneer zou je microservices verkiezen boven een monoliet?"
    }

    print(
        f"\n🎙️ Interviewer: {opening_questions.get(scenario_key, 'Vertel me over jezelf.')}\n")

    turn = 1
    scores = []

    while True:
        user_input = input(f"[Turn {turn}] You (Kandidaat): ").strip()

        if user_input.lower() == 'end':
            if scores:
                avg_score = sum(scores) / len(scores)
                print(
                    f"\n✓ Interview ended. Average score: {avg_score:.0f}/100")
            print("Bedankt voor het oefenen!")
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

        result = run_backend_interview(
            scenario_key,
            user_input,
            conversation_history
        )

        if "error" in result:
            print(f"❌ Error: {result['error']}")
            continue

        print(f"\n🎙️ Interviewer: {result['interviewer_response']}")

        format_feedback(result['feedback'], result['interview_score'])
        scores.append(result['interview_score'])

        conversation_history = result['history']
        turn += 1


# === MAIN ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Quick test mode
        print("\n🧪 QUICK TEST MODE\n")

        test_input = "Ik heb 5 jaar ervaring met Python en Django. Ik kan REST APIs bouwen."

        result = run_backend_interview(
            "technical_screening",
            test_input,
            []
        )

        print(f"You: {test_input}")
        print(f"\nInterviewer: {result['interviewer_response']}")
        format_feedback(result['feedback'], result['interview_score'])

        print("\n📚 Scenario Vocabulary:")
        for vocab in result['scenario_vocab']:
            print(f"   • {vocab}")
    else:
        # Interactive mode
        run_interactive_session()
