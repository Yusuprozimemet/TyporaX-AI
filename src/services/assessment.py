"""
Real-time Assessment System for TyporaX-AI Expert Conversations
Provides dynamic feedback, hints, and assessments during expert chats
Integrates with AssessmentTracker for session-based progress tracking
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import httpx
from src.utils.utils import get_logger
from src.utils.prompt_manager import get_prompt
from src.services.tracker import AssessmentTracker

logger = get_logger(__name__)


class RealTimeAssessment:
    """Real-time assessment engine for expert conversations with tracker integration"""

    def __init__(self, hf_token: str, api_url: str, default_model: str = None, fallback_model: str = None):
        from config.settings import config
        self.hf_token = hf_token
        self.api_url = api_url
        self.default_model = default_model or config.DEFAULT_MODEL
        self.fallback_model = fallback_model or config.FALLBACK_MODEL
        self.conversation_context = {}
        self.trackers = {}  # Dict to store trackers per user session

    def _get_language_analysis_prompt(self, message: str, language: str = "dutch") -> str:
        """Generate language-specific analysis prompt"""
        prompts = {
            "english": f"""You are an English language expert. Analyze this English text precisely:

Text: "{message}"

Rate on:
1. Grammar (0-10): Are sentence structure, verb conjugations, tense correct?
2. Vocabulary (beginner/intermediate/advanced): Word complexity and variety
3. Fluency (0-10): Natural flow and smoothness
4. Specific errors and improvements

Answer ONLY with valid JSON:
{{
    "grammar_score": 0-10,
    "vocabulary_level": "beginner/intermediate/advanced",
    "fluency_score": 0-10,
    "errors": ["specific grammar errors or wrong words"],
    "corrections": ["correct versions of the errors"],
    "improved_version": "An improved version of the whole message with correct grammar and natural language use",
    "explanation": "Explanation of the main improvements",
    "strengths": ["strong points"]
}}""",
            "french": f"""Vous êtes un expert en français. Analysez ce texte français précisément:

Texte: "{message}"

Évaluez sur:
1. Grammaire (0-10): La structure des phrases, conjugaisons, temps sont-ils corrects?
2. Vocabulaire (débutant/intermédiaire/avancé): Complexité et variété des mots
3. Fluidité (0-10): Flux naturel et douceur
4. Erreurs spécifiques et améliorations

Répondez UNIQUEMENT avec du JSON valide:
{{
    "grammar_score": 0-10,
    "vocabulary_level": "débutant/intermédiaire/avancé",
    "fluency_score": 0-10,
    "errors": ["erreurs grammaticales spécifiques ou mauvais mots"],
    "corrections": ["versions correctes des erreurs"],
    "improved_version": "Une version améliorée du message entier avec grammaire correcte et usage naturel",
    "explanation": "Explication des améliorations principales",
    "strengths": ["points forts"]
}}""",
            "chinese": f"""你是一位中文语言专家。精确地分析这段中文文本:

文本: "{message}"

评估以下方面:
1. 语法 (0-10): 句子结构、动词变位、时态是否正确?
2. 词汇 (初学者/中级/高级): 单词的复杂性和多样性
3. 流畅度 (0-10): 自然流畅和平滑度
4. 具体错误和改进

ONLY回答有效的JSON:
{{
    "grammar_score": 0-10,
    "vocabulary_level": "初学者/中级/高级",
    "fluency_score": 0-10,
    "errors": ["具体的语法错误或错误的词"],
    "corrections": ["错误的正确版本"],
    "improved_version": "整个消息的改进版本，包含正确的语法和自然的语言使用",
    "explanation": "主要改进的解释",
    "strengths": ["优点"]
}}""",
            "dutch": f"""Je bent een Nederlandse taalexpert. Analyseer deze Nederlandse tekst precies:

Tekst: "{message}"

Beoordeel op:
1. Grammatica (0-10): Zijn zinsbouw, werkwoordsvervoegingen, naamvallen correct?
2. Woordenschat (beginner/intermediate/advanced): Complexiteit en variatie van woorden
3. Vloeendheid (0-10): Natuurlijkheid en vloeiendheid van de tekst
4. Specificke fouten en verbeteringen

