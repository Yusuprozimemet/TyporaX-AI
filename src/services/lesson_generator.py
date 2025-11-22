"""
Lesson Generator - Creates personalized Duolingo-style lessons based on assessment data
"""

import json
import random
import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# === CONFIG ===
from config.settings import config
from src.utils.lesson_logger import LessonLogger

DEFAULT_MODEL = config.DEFAULT_MODEL
FALLBACK_MODEL = config.FALLBACK_MODEL
HF_API_URL = config.HF_API_URL
HF_TOKEN = config.HF_TOKEN or ""

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LessonGenerator:
    """Generates adaptive lessons based on user assessments"""

    def __init__(self):
        self.api_url = HF_API_URL
        self.api_key = HF_TOKEN
        self.model = DEFAULT_MODEL
        self.fallback_model = FALLBACK_MODEL

        # Exercise type weights based on error types
        self.exercise_weights = {
            "grammar": ["fill_blank", "word_order"],
            "vocabulary": ["matching", "typing"],
            "fluency": ["pronunciation", "typing", "word_order"],
            "general": ["typing", "fill_blank", "matching"]
        }

    def analyze_assessments(self, assessments: List[Dict]) -> Dict[str, Any]:
        """Analyze assessment data to identify learning needs"""

        if not assessments:
            logger.info("No assessments found - using default analysis")
            return {
                "error_patterns": [],
                "focus_areas": [],
                "vocabulary_gaps": [],
                "grammar_issues": [],
                "difficulty_level": "beginner"
            }

        logger.info(f"Analyzing {len(assessments)} assessment(s)")

        # Collect all errors and focus areas
        all_errors = []
        all_focus_areas = []
        grammar_scores = []
        vocab_levels = []
        all_specific_skills = []
        all_corrections = []
        all_improvements = []

        for idx, assessment in enumerate(assessments):
            logger.debug(
                f"Assessment {idx+1}: {json.dumps(assessment, indent=2)[:500]}...")

            lang_analysis = assessment.get("language_analysis", {})
            expert_specific = assessment.get("expert_specific", {})
            overall = assessment.get("overall_score", {})
            conversation_flow = assessment.get("conversation_flow", {})
            learning_progress = assessment.get("learning_progress", {})

            # Collect errors from language_analysis
            errors = lang_analysis.get("errors", [])
            all_errors.extend(errors)
            logger.debug(f"  - Errors found: {errors}")

            # Collect corrections (if available)
            corrections = lang_analysis.get("corrections", [])
            all_corrections.extend(corrections)

            # Collect improvements (if available)
            improvements = lang_analysis.get("improved_version", "")
            if improvements:
                all_improvements.append(improvements)

            # Collect focus areas from multiple sources
            # 1. From overall_score (if exists)
            focus_areas = overall.get("focus_areas", [])
            all_focus_areas.extend(focus_areas)

            # 2. From expert_specific.specific_skills (domain-specific learning areas)
            specific_skills = expert_specific.get("specific_skills", [])
            all_specific_skills.extend(specific_skills)
            all_focus_areas.extend(specific_skills)
            logger.debug(f"  - Domain-specific skills: {specific_skills}")

            # 3. From conversation_flow (engagement and interaction skills)
            engagement_level = conversation_flow.get("engagement_level", "")
            if engagement_level and engagement_level != "high":
                all_focus_areas.append(f"engagement: {engagement_level}")

            # 4. From learning_progress (learning momentum)
            learning_momentum = learning_progress.get("learning_momentum", "")
            if learning_momentum and learning_momentum != "accelerating":
                all_focus_areas.append(
                    f"learning_momentum: {learning_momentum}")

            # Collect scores
            grammar_score = lang_analysis.get("grammar_score", 0)
            grammar_scores.append(grammar_score)
            vocab_level = lang_analysis.get("vocabulary_level", "beginner")
            vocab_levels.append(vocab_level)
            logger.debug(
                f"  - Grammar score: {grammar_score}/10, Vocab level: {vocab_level}")

        # Determine difficulty level
        avg_grammar = sum(grammar_scores) / \
            len(grammar_scores) if grammar_scores else 0
        if avg_grammar >= 8:
            difficulty = "advanced"
        elif avg_grammar >= 5:
            difficulty = "intermediate"
        else:
            difficulty = "beginner"

        analysis_result = {
            # Top 10 errors, or improvements if no errors
            "error_patterns": all_errors[:10] if all_errors else all_improvements[:5],
            # Top 5 unique focus areas (include specific skills and flow issues)
            "focus_areas": list(set([f for f in all_focus_areas if f]))[:5] or all_specific_skills[:3],
            "grammar_issues": [e for e in all_errors if "grammar" in e.lower() or "zinsbouw" in e.lower()],
            # Use corrections as vocabulary guidance
            "vocabulary_gaps": all_corrections[:3] if all_corrections else [],
            "difficulty_level": difficulty,
            "avg_grammar_score": avg_grammar,
            "expert_domain": assessments[0].get("expert", "general") if assessments else "general",
            "raw_assessment_data": {
                "specific_skills": all_specific_skills,
                "corrections": all_corrections,
                "engagement_level": assessments[-1].get("conversation_flow", {}).get("engagement_level", "medium") if assessments else "medium"
            }
        }

        logger.info(f"""
✓ ASSESSMENT ANALYSIS SUMMARY:
  - Difficulty Level: {difficulty}
  - Average Grammar Score: {avg_grammar:.1f}/10
  - Error Patterns ({len(all_errors)}): {all_errors[:5] if all_errors else 'None - user performs well'}
  - Focus Areas: {analysis_result['focus_areas']}
  - Grammar Issues: {analysis_result['grammar_issues']}
  - Vocabulary Gaps: {analysis_result['vocabulary_gaps']}
  - Domain-specific skills: {all_specific_skills}
  - Expert domain: {analysis_result['expert_domain']}
""")

        return analysis_result

    def generate_lesson_plan(
        self,
        user_id: str,
        language: str,
        expert: str,
        assessments: List[Dict]
    ) -> Dict[str, Any]:
        """Generate a complete lesson plan with multiple exercises"""

        logger.info(f"\n{'='*80}")
        logger.info(f"GENERATING LESSON PLAN")
        logger.info(f"  User ID: {user_id}")
        logger.info(f"  Language: {language}")
        logger.info(f"  Expert Domain: {expert}")
        logger.info(f"  Assessments Count: {len(assessments)}")
        logger.info(f"{'='*80}\n")

        analysis = self.analyze_assessments(assessments)

        # Build AI prompt for lesson generation
        prompt = self._build_lesson_prompt(language, expert, analysis)

        logger.debug(f"Generated prompt:\n{prompt}\n")

        try:
            # Call Groq API to generate lesson content
            logger.info("Calling AI model for lesson generation...")
            lesson_content = self._call_groq_api(prompt)

            logger.debug(
                f"AI Response (first 500 chars):\n{lesson_content[:500]}\n")

            # Parse the lesson content
            lesson_data = self._parse_lesson_content(
                lesson_content, language, expert)

            # Add metadata
            lesson_data["metadata"] = {
                "user_id": user_id,
                "language": language,
                "expert": expert,
                "difficulty": analysis["difficulty_level"],
                "generated_at": datetime.now().isoformat(),
                "focus_areas": analysis["focus_areas"][:3],
                "assessment_count": len(assessments),
                "error_patterns_used": analysis["error_patterns"][:3],
                "grammar_issues_addressed": analysis["grammar_issues"][:3],
                "vocabulary_gaps_addressed": analysis["vocabulary_gaps"][:3]
            }

            logger.info(f"""
✓ LESSON GENERATED SUCCESSFULLY:
  - Title: {lesson_data.get('lesson_title', 'N/A')}
  - Exercises: {len(lesson_data.get('exercises', []))}
  - Difficulty: {analysis['difficulty_level']}
  - Assessment-based Focus Areas: {analysis['focus_areas'][:3]}
  - Grammar Issues Addressed: {analysis['grammar_issues'][:3]}
  - Vocabulary Gaps: {analysis['vocabulary_gaps'][:3]}
""")

            # Log generation details for audit trail
            log_file = LessonLogger.log_generation(
                user_id, analysis, prompt, lesson_content, lesson_data)
            logger.info(f"✓ Generation logs saved to: {log_file}\n")

            return lesson_data

        except Exception as e:
            logger.error(f"Error generating lesson: {e}", exc_info=True)
            logger.warning("Falling back to default lesson structure")
            return self._generate_fallback_lesson(language, expert, analysis)

    def _call_groq_api(self, prompt: str, use_fallback: bool = False) -> str:
        """Call Groq API for lesson generation"""

        model = self.fallback_model if use_fallback else self.model
        logger.info(f"Calling API with model: {model}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert language learning curriculum designer. Generate structured, pedagogically sound lessons in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 3000,
            "top_p": 0.9
        }

        try:
            logger.debug(f"Sending request to {self.api_url}...")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            logger.info(
                f"✓ API call successful ({len(content)} characters received)")
            return content

        except Exception as e:
            logger.error(f"Error calling Groq API with {model}: {e}")
            if not use_fallback:
                logger.info(
                    f"Retrying with fallback model: {self.fallback_model}")
                return self._call_groq_api(prompt, use_fallback=True)
            raise

    def _build_lesson_prompt(self, language: str, expert: str, analysis: Dict) -> str:
        """Build prompt for AI to generate lesson content based on assessment data"""

        # Extract assessment data
        expert_domain = analysis.get("expert_domain", expert)
        raw_data = analysis.get("raw_assessment_data", {})
        specific_skills = raw_data.get("specific_skills", [])
        corrections = raw_data.get("corrections", [])
        engagement = raw_data.get("engagement_level", "medium")
        error_patterns = analysis.get("error_patterns", [])
        focus_areas = analysis.get("focus_areas", [])
        vocab_gaps = analysis.get("vocabulary_gaps", [])
        grammar_issues = analysis.get("grammar_issues", [])

        # Build sections based on available assessment data
        error_section = ""
        if error_patterns:
            error_section = f"""## SPECIFIC ERRORS TO ADDRESS (from user assessments)
{chr(10).join(f"• {error}" for error in error_patterns[:5])}
These errors must be targeted in the lesson exercises."""
        else:
            error_section = f"""## USER STRENGTHS & AREAS FOR IMPROVEMENT
The user has demonstrated good performance. Focus on:
{chr(10).join(f"• {skill}" for skill in specific_skills[:5]) if specific_skills else f"• General {expert_domain} domain vocabulary and phrases"}"""

        corrections_section = ""
        if corrections:
            corrections_section = f"""
## VOCABULARY CORRECTIONS & IMPROVEMENTS
Use these corrected forms in lessons:
{chr(10).join(f"• {corr}" for corr in corrections[:5])}"""

        skills_section = ""
        if specific_skills:
            skills_section = f"""
## DOMAIN-SPECIFIC SKILLS TO DEVELOP
Focus lessons on these {expert_domain} domain skills:
{chr(10).join(f"• {skill}" for skill in specific_skills)}"""

        prompt = f"""You are a professional language curriculum designer specializing in {language} instruction. Generate a highly personalized, pedagogically sound lesson for the {expert_domain} domain.

## USER PROFILE
- Proficiency Level: {analysis['difficulty_level'].upper()}
- Grammar Competency: {analysis.get('avg_grammar_score', 0)}/10
- Engagement Level: {engagement.replace('_', ' ').title()}
- Primary Focus Areas: {', '.join(focus_areas[:3]) if focus_areas else 'General language skills'}

{error_section}
{corrections_section}
{skills_section}

## LESSON DESIGN REQUIREMENTS
Create 8-10 high-quality exercises that directly address the user's assessment data:

1. **TYPING EXERCISES** (2-3):
   - Real-world {expert_domain} scenarios user needs to handle
   - Use vocabulary from their assessment corrections if available
   - Build confidence in practical communication

2. **FILL-IN-THE-BLANK EXERCISES** (2-3):
   - Address any grammar issues from assessments
   - Use domain-specific terminology
   - Provide 4-5 plausible options

3. **WORD ORDER EXERCISES** (1-2):
   - Correct sentence structure patterns
   - Use authentic {expert_domain} context
   - 5-7 words to rearrange

4. **MATCHING EXERCISES** (1-2):
   - Domain terminology with definitions/translations
   - Build vocabulary gaps identified in assessments
   - 6-8 meaningful pairs

## CONTENT STANDARDS
✓ PERSONALIZED: Directly use assessment errors and focus areas
✓ AUTHENTIC: Real {expert_domain} vocabulary and scenarios
✓ CLEAR: Explanations teach WHY answers are correct
✓ GRADUAL: Progress from assessed level to next skill level
✓ NATURAL: Native-like grammar and phrasing (proficiency: {analysis['difficulty_level']})

## OUTPUT FORMAT - STRICT JSON ONLY
Generate ONLY valid JSON with 8-10 total exercises. No markdown. No explanations. No code blocks.

{{
  "lesson_title": "Personalized {expert_domain.title()} Practice Based on Your Assessment",
  "description": "Targeted exercises addressing your specific learning needs from assessments",
  "exercises": [
    {{
      "type": "typing",
      "question": "Type a complete sentence for: ...",
      "correct_answer": "Complete sentence in {language}",
      "explanation": "Why this answer is correct...",
      "audio_text": "Complete sentence in {language}",
      "hints": ["Hint 1", "Hint 2"]
    }},
    {{
      "type": "fill_blank",
      "question": "Fill: The ___ is on the table",
      "correct_answer": "book",
      "options": ["book", "table", "chair", "wall"],
      "explanation": "This is the correct word because...",
      "audio_text": "The book is on the table",
      "hints": ["Think about objects", "It's something you read"]
    }},
    {{
      "type": "word_order",
      "question": "Rearrange to form correct sentence",
      "correct_answer": "I go to school every day",
      "options": ["every", "I", "go", "to", "school", "day"],
      "explanation": "Correct English word order places subject first...",
      "audio_text": "I go to school every day",
      "hints": ["Subject comes first", "Time expressions go at end"]
    }},
    {{
      "type": "matching",
      "question": "Match words with definitions",
      "correct_answer": "word1=definition1,word2=definition2",
      "options": ["definition1", "definition2"],
      "explanation": "These are the correct pairings...",
      "audio_text": "word1 definition1",
      "hints": ["Look for similar patterns", "Consider word categories"]
    }}
  ]
}}

REMINDER: Generate 8-10 exercises total with mix of all 4 types."""

        return prompt

    def _parse_lesson_content(self, content: str, language: str, expert: str) -> Dict:
        """Parse AI-generated lesson content"""

        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                logger.debug(
                    "Extracting JSON from markdown code block (```json)")
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                logger.debug("Extracting JSON from markdown code block (```)")
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()

            # Remove any leading/trailing whitespace
            content = content.strip()

            lesson_data = json.loads(content)

            logger.info(f"✓ JSON parsed successfully")
            logger.info(
                f"  - Lesson Title: {lesson_data.get('lesson_title', 'N/A')}")
            logger.info(
                f"  - Description: {lesson_data.get('description', 'N/A')}")

            # Validate and enhance exercises
            exercise_types_count = {}
            for i, exercise in enumerate(lesson_data.get("exercises", [])):
                exercise["id"] = f"ex_{i+1}"
                exercise["completed"] = False
                exercise["attempts"] = 0

                ex_type = exercise.get("type", "unknown")
                exercise_types_count[ex_type] = exercise_types_count.get(
                    ex_type, 0) + 1

                logger.debug(
                    f"  Exercise {i+1}: type={ex_type}, question='{exercise.get('question', '')[:60]}...'")

                # Ensure all required fields exist
                if "hints" not in exercise:
                    exercise["hints"] = []
                if "audio_text" not in exercise:
                    exercise["audio_text"] = exercise.get("correct_answer", "")
                if "options" not in exercise and exercise["type"] in ["fill_blank", "word_order", "matching"]:
                    exercise["options"] = []

            logger.info(
                f"LESSON PARSED:\n  - Total Exercises: {len(lesson_data.get('exercises', []))}\n  - Exercise Types: {exercise_types_count}")

            return lesson_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse lesson JSON: {e}")
            logger.debug(f"Content preview: {content[:500]}")
            return self._generate_fallback_lesson(language, expert, {})

    def _generate_fallback_lesson(self, language: str, expert: str, analysis: Dict) -> Dict:
        """Generate a basic lesson if AI generation fails"""

        # Get language-specific examples
        if language.lower() == "dutch":
            examples = self._get_dutch_examples(expert)
        elif language.lower() == "english":
            examples = self._get_english_examples(expert)
        elif language.lower() == "chinese":
            examples = self._get_chinese_examples(expert)
        else:
            examples = self._get_dutch_examples(expert)

        return {
            "lesson_title": f"Practice Session - {expert.title()}",
            "description": f"Basic {language} exercises for {expert} context",
            "exercises": examples,
            "metadata": {
                "language": language,
                "expert": expert,
                "difficulty": analysis.get("difficulty_level", "beginner"),
                "generated_at": datetime.now().isoformat(),
                "fallback": True
            }
        }

    def _get_dutch_examples(self, expert: str) -> List[Dict]:
        """Get Dutch language examples for fallback"""

        if expert == "healthcare":
            return [
                {
                    "id": "ex_1",
                    "type": "typing",
                    "question": "Type deze zin correct:",
                    "correct_answer": "Ik voel me niet lekker.",
                    "explanation": "Basis uitdrukking voor onwel voelen",
                    "audio_text": "Ik voel me niet lekker.",
                    "hints": ["Let op spelling", "Gebruik 'me' niet 'mij'"],
                    "completed": False,
                    "attempts": 0
                },
                {
                    "id": "ex_2",
                    "type": "fill_blank",
                    "question": "Ik heb ___ in mijn buik.",
                    "correct_answer": "pijn",
                    "options": ["pijn", "pijnen", "zeer", "pijntje"],
                    "explanation": "'Pijn' is het correcte woord voor pain",
                    "audio_text": "Ik heb pijn in mijn buik.",
                    "hints": ["Denk aan het medische vocabulaire"],
                    "completed": False,
                    "attempts": 0
                },
                {
                    "id": "ex_3",
                    "type": "word_order",
                    "question": "Zet deze woorden in de juiste volgorde:",
                    "correct_answer": "Ik moet naar de dokter.",
                    "options": ["dokter", "de", "naar", "moet", "Ik"],
                    "explanation": "Nederlandse zinsopbouw: Subject + werkwoord + rest",
                    "audio_text": "Ik moet naar de dokter.",
                    "hints": ["Begin met 'Ik'", "Werkwoord op tweede plaats"],
                    "completed": False,
                    "attempts": 0
                },
                {
                    "id": "ex_4",
                    "type": "matching",
                    "question": "Match Dutch healthcare terms with English translations:",
                    "correct_answer": "ziek=sick,dokter=doctor,pijn=pain,medicijn=medicine",
                    "options": ["ziek", "dokter", "pijn", "medicijn", "sick", "doctor", "pain", "medicine"],
                    "explanation": "Essential healthcare vocabulary in Dutch",
                    "audio_text": "ziek dokter pijn medicijn",
                    "hints": ["Think about medical context", "Group by meaning"],
                    "completed": False,
                    "attempts": 0
                }
            ]
        else:
            return [
                {
                    "id": "ex_1",
                    "type": "typing",
                    "question": "Type deze zin:",
                    "correct_answer": "Goedemorgen, hoe gaat het met u?",
                    "explanation": "Formele begroeting in het Nederlands",
                    "audio_text": "Goedemorgen, hoe gaat het met u?",
                    "hints": ["Gebruik 'u' voor formeel"],
                    "completed": False,
                    "attempts": 0
                }
            ]

    def _get_english_examples(self, expert: str) -> List[Dict]:
        """Get English examples for fallback"""
        return [
            {
                "id": "ex_1",
                "type": "typing",
                "question": "Type this sentence:",
                "correct_answer": "I am learning English.",
                "explanation": "Basic present continuous",
                "audio_text": "I am learning English.",
                "hints": ["Use present continuous form"],
                "completed": False,
                "attempts": 0
            }
        ]

    def _get_chinese_examples(self, expert: str) -> List[Dict]:
        """Get Chinese examples for fallback"""
        return [
            {
                "id": "ex_1",
                "type": "typing",
                "question": "输入这个句子:",
                "correct_answer": "我在学习中文。",
                "explanation": "基本的现在进行时",
                "audio_text": "我在学习中文。",
                "hints": ["使用 '在' 表示进行时"],
                "completed": False,
                "attempts": 0
            }
        ]

    def save_lesson(self, user_id: str, lesson: Dict) -> str:
        """Save lesson to user's directory"""

        user_dir = Path(f"data/users/{user_id}")
        user_dir.mkdir(parents=True, exist_ok=True)

        lessons_dir = user_dir / "lessons"
        lessons_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        lesson_file = lessons_dir / f"lesson_{timestamp}.json"

        with open(lesson_file, "w", encoding="utf-8") as f:
            json.dump(lesson, f, indent=2, ensure_ascii=False)

        return str(lesson_file)

    def load_user_lessons(self, user_id: str) -> List[Dict]:
        """Load all lessons for a user"""

        lessons_dir = Path(f"data/users/{user_id}/lessons")

        if not lessons_dir.exists():
            return []

        lessons = []
        for lesson_file in sorted(lessons_dir.glob("lesson_*.json"), reverse=True):
            try:
                with open(lesson_file, "r", encoding="utf-8") as f:
                    lesson = json.load(f)
                    lesson["file_path"] = str(lesson_file)
                    lessons.append(lesson)
            except Exception as e:
                print(f"Error loading lesson {lesson_file}: {e}")

        return lessons

    def update_lesson_progress(
        self,
        user_id: str,
        lesson_file: str,
        exercise_id: str,
        completed: bool,
        attempts: int
    ):
        """Update progress for a specific exercise"""

        try:
            with open(lesson_file, "r", encoding="utf-8") as f:
                lesson = json.load(f)

            # Find and update the exercise
            for exercise in lesson.get("exercises", []):
                if exercise.get("id") == exercise_id:
                    exercise["completed"] = completed
                    exercise["attempts"] = attempts
                    break

            # Save updated lesson
            with open(lesson_file, "w", encoding="utf-8") as f:
                json.dump(lesson, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error updating lesson progress: {e}")

    def calculate_lesson_score(self, lesson: Dict) -> Dict[str, Any]:
        """Calculate overall score for a completed lesson"""

        exercises = lesson.get("exercises", [])
        if not exercises:
            return {"score": 0, "total": 0, "percentage": 0}

        completed = sum(1 for ex in exercises if ex.get("completed", False))
        total = len(exercises)

        # Calculate score based on attempts (fewer attempts = better score)
        total_score = 0
        for ex in exercises:
            if ex.get("completed", False):
                attempts = ex.get("attempts", 1)
                # First try: 100%, second: 75%, third+: 50%
                if attempts == 1:
                    total_score += 100
                elif attempts == 2:
                    total_score += 75
                else:
                    total_score += 50

        avg_score = (total_score / total) if total > 0 else 0

        return {
            "score": round(avg_score, 1),
            "completed": completed,
            "total": total,
            "percentage": round((completed / total) * 100, 1) if total > 0 else 0
        }


# === HELPER FUNCTIONS ===

def generate_lesson_for_user(user_id: str, language: str = "dutch", expert: str = "healthcare") -> Dict:
    """Convenient function to generate a lesson for a user"""

    generator = LessonGenerator()

    # Load user's assessments
    assessment_file = Path(f"data/users/{user_id}/assessments.json")
    assessments = []

    if assessment_file.exists():
        with open(assessment_file, "r", encoding="utf-8") as f:
            assessments = json.load(f)

    # Generate lesson
    lesson = generator.generate_lesson_plan(
        user_id, language, expert, assessments)

    # Save lesson
    lesson_path = generator.save_lesson(user_id, lesson)

    print(f"✅ Lesson generated and saved to: {lesson_path}")
    return lesson


if __name__ == "__main__":
    # Example usage
    print("Generating lesson for user 'tester'...")
    lesson = generate_lesson_for_user("tester", "dutch", "healthcare")

    # Display summary
    print(f"\n📚 Lesson: {lesson.get('lesson_title')}")
    print(f"📝 Description: {lesson.get('description')}")
    print(f"🎯 Exercises: {len(lesson.get('exercises', []))}")
    print(
        f"📊 Difficulty: {lesson.get('metadata', {}).get('difficulty', 'N/A')}")
