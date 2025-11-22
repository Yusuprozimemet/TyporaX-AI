"""
Lesson Generation Logger - Records detailed logs of how lessons are generated
Stores logs in user-specific directories for audit trail and debugging
"""

import json
import os
from datetime import datetime
from pathlib import Path


class LessonLogger:
    """Logs lesson generation details for debugging and verification"""

    @staticmethod
    def log_generation(user_id: str, analysis: dict, prompt: str, ai_response: str, lesson: dict):
        """Log complete lesson generation information"""

        user_log_dir = Path(f"data/users/{user_id}/lesson_logs")
        user_log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "prompt_preview": prompt[:500],  # First 500 chars of prompt
            # First 500 chars of response
            "ai_response_preview": ai_response[:500],
            "lesson": {
                "title": lesson.get("lesson_title"),
                "description": lesson.get("description"),
                "exercise_count": len(lesson.get("exercises", [])),
                "exercises": [
                    {
                        "id": ex.get("id"),
                        "type": ex.get("type"),
                        "question": ex.get("question", "")[:100],
                        "correct_answer": ex.get("correct_answer", "")[:100]
                    }
                    for ex in lesson.get("exercises", [])
                ],
                "metadata": lesson.get("metadata", {})
            }
        }

        # Save detailed log
        log_file = user_log_dir / f"lesson_log_{timestamp}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)

        # Save full prompt and response for inspection
        prompt_file = user_log_dir / f"prompt_{timestamp}.txt"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(f"=== LESSON GENERATION PROMPT ===\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"User: {user_id}\n")
            f.write(f"\n{prompt}\n")

        response_file = user_log_dir / f"response_{timestamp}.txt"
        with open(response_file, "w", encoding="utf-8") as f:
            f.write(f"=== AI RESPONSE ===\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"User: {user_id}\n")
            f.write(f"\n{ai_response}\n")

        return str(log_file)

    @staticmethod
    def get_latest_log(user_id: str) -> dict:
        """Get the most recent lesson generation log"""

        user_log_dir = Path(f"data/users/{user_id}/lesson_logs")
        if not user_log_dir.exists():
            return None

        log_files = sorted(user_log_dir.glob(
            "lesson_log_*.json"), reverse=True)
        if not log_files:
            return None

        with open(log_files[0], "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def get_all_logs(user_id: str) -> list:
        """Get all lesson generation logs for a user"""

        user_log_dir = Path(f"data/users/{user_id}/lesson_logs")
        if not user_log_dir.exists():
            return []

        logs = []
        for log_file in sorted(user_log_dir.glob("lesson_log_*.json"), reverse=True):
            with open(log_file, "r", encoding="utf-8") as f:
                logs.append(json.load(f))

        return logs

    @staticmethod
    def get_assessment_impact_summary(user_id: str) -> dict:
        """Analyze how assessments impacted lesson generation over time"""

        logs = LessonLogger.get_all_logs(user_id)
        if not logs:
            return {"error": "No lesson logs found"}

        summary = {
            "total_lessons_generated": len(logs),
            "lessons": []
        }

        for log in logs:
            lesson_summary = {
                "timestamp": log.get("timestamp"),
                "difficulty": log.get("analysis", {}).get("difficulty_level"),
                "grammar_score": log.get("analysis", {}).get("avg_grammar_score"),
                "error_patterns": log.get("analysis", {}).get("error_patterns", [])[:3],
                "focus_areas": log.get("analysis", {}).get("focus_areas", []),
                "exercise_types": {}
            }

            # Count exercise types
            for ex in log.get("lesson", {}).get("exercises", []):
                ex_type = ex.get("type", "unknown")
                lesson_summary["exercise_types"][ex_type] = lesson_summary["exercise_types"].get(
                    ex_type, 0) + 1

            summary["lessons"].append(lesson_summary)

        return summary