Antwoord ALLEEN met geldige JSON:
{{
    "grammar_score": 0-10,
    "vocabulary_level": "beginner/intermediate/advanced",
    "fluency_score": 0-10,
    "errors": ["specifieke grammaticale fouten of verkeerde woorden"],
    "corrections": ["correcte versies van de fouten"],
    "improved_version": "Een verbeterde versie van het hele bericht met correcte grammatica en natuurlijker taalgebruik",
    "explanation": "Uitleg van de belangrijkste verbeteringen",
    "strengths": ["sterke punten"]
}}"""
        }
        return prompts.get(language.lower(), prompts["dutch"])

    def _get_hints_prompt(self, expert: str, context: str, current_message: str, language: str = "dutch") -> str:
        """Generate language-specific hints prompt"""
        prompts = {
            "english": f"""Provide short, practical tips for this English conversation:

Expert: {expert}
Context: {context}
Latest message: {current_message}

Give 3 types of tips:
1. Language improvements (grammar/vocabulary)
2. Conversation tips (flow/engagement)
3. Expert-specific tips ({expert} context)

Keep it brief and practical.""",
            "french": f"""Fournissez des conseils courts et pratiques pour cette conversation en français:

Expert: {expert}
Contexte: {context}
Dernier message: {current_message}

Donnez 3 types de conseils:
1. Améliorations linguistiques (grammaire/vocabulaire)
2. Conseils de conversation (flux/engagement)
3. Conseils spécifiques à l'expert ({expert} contexte)

Restez bref et pratique.""",
            "chinese": f"""为这次中文对话提供简短实用的建议:

专家: {expert}
背景: {context}
最新消息: {current_message}

给出3种建议:
1. 语言改进(语法/词汇)
2. 对话建议(流畅/参与)
3. 专家特定建议({expert}背景)

保持简洁和实用。""",
            "dutch": f"""Geef korte, praktische tips voor deze Nederlandse conversatie:

Expert: {expert}
Context: {context}
Laatste bericht: {current_message}

Geef 3 soorten tips:
1. Taalverbeteringen (grammar/vocabulary)
2. Conversatie tips (flow/engagement)
3. Expert-specifieke tips ({expert} context)

