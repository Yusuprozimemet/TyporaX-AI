"""
Real-time Assessment System for GeneLingua Expert Conversations
Provides dynamic feedback, hints, and assessments during expert chats
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import httpx
from src.utils.utils import get_logger
from src.utils.prompt_manager import get_prompt

logger = get_logger(__name__)


class RealTimeAssessment:
    """Real-time assessment engine for expert conversations"""

    def __init__(self, hf_token: str, api_url: str, default_model: str = "google/gemma-2-9b-it", fallback_model: str = "deepseek-ai/DeepSeek-R1:together"):
        self.hf_token = hf_token
        self.api_url = api_url
        self.default_model = default_model
        self.fallback_model = fallback_model
        self.conversation_context = {}

    async def analyze_conversation(self, user_id: str, expert: str,
                                   conversation_history: List[Dict],
                                   current_message: str) -> Dict:
        """
        Analyze ongoing conversation and provide real-time assessment
        """
        try:
            # Analyze different aspects of the conversation
            language_analysis = await self._analyze_language_quality(current_message)
            conversation_flow = self._analyze_conversation_flow(
                conversation_history)
            expert_specific = await self._get_expert_specific_assessment(
                expert, conversation_history, current_message
            )
            learning_progress = self._assess_learning_progress(
                user_id, conversation_history)

            # Generate real-time hints and suggestions
            hints = await self._generate_hints(expert, current_message, conversation_history)

            assessment = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "expert": expert,
                "language_analysis": language_analysis,
                "conversation_flow": conversation_flow,
                "expert_specific": expert_specific,
                "learning_progress": learning_progress,
                "hints": hints,
                "overall_score": self._calculate_overall_score(
                    language_analysis, conversation_flow, expert_specific
                )
            }

            return assessment

        except Exception as e:
            logger.error(f"Assessment analysis failed: {e}")
            return self._get_fallback_assessment(expert)

    async def _analyze_language_quality(self, message: str) -> Dict:
        """Analyze Dutch language quality of user message"""
        try:
            # Get language analysis prompt from configuration
            prompt = get_prompt('assessment', 'language_analysis', {
                                'message': message})

            # Try default model first
            payload = {
                "model": self.default_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600,
                "temperature": 0.2
            }

            headers = {"Authorization": f"Bearer {self.hf_token}"}

            # Try default model first, then fallback
            for model in [self.default_model, self.fallback_model]:
                try:
                    payload["model"] = model
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        response = await client.post(self.api_url, json=payload, headers=headers)
                        response.raise_for_status()

                        result = response.json()
                        content = result["choices"][0]["message"]["content"]

                        # Try to parse JSON from response
                        json_match = re.search(
                            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                        if json_match:
                            parsed_result = json.loads(json_match.group())
                            logger.info(
                                f"Assessment analysis successful with {model}")
                            return parsed_result

                        # If no JSON found, try simple parsing
                        return self._parse_language_analysis_fallback(content)

                except Exception as e:
                    logger.warning(f"Model {model} failed: {e}")
                    continue

            # If all models fail, return fallback
            return self._get_smart_fallback_analysis(message)

        except Exception as e:
            logger.error(f"Language analysis failed: {e}")
            return {
                "grammar_score": 5,
                "vocabulary_level": "intermediate",
                "fluency_score": 5,
                "errors": [],
                "corrections": [],
                "improved_version": message,
                "explanation": "Geen specifieke verbeteringen beschikbaar",
                "strengths": ["Je probeert Nederlands te spreken!"]
            }

    def _analyze_conversation_flow(self, conversation_history: List[Dict]) -> Dict:
        """Analyze conversation flow and engagement"""
        if len(conversation_history) < 2:
            return {
                "engagement_level": "starting",
                "turn_count": len(conversation_history) // 2,
                "avg_message_length": 0,
                "topic_consistency": "new_conversation"
            }

        user_messages = [
            msg for msg in conversation_history if msg.get("role") == "user"]

        avg_length = sum(len(msg.get("content", ""))
                         for msg in user_messages) / len(user_messages) if user_messages else 0
        turn_count = len(user_messages)

        engagement_level = "high" if turn_count > 5 and avg_length > 50 else "medium" if turn_count > 2 else "low"

        return {
            "engagement_level": engagement_level,
            "turn_count": turn_count,
            "avg_message_length": avg_length,
            "topic_consistency": "consistent" if turn_count > 3 else "developing"
        }

    async def _get_expert_specific_assessment(self, expert: str,
                                              conversation_history: List[Dict],
                                              current_message: str) -> Dict:
        """Get expert-specific assessment based on domain"""
        assessments = {
            "healthcare": await self._assess_healthcare_conversation(conversation_history, current_message),
            "interview": await self._assess_interview_conversation(conversation_history, current_message),
            "language": await self._assess_language_conversation(conversation_history, current_message)
        }

        return assessments.get(expert, assessments["language"])

    async def _assess_healthcare_conversation(self, conversation_history: List[Dict],
                                              current_message: str) -> Dict:
        """Assess healthcare-specific Dutch conversation"""
        medical_terms = self._count_medical_vocabulary(current_message)
        professional_tone = self._assess_professional_tone(current_message)

        return {
            "domain": "healthcare",
            "medical_vocabulary_used": medical_terms,
            "professional_tone_score": professional_tone,
            "scenario_relevance": "high" if medical_terms > 0 else "medium",
            "specific_skills": [
                "Medische terminologie" if medical_terms > 0 else "Basis communicatie",
                "Patiënt-professional interactie",
                "Nederlandse zorgcultuur"
            ]
        }

    async def _assess_interview_conversation(self, conversation_history: List[Dict],
                                             current_message: str) -> Dict:
        """Assess IT interview-specific Dutch conversation"""
        technical_terms = self._count_technical_vocabulary(current_message)
        confidence_level = self._assess_confidence_level(current_message)

        return {
            "domain": "interview",
            "technical_vocabulary_used": technical_terms,
            "confidence_level": confidence_level,
            "interview_readiness": "high" if technical_terms > 0 and confidence_level > 6 else "medium",
            "specific_skills": [
                "Technische Nederlandse begrippen" if technical_terms > 0 else "Basis Nederlands",
                "Professionele presentatie",
                "Nederlandse werkplaatscommunicatie"
            ]
        }

    async def _assess_language_conversation(self, conversation_history: List[Dict],
                                            current_message: str) -> Dict:
        """Assess general language learning conversation"""
        return {
            "domain": "language",
            "learning_focus": "algemene Nederlandse taalvaardigheden",
            "practice_type": "conversatie oefening",
            "skill_development": [
                "Woordenschat uitbreiding",
                "Grammatica toepassing",
                "Vloeende conversatie"
            ]
        }

    async def _generate_hints(self, expert: str, current_message: str,
                              conversation_history: List[Dict]) -> Dict:
        """Generate contextual hints and suggestions"""
        try:
            context = " ".join([msg.get("content", "")
                               for msg in conversation_history[-4:]])

            prompt = get_prompt('assessment', 'hints_generation', {
                'expert': expert,
                'context': context,
                'current_message': current_message
            })

            payload = {
                "model": self.default_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400,
                "temperature": 0.6
            }

            headers = {"Authorization": f"Bearer {self.hf_token}"}

            # Try models with fallback
            for model in [self.default_model, self.fallback_model]:
                try:
                    payload["model"] = model
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        response = await client.post(self.api_url, json=payload, headers=headers)
                        response.raise_for_status()

                        result = response.json()
                        content = result["choices"][0]["message"]["content"]
                        break
                except Exception as e:
                    logger.warning(f"Hint generation with {model} failed: {e}")
                    if model == self.fallback_model:
                        raise

                return {
                    "language_tips": self._extract_tips(content, "taal"),
                    "conversation_tips": self._extract_tips(content, "conversatie"),
                    "expert_tips": self._extract_tips(content, expert),
                    "quick_suggestions": [
                        "Probeer meer Nederlandse woorden",
                        "Stel follow-up vragen",
                        "Gebruik formele begroetingen"
                    ]
                }

        except Exception as e:
            logger.error(f"Hint generation failed: {e}")
            return self._get_fallback_hints(expert)

    def _assess_learning_progress(self, user_id: str, conversation_history: List[Dict]) -> Dict:
        """Assess user's learning progress over time"""
        try:
            # Load historical data
            user_dir = f"data/users/{user_id}"
            progress_file = f"{user_dir}/conversation_progress.json"

            if os.path.exists(progress_file):
                with open(progress_file, "r", encoding="utf-8") as f:
                    historical_data = json.load(f)
            else:
                historical_data = {
                    "sessions": [], "total_messages": 0, "improvement_trend": "stable"}

            current_session_length = len(
                [msg for msg in conversation_history if msg.get("role") == "user"])

            return {
                "session_messages": current_session_length,
                "total_historical_messages": historical_data.get("total_messages", 0),
                "improvement_trend": historical_data.get("improvement_trend", "stable"),
                "learning_momentum": "high" if current_session_length > 5 else "medium" if current_session_length > 2 else "starting"
            }

        except Exception as e:
            logger.error(f"Progress assessment failed: {e}")
            return {
                "session_messages": 0,
                "total_historical_messages": 0,
                "improvement_trend": "stable",
                "learning_momentum": "starting"
            }

    def _calculate_overall_score(self, language_analysis: Dict,
                                 conversation_flow: Dict, expert_specific: Dict) -> Dict:
        """Calculate overall performance score"""
        grammar_score = language_analysis.get("grammar_score", 5)
        fluency_score = language_analysis.get("fluency_score", 5)
        engagement_bonus = 2 if conversation_flow.get(
            "engagement_level") == "high" else 1

        overall = (grammar_score + fluency_score + engagement_bonus) / 3

        return {
            "overall_score": round(overall, 1),
            "performance_level": "excellent" if overall >= 8 else "good" if overall >= 6 else "developing",
            "key_strengths": language_analysis.get("strengths", []),
            "focus_areas": language_analysis.get("errors", [])
        }

    # Helper methods
    def _count_medical_vocabulary(self, text: str) -> int:
        medical_terms = ["patiënt", "dokter", "ziekenhuis", "medicijn", "behandeling",
                         "symptoom", "diagnose", "therapie", "verpleegkundige", "apotheek"]
        return sum(1 for term in medical_terms if term.lower() in text.lower())

    def _count_technical_vocabulary(self, text: str) -> int:
        tech_terms = ["programmeren", "database", "software", "ontwikkeling", "code",
                      "systeem", "applicatie", "server", "netwerk", "algoritme"]
        return sum(1 for term in tech_terms if term.lower() in text.lower())

    def _assess_professional_tone(self, text: str) -> int:
        formal_indicators = ["u", "zou", "kunt",
                             "dank je wel", "met vriendelijke groet"]
        score = sum(
            2 for indicator in formal_indicators if indicator in text.lower())
        return min(10, max(1, score))

    def _assess_confidence_level(self, text: str) -> int:
        confidence_indicators = ["ik denk", "misschien",
                                 "waarschijnlijk", "zeker", "absoluut"]
        uncertainty = ["eh", "uhm", "weet niet", "misschien"]

        confidence_score = sum(
            1 for indicator in confidence_indicators if indicator in text.lower())
        uncertainty_penalty = sum(
            1 for indicator in uncertainty if indicator in text.lower())

        return max(1, min(10, 5 + confidence_score - uncertainty_penalty))

    def _extract_tips(self, content: str, category: str) -> List[str]:
        """Extract tips from AI response"""
        lines = content.split('\n')
        tips = []
        for line in lines:
            if category.lower() in line.lower() and ('tip' in line.lower() or '-' in line or '•' in line):
                clean_tip = re.sub(r'^[-•\d.\s]+', '', line).strip()
                if clean_tip and len(clean_tip) > 10:
                    tips.append(clean_tip)

        return tips[:3] if tips else [f"Blijf oefenen met {category}!"]

    def _get_smart_fallback_analysis(self, message: str) -> Dict:
        """Smart fallback analysis based on message characteristics"""
        message_length = len(message.split())
        has_complex_words = any(len(word) > 6 for word in message.split())
        has_questions = '?' in message
        has_conjunctions = any(word in message.lower() for word in [
                               'omdat', 'terwijl', 'hoewel', 'voordat', 'nadat'])

        # Base scores on message complexity
        grammar_score = 5
        fluency_score = 4
        vocab_level = "beginner"

        if message_length > 10:
            grammar_score += 2
            fluency_score += 2
            vocab_level = "intermediate"

        if has_complex_words:
            grammar_score += 1
            fluency_score += 1

        if has_conjunctions:
            grammar_score += 2
            fluency_score += 2
            vocab_level = "advanced" if vocab_level == "intermediate" else "intermediate"

        # Simple improvements for common patterns
        improved_message = message
        corrections = []
        errors = []

        # Basic grammar improvements
        if message.lower().startswith('ik ben'):
            if 'ziek' in message.lower():
                improved_message = "Ik voel me niet lekker" if message.lower(
                ) == 'ik ben ziek' else message
                if improved_message != message:
                    corrections.append(
                        "'Ik voel me niet lekker' klinkt natuurlijker dan 'Ik ben ziek'")
                    errors.append("Te letterlijke vertaling")

        # Check for English words mixed in
        english_words = ['the', 'and', 'but', 'with', 'have', 'this', 'that', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some',
                         'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'over', 'such', 'take', 'than', 'them', 'well', 'were']
        found_english = [word for word in message.lower().split()
                         if word in english_words]
        if found_english:
            errors.extend(
                [f"Engels woord gebruikt: '{word}'" for word in found_english[:2]])
            corrections.extend(
                [f"Vervang '{word}' door een Nederlands woord" for word in found_english[:2]])

        return {
            "grammar_score": min(10, grammar_score),
            "vocabulary_level": vocab_level,
            "fluency_score": min(10, fluency_score),
            "errors": errors if errors else (["Meer complexe zinnen proberen"] if grammar_score < 7 else []),
            "corrections": corrections if corrections else ["Gebruik meer Nederlandse connectoren"],
            "improved_version": improved_message,
            "explanation": "Automatische basisverbetering op basis van Nederlandse taalpatronen",
            "strengths": ["Goede woordkeuze" if has_complex_words else "Duidelijke communicatie"]
        }

    def _parse_language_analysis_fallback(self, content: str) -> Dict:
        """Fallback parser for language analysis"""
        # Try to extract any useful information from the AI response
        lines = content.lower().split('\n')
        improved_version = "Geen verbeterde versie beschikbaar"
        explanation = "AI analyse niet beschikbaar, basis feedback gegeven"

        # Look for any suggestions in the response
        for line in lines:
            if 'beter' in line or 'verbetering' in line or 'correct' in line:
                improved_version = line.strip()
                break

        return {
            "grammar_score": 6,
            "vocabulary_level": "intermediate",
            "fluency_score": 6,
            "errors": ["Meer oefening nodig"],
            "corrections": ["Blijf Nederlands spreken"],
            "improved_version": improved_version,
            "explanation": explanation,
            "strengths": ["Goede poging!"]
        }

    def _get_fallback_assessment(self, expert: str) -> Dict:
        """Fallback assessment when analysis fails"""
        return {
            "timestamp": datetime.now().isoformat(),
            "expert": expert,
            "language_analysis": {
                "grammar_score": 5,
                "vocabulary_level": "intermediate",
                "fluency_score": 5,
                "errors": [],
                "corrections": [],
                "strengths": ["Je probeert Nederlands te spreken!"]
            },
            "conversation_flow": {
                "engagement_level": "medium",
                "turn_count": 1,
                "avg_message_length": 0,
                "topic_consistency": "developing"
            },
            "expert_specific": {
                "domain": expert,
                "scenario_relevance": "medium"
            },
            "learning_progress": {
                "session_messages": 1,
                "learning_momentum": "starting"
            },
            "hints": self._get_fallback_hints(expert),
            "overall_score": {
                "overall_score": 5.0,
                "performance_level": "developing",
                "key_strengths": ["Goede start!"],
                "focus_areas": ["Meer oefening"]
            }
        }

    def _get_fallback_hints(self, expert: str) -> Dict:
        """Fallback hints when generation fails"""
        expert_hints = {
            "healthcare": [
                "Gebruik medische terminologie",
                "Spreek duidelijk en professioneel",
                "Stel patiëntgerichte vragen"
            ],
            "interview": [
                "Gebruik technische Nederlandse begrippen",
                "Toon je ervaring met voorbeelden",
                "Stel goede vragen over het bedrijf"
            ],
            "language": [
                "Probeer langere zinnen te maken",
                "Gebruik verschillende werkwoorden",
                "Oefen met Nederlandse uitdrukkingen"
            ]
        }

        return {
            "language_tips": ["Oefen dagelijks Nederlands", "Lees Nederlandse teksten"],
            "conversation_tips": ["Stel open vragen", "Luister actief"],
            "expert_tips": expert_hints.get(expert, expert_hints["language"]),
            "quick_suggestions": ["Spreek langzaam en duidelijk", "Maak oogcontact", "Gebruik gebaren"]
        }

# Async function to save assessment data


async def save_assessment_data(user_id: str, assessment: Dict):
    """Save assessment data for analytics"""
    try:
        import os
        user_dir = f"data/users/{user_id}"
        os.makedirs(user_dir, exist_ok=True)

        assessments_file = f"{user_dir}/assessments.json"

        # Load existing assessments
        if os.path.exists(assessments_file):
            with open(assessments_file, "r", encoding="utf-8") as f:
                assessments = json.load(f)
        else:
            assessments = []

        # Add new assessment
        assessments.append(assessment)

        # Keep only last 50 assessments
        if len(assessments) > 50:
            assessments = assessments[-50:]

        # Save assessments
        with open(assessments_file, "w", encoding="utf-8") as f:
            json.dump(assessments, f, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Failed to save assessment data: {e}")