Houd het kort en praktisch."""
        }
        return prompts.get(language.lower(), prompts["dutch"])

    def _get_or_create_tracker(self, user_id: str, expert: str, language: str = "dutch") -> AssessmentTracker:
        """Get or create a tracker for the user session"""
        tracker_key = f"{user_id}_{expert}_{language}"
        if tracker_key not in self.trackers:
            tracker = AssessmentTracker(user_id)
            tracker.start_session(expert, language)
            self.trackers[tracker_key] = tracker
        return self.trackers[tracker_key]

    async def analyze_conversation(self, user_id: str, expert: str,
                                   conversation_history: List[Dict],
                                   current_message: str, language: str = "dutch") -> Dict:
        """
        Analyze ongoing conversation and provide real-time assessment
        Integrates with tracker for session-based progress tracking
        """
        try:
            # Analyze different aspects of the conversation
            language_analysis = await self._analyze_language_quality(current_message, language)
            conversation_flow = self._analyze_conversation_flow(
                conversation_history)
            expert_specific = await self._get_expert_specific_assessment(
                expert, conversation_history, current_message, language
            )
            learning_progress = self._assess_learning_progress(
                user_id, conversation_history)

            # Generate real-time hints and suggestions
            hints = await self._generate_hints(expert, current_message, conversation_history, language)

            assessment = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "expert": expert,
                "language": language,
                "language_analysis": language_analysis,
                "conversation_flow": conversation_flow,
                "expert_specific": expert_specific,
                "learning_progress": learning_progress,
                "hints": hints,
                "overall_score": self._calculate_overall_score(
                    language_analysis, conversation_flow, expert_specific
                )
            }

            # Track assessment in session (following tracker.py pattern)
            try:
                tracker = self._get_or_create_tracker(
                    user_id, expert, language)
                tracker.add_assessment_to_session(assessment)
            except Exception as track_err:
                logger.warning(f"Failed to track assessment: {track_err}")
                # Continue anyway - tracking shouldn't break the assessment

            return assessment

        except Exception as e:
            logger.error(f"Assessment analysis failed: {e}")
            return self._get_fallback_assessment(expert, language)

    def end_session(self, user_id: str, expert: str, language: str = "dutch") -> Dict:
        """End the current session and return session summary (following tracker pattern)"""
        tracker_key = f"{user_id}_{expert}_{language}"
        if tracker_key not in self.trackers:
            return {"error": "No active session"}

        tracker = self.trackers[tracker_key]
        try:
            session_summary = tracker.end_session()
            logger.info(
                f"Session ended for user {user_id}, expert {expert}: {session_summary.get('total_turns', 0)} turns")
            # Clean up tracker
            del self.trackers[tracker_key]
            return session_summary
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            return {"error": str(e)}

    def get_user_progress(self, user_id: str) -> Dict:
        """Get comprehensive user progress summary (following tracker pattern)"""
        try:
            tracker = AssessmentTracker(user_id)
            progress = tracker.get_progress_summary()
            return progress
        except Exception as e:
            logger.error(f"Failed to get progress: {e}")
            return {"error": str(e)}

    async def _analyze_language_quality(self, message: str, language: str = "dutch") -> Dict:
        """Analyze language quality of user message in the specified language"""
        try:
            # Create language-specific prompt
            prompt = self._get_language_analysis_prompt(message, language)

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
                    async with httpx.AsyncClient(timeout=40.0) as client:
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
            # Fallback messages by language
            fallback_msgs = {
                "english": "No specific improvements available",
                "french": "Aucune amélioration spécifique disponible",
                "chinese": "没有具体的改进建议",
                "dutch": "Geen specifieke verbeteringen beschikbaar"
            }
            return {
                "grammar_score": 5,
                "vocabulary_level": "intermediate",
                "fluency_score": 5,
                "errors": [],
                "corrections": [],
                "improved_version": message,
                "explanation": fallback_msgs.get(language.lower(), fallback_msgs["dutch"]),
                "strengths": ["You're making an effort to communicate!"] if language.lower() == "english" else ["Vous faites un effort pour communiquer!"] if language.lower() == "french" else ["你在努力交流!"] if language.lower() == "chinese" else ["Je probeert Nederlands te spreken!"]
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
                                              current_message: str, language: str = "dutch") -> Dict:
        """Get expert-specific assessment based on domain"""
        assessments = {
            "healthcare": await self._assess_healthcare_conversation(conversation_history, current_message, language),
            "interview": await self._assess_interview_conversation(conversation_history, current_message, language),
            "language": await self._assess_language_conversation(conversation_history, current_message, language)
        }

        return assessments.get(expert, assessments["language"])

    async def _assess_healthcare_conversation(self, conversation_history: List[Dict],
                                              current_message: str, language: str = "dutch") -> Dict:
        """Assess healthcare-specific conversation"""
        medical_terms = self._count_medical_vocabulary(current_message)
        professional_tone = self._assess_professional_tone(current_message)

        # Language-specific skill descriptions
        lang_skills = {
            "english": [
                "Medical terminology" if medical_terms > 0 else "Basic communication",
                "Patient-professional interaction",
                "Healthcare communication"
            ],
            "french": [
                "Terminologie médicale" if medical_terms > 0 else "Communication de base",
                "Interaction patient-professionnel",
                "Communication en santé"
            ],
            "chinese": [
                "医学术语" if medical_terms > 0 else "基本沟通",
                "患者-专业人士互动",
                "医疗保健沟通"
            ],
            "dutch": [
                "Medische terminologie" if medical_terms > 0 else "Basis communicatie",
                "Patiënt-professional interactie",
                "Nederlandse zorgcultuur"
            ]
        }

        return {
            "domain": "healthcare",
            "medical_vocabulary_used": medical_terms,
            "professional_tone_score": professional_tone,
            "scenario_relevance": "high" if medical_terms > 0 else "medium",
            "specific_skills": lang_skills.get(language.lower(), lang_skills["dutch"])
        }

    async def _assess_interview_conversation(self, conversation_history: List[Dict],
                                             current_message: str, language: str = "dutch") -> Dict:
        """Assess IT interview-specific conversation"""
        technical_terms = self._count_technical_vocabulary(current_message)
        confidence_level = self._assess_confidence_level(current_message)

        # Language-specific skill descriptions
        lang_skills = {
            "english": [
                "Technical English terms" if technical_terms > 0 else "Basic English",
                "Professional presentation",
                "Workplace communication"
            ],
            "french": [
                "Termes techniques en français" if technical_terms > 0 else "Français de base",
                "Présentation professionnelle",
                "Communication en milieu de travail"
            ],
            "chinese": [
                "技术中文术语" if technical_terms > 0 else "基础中文",
                "专业演讲",
                "工作场所沟通"
            ],
            "dutch": [
                "Technische Nederlandse begrippen" if technical_terms > 0 else "Basis Nederlands",
                "Professionele presentatie",
                "Nederlandse werkplaatscommunicatie"
            ]
        }

        return {
            "domain": "interview",
            "technical_vocabulary_used": technical_terms,
            "confidence_level": confidence_level,
            "interview_readiness": "high" if technical_terms > 0 and confidence_level > 6 else "medium",
            "specific_skills": lang_skills.get(language.lower(), lang_skills["dutch"])
        }

    async def _assess_language_conversation(self, conversation_history: List[Dict],
                                            current_message: str, language: str = "dutch") -> Dict:
        """Assess general language learning conversation"""
        # Language-specific learning focus
        lang_focus = {
            "english": {
                "learning_focus": "General English language skills",
                "practice_type": "Conversation practice",
                "skill_development": [
                    "Vocabulary expansion",
                    "Grammar application",
                    "Fluent conversation"
                ]
            },
            "french": {
                "learning_focus": "Compétences générales en français",
                "practice_type": "Pratique de conversation",
                "skill_development": [
                    "Expansion du vocabulaire",
                    "Application de la grammaire",
                    "Conversation fluide"
                ]
            },
            "chinese": {
                "learning_focus": "一般中文语言技能",
                "practice_type": "会话练习",
                "skill_development": [
                    "词汇扩展",
                    "语法应用",
                    "流利对话"
                ]
            },
            "dutch": {
                "learning_focus": "algemene Nederlandse taalvaardigheden",
                "practice_type": "conversatie oefening",
                "skill_development": [
                    "Woordenschat uitbreiding",
                    "Grammatica toepassing",
                    "Vloeende conversatie"
                ]
            }
        }

        return {
            "domain": "language",
            **lang_focus.get(language.lower(), lang_focus["dutch"])
        }

    async def _generate_hints(self, expert: str, current_message: str,
                              conversation_history: List[Dict], language: str = "dutch") -> Dict:
        """Generate contextual hints and suggestions in the specified language"""
        try:
            context = " ".join([msg.get("content", "")
                               for msg in conversation_history[-4:]])

            prompt = self._get_hints_prompt(
                expert, context, current_message, language)

            payload = {
                "model": self.default_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600,
                "temperature": 0.6
            }

            headers = {"Authorization": f"Bearer {self.hf_token}"}

            # Try models with fallback
            content = None
            for model in [self.default_model, self.fallback_model]:
                try:
                    payload["model"] = model
                    async with httpx.AsyncClient(timeout=40.0) as client:
                        response = await client.post(self.api_url, json=payload, headers=headers)
                        response.raise_for_status()

                        result = response.json()
                        content = result["choices"][0]["message"]["content"]
                        break  # Success, exit loop
                except Exception as e:
                    logger.warning(f"Hint generation with {model} failed: {e}")
                    if model == self.fallback_model:
                        # Both models failed, will use fallback hints
                        return self._get_fallback_hints(expert)
                    continue

            # Parse successful response
            if content:
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
            else:
                return self._get_fallback_hints(expert)

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
                try:
                    with open(progress_file, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        historical_data = json.loads(content) if content else {
                            "sessions": [], "total_messages": 0, "improvement_trend": "stable"}
                except (json.JSONDecodeError, IOError):
                    historical_data = {
                        "sessions": [], "total_messages": 0, "improvement_trend": "stable"}
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

    def _get_fallback_assessment(self, expert: str, language: str = "dutch") -> Dict:
        """Fallback assessment when analysis fails"""
        # Language-specific fallback messages
        lang_messages = {
            "english": {
                "strength": "You're making an effort!",
                "focus": "Keep practicing"
            },
            "french": {
                "strength": "Vous faites un effort!",
                "focus": "Continuez à pratiquer"
            },
            "chinese": {
                "strength": "你在努力!",
                "focus": "继续练习"
            },
            "dutch": {
                "strength": "Je probeert Nederlands te spreken!",
                "focus": "Meer oefening"
            }
        }

        msg = lang_messages.get(language.lower(), lang_messages["dutch"])

        return {
            "timestamp": datetime.now().isoformat(),
            "expert": expert,
            "language": language,
            "language_analysis": {
                "grammar_score": 5,
                "vocabulary_level": "intermediate",
                "fluency_score": 5,
                "errors": [],
                "corrections": [],
                "strengths": [msg["strength"]]
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
            "hints": self._get_fallback_hints(expert, language),
            "overall_score": {
                "overall_score": 5.0,
                "performance_level": "developing",
                "key_strengths": ["Good start!"] if language.lower() != "dutch" else ["Goede start!"],
                "focus_areas": [msg["focus"]]
            }
        }

    def _get_fallback_hints(self, expert: str, language: str = "dutch") -> Dict:
        """Fallback hints when generation fails"""
        # Language-specific expert hints
        expert_hints = {
            "english": {
                "healthcare": [
                    "Use medical terminology",
                    "Speak clearly and professionally",
                    "Ask patient-focused questions"
                ],
                "interview": [
                    "Use technical English terms",
                    "Show your experience with examples",
                    "Ask good questions about the company"
                ],
                "language": [
                    "Try to make longer sentences",
                    "Use different verbs",
                    "Practice with English expressions"
                ]
            },
            "french": {
                "healthcare": [
                    "Utilisez la terminologie médicale",
                    "Parlez clairement et professionnellement",
                    "Posez des questions centrées sur le patient"
                ],
                "interview": [
                    "Utilisez les termes français techniques",
                    "Montrez votre expérience avec des exemples",
                    "Posez de bonnes questions sur l'entreprise"
                ],
                "language": [
                    "Essayez de faire des phrases plus longues",
                    "Utilisez différents verbes",
                    "Pratiquez les expressions françaises"
                ]
            },
            "chinese": {
                "healthcare": [
                    "使用医学术语",
                    "清晰专业地说话",
                    "提出以患者为中心的问题"
                ],
                "interview": [
                    "使用技术中文术语",
                    "通过例子展示你的经验",
                    "问关于公司的好问题"
                ],
                "language": [
                    "尝试制作更长的句子",
                    "使用不同的动词",
                    "练习中文表达"
                ]
            },
            "dutch": {
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
        }

        # Language-specific general tips
        lang_tips = {
            "english": {
                "language": ["Practice daily English", "Read English texts"],
                "conversation": ["Ask open questions", "Listen actively"],
                "quick": ["Speak slowly and clearly", "Make eye contact", "Use gestures"]
            },
            "french": {
                "language": ["Pratiquez le français quotidiennement", "Lisez des textes français"],
                "conversation": ["Posez des questions ouvertes", "Écoutez activement"],
                "quick": ["Parlez lentement et clairement", "Faites contact visuel", "Utilisez les gestes"]
            },
            "chinese": {
                "language": ["每天练习中文", "阅读中文文本"],
                "conversation": ["提问开放式问题", "积极倾听"],
                "quick": ["清晰缓慢地说话", "眼神接触", "使用手势"]
            },
            "dutch": {
                "language": ["Oefen dagelijks Nederlands", "Lees Nederlandse teksten"],
                "conversation": ["Stel open vragen", "Luister actief"],
                "quick": ["Spreek langzaam en duidelijk", "Maak oogcontact", "Gebruik gebaren"]
            }
        }

        expert_hints_lang = expert_hints.get(
            language.lower(), expert_hints["dutch"])
        tips_lang = lang_tips.get(language.lower(), lang_tips["dutch"])

        return {
            "language_tips": tips_lang["language"],
            "conversation_tips": tips_lang["conversation"],
            "expert_tips": expert_hints_lang.get(expert, expert_hints_lang.get("language", expert_hints_lang.get("language_conversation", []))),
            "quick_suggestions": tips_lang["quick"]
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
            try:
                with open(assessments_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    assessments = json.loads(content) if content else []
            except (json.JSONDecodeError, IOError):
                assessments = []
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
