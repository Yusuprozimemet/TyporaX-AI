"""
Enhanced Assessment Tracking System
Provides session-based tracing, analytics, and progress visualization
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from src.utils.utils import get_logger

logger = get_logger(__name__)


class AssessmentTracker:
    """Enhanced tracker for user learning progress with session management"""

    def __init__(self, user_id: str, base_dir: str = "data/users"):
        self.user_id = user_id
        self.user_dir = Path(base_dir) / user_id
        self.user_dir.mkdir(parents=True, exist_ok=True)

        # File paths
        self.assessments_file = self.user_dir / "assessments.json"
        self.sessions_dir = self.user_dir / "sessions"
        self.sessions_dir.mkdir(exist_ok=True)
        self.progress_file = self.user_dir / "progress.json"
        self.analytics_dir = self.user_dir / "analytics"
        self.analytics_dir.mkdir(exist_ok=True)

        # Current session tracking
        self.current_session_id = None
        self.current_session_data = []

    def start_session(self, expert: str, language: str = "dutch") -> str:
        """Start a new learning session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session_id = session_id
        self.current_session_data = []

        session_metadata = {
            "session_id": session_id,
            "user_id": self.user_id,
            "expert": expert,
            "language": language,
            "start_time": datetime.now().isoformat(),
            "status": "active"
        }

        # Save session metadata
        session_file = self.sessions_dir / f"{session_id}_metadata.json"
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_metadata, f, indent=2, ensure_ascii=False)

        return session_id

    def add_assessment_to_session(self, assessment: Dict):
        """Add an assessment to the current session"""
        if not self.current_session_id:
            # Auto-start session if not started
            self.start_session(
                assessment.get("expert", "language"),
                assessment.get("language", "dutch")
            )

        self.current_session_data.append(assessment)

        # Also append to main assessments file for backward compatibility
        self._append_to_assessments_file(assessment)

    def end_session(self) -> Dict:
        """End current session and generate session summary"""
        if not self.current_session_id or not self.current_session_data:
            return {"error": "No active session"}

        # Calculate session metrics
        session_summary = self._calculate_session_summary()

        # Save complete session data
        session_file = self.sessions_dir / f"{self.current_session_id}.json"
        session_data = {
            "session_id": self.current_session_id,
            "user_id": self.user_id,
            "start_time": self.current_session_data[0]["timestamp"],
            "end_time": datetime.now().isoformat(),
            "assessments": self.current_session_data,
            "summary": session_summary
        }

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        # Update metadata
        metadata_file = self.sessions_dir / \
            f"{self.current_session_id}_metadata.json"
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        metadata["status"] = "completed"
        metadata["end_time"] = datetime.now().isoformat()
        metadata["summary"] = session_summary

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Update overall progress
        self._update_progress()

        # Generate analytics
        self._update_analytics()

        # Reset session
        self.current_session_id = None
        self.current_session_data = []

        return session_summary

    def _calculate_session_summary(self) -> Dict:
        """Calculate comprehensive session metrics"""
        if not self.current_session_data:
            return {}

        # Extract scores
        scores = [a["overall_score"]["overall_score"]
                  for a in self.current_session_data]
        grammar_scores = [a["language_analysis"]["grammar_score"]
                          for a in self.current_session_data]
        fluency_scores = [a["language_analysis"]["fluency_score"]
                          for a in self.current_session_data]

        # Calculate trends
        score_trend = "improving" if len(scores) > 1 and scores[-1] > scores[0] else \
                      "declining" if len(
                          scores) > 1 and scores[-1] < scores[0] else "stable"

        # Collect all errors and strengths
        all_errors = []
        all_strengths = []
        for assessment in self.current_session_data:
            all_errors.extend(
                assessment["language_analysis"].get("errors", []))
            all_strengths.extend(
                assessment["language_analysis"].get("strengths", []))

        # Time calculation
        start_time = datetime.fromisoformat(
            self.current_session_data[0]["timestamp"])
        end_time = datetime.fromisoformat(
            self.current_session_data[-1]["timestamp"])
        practice_minutes = (end_time - start_time).total_seconds() / 60

        summary = {
            "total_turns": len(self.current_session_data),
            "avg_score": round(np.mean(scores), 2),
            "min_score": round(min(scores), 2),
            "max_score": round(max(scores), 2),
            "score_trend": score_trend,
            "avg_grammar": round(np.mean(grammar_scores), 2),
            "avg_fluency": round(np.mean(fluency_scores), 2),
            "practice_time_minutes": round(practice_minutes, 1),
            "total_errors": len(all_errors),
            "total_strengths": len(all_strengths),
            "key_improvements": all_strengths[-3:] if all_strengths else [],
            "key_challenges": list(set(all_errors))[:3],
            "performance_level": self.current_session_data[-1]["overall_score"]["performance_level"],
            "expert": self.current_session_data[0]["expert"],
            "language": self.current_session_data[0]["language"]
        }

        return summary

    def _update_progress(self):
        """Update overall user progress"""
        # Load existing progress
        if self.progress_file.exists():
            with open(self.progress_file, "r", encoding="utf-8") as f:
                progress = json.load(f)
        else:
            progress = {
                "user_id": self.user_id,
                "first_session": datetime.now().isoformat(),
                "total_sessions": 0,
                "total_messages": 0,
                "total_practice_minutes": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "last_practice_date": None,
                "by_expert": {},
                "by_language": {},
                "milestones": []
            }

        # Update with current session
        if not self.current_session_data:
            return

        session_summary = self._calculate_session_summary()
        expert = session_summary["expert"]
        language = session_summary["language"]

        progress["total_sessions"] += 1
        progress["total_messages"] += session_summary["total_turns"]
        progress["total_practice_minutes"] += session_summary["practice_time_minutes"]

        # Update by expert
        if expert not in progress["by_expert"]:
            progress["by_expert"][expert] = {
                "sessions": 0,
                "total_messages": 0,
                "avg_score": 0,
                "best_score": 0
            }
        progress["by_expert"][expert]["sessions"] += 1
        progress["by_expert"][expert]["total_messages"] += session_summary["total_turns"]
        progress["by_expert"][expert]["best_score"] = max(
            progress["by_expert"][expert]["best_score"],
            session_summary["max_score"]
        )

        # Update by language
        if language not in progress["by_language"]:
            progress["by_language"][language] = {
                "sessions": 0,
                "avg_score": 0,
                "vocab_level": "beginner"
            }
        progress["by_language"][language]["sessions"] += 1

        # Update streak
        today = datetime.now().date()
        last_date = datetime.fromisoformat(progress["last_practice_date"]).date(
        ) if progress["last_practice_date"] else None

        if last_date:
            if (today - last_date).days == 1:
                progress["current_streak"] += 1
            elif (today - last_date).days > 1:
                progress["current_streak"] = 1
        else:
            progress["current_streak"] = 1

        progress["longest_streak"] = max(
            progress["longest_streak"], progress["current_streak"])
        progress["last_practice_date"] = datetime.now().isoformat()

        # Check for milestones
        self._check_milestones(progress)

        # Save progress
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)

    def _check_milestones(self, progress: Dict):
        """Check and add achieved milestones"""
        milestones_to_check = [
            (1, "first_session", "Eerste sessie voltooid! 🎉"),
            (5, "five_sessions", "5 sessies bereikt! 🌟"),
            (10, "ten_sessions", "10 sessies - Je bent consistent! 💪"),
            (25, "quarter_century", "25 sessies - Geweldig! 🏆"),
            (50, "half_century", "50 sessies - Expert in wording! 🎓"),
        ]

        existing_milestones = {m["type"]
                               for m in progress.get("milestones", [])}

        for threshold, milestone_type, message in milestones_to_check:
            if progress["total_sessions"] >= threshold and milestone_type not in existing_milestones:
                progress.setdefault("milestones", []).append({
                    "type": milestone_type,
                    "message": message,
                    "achieved_at": datetime.now().isoformat(),
                    "session_count": progress["total_sessions"]
                })

    def _update_analytics(self):
        """Generate analytical insights"""
        # Load all sessions
        sessions = self._load_all_sessions()
        if not sessions:
            return

        # Weekly summary
        weekly_summary = self._calculate_weekly_summary(sessions)
        with open(self.analytics_dir / "weekly_summary.json", "w", encoding="utf-8") as f:
            json.dump(weekly_summary, f, indent=2, ensure_ascii=False)

        # Error patterns
        error_patterns = self._analyze_error_patterns(sessions)
        with open(self.analytics_dir / "error_patterns.json", "w", encoding="utf-8") as f:
            json.dump(error_patterns, f, indent=2, ensure_ascii=False)

        # Generate visualizations
        self._generate_progress_charts(sessions)

    def _load_all_sessions(self) -> List[Dict]:
        """Load all session data"""
        sessions = []
        for session_file in self.sessions_dir.glob("session_*.json"):
            if "_metadata" not in session_file.name:
                with open(session_file, "r", encoding="utf-8") as f:
                    sessions.append(json.load(f))
        return sorted(sessions, key=lambda x: x["start_time"])

    def _calculate_weekly_summary(self, sessions: List[Dict]) -> Dict:
        """Calculate weekly performance summary"""
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        recent_sessions = [
            s for s in sessions
            if datetime.fromisoformat(s["start_time"]) > week_ago
        ]

        if not recent_sessions:
            return {"period": "last_7_days", "sessions": 0}

        all_scores = []
        for session in recent_sessions:
            all_scores.extend([
                a["overall_score"]["overall_score"]
                for a in session["assessments"]
            ])

        return {
            "period": "last_7_days",
            "sessions": len(recent_sessions),
            "total_messages": sum(s["summary"]["total_turns"] for s in recent_sessions),
            "total_minutes": sum(s["summary"]["practice_time_minutes"] for s in recent_sessions),
            "avg_score": round(np.mean(all_scores), 2) if all_scores else 0,
            "improvement_rate": self._calculate_improvement_rate(recent_sessions)
        }

    def _calculate_improvement_rate(self, sessions: List[Dict]) -> float:
        """Calculate week-over-week improvement"""
        if len(sessions) < 2:
            return 0.0

        first_half = sessions[:len(sessions)//2]
        second_half = sessions[len(sessions)//2:]

        first_avg = np.mean([
            a["overall_score"]["overall_score"]
            for s in first_half
            for a in s["assessments"]
        ])

        second_avg = np.mean([
            a["overall_score"]["overall_score"]
            for s in second_half
            for a in s["assessments"]
        ])

        return round(second_avg - first_avg, 2)

    def _analyze_error_patterns(self, sessions: List[Dict]) -> Dict:
        """Analyze common error patterns"""
        error_categories = defaultdict(int)
        error_examples = defaultdict(list)

        for session in sessions:
            for assessment in session["assessments"]:
                errors = assessment["language_analysis"].get("errors", [])
                for error in errors:
                    # Categorize error
                    if "grammatica" in error.lower() or "grammar" in error.lower():
                        category = "grammar"
                    elif "woordenschat" in error.lower() or "vocabulary" in error.lower():
                        category = "vocabulary"
                    elif "zinsbouw" in error.lower() or "sentence" in error.lower():
                        category = "sentence_structure"
                    else:
                        category = "other"

                    error_categories[category] += 1
                    if len(error_examples[category]) < 5:
                        error_examples[category].append(error)

        return {
            "categories": dict(error_categories),
            "examples": {k: v for k, v in error_examples.items()},
            "most_common": max(error_categories.items(), key=lambda x: x[1])[0] if error_categories else "none"
        }

    def _generate_progress_charts(self, sessions: List[Dict]):
        """Generate progress visualization charts"""
        if not sessions:
            return

        # Prepare data
        dates = []
        scores = []
        grammar_scores = []
        fluency_scores = []

        for session in sessions:
            for assessment in session["assessments"]:
                dates.append(datetime.fromisoformat(assessment["timestamp"]))
                scores.append(assessment["overall_score"]["overall_score"])
                grammar_scores.append(
                    assessment["language_analysis"]["grammar_score"])
                fluency_scores.append(
                    assessment["language_analysis"]["fluency_score"])

        # Create multi-panel chart
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Learning Progress Dashboard',
                     fontsize=16, fontweight='bold')

        # 1. Overall Score Trend
        axes[0, 0].plot(dates, scores, marker='o', linewidth=2,
                        markersize=4, color='#3498db', alpha=0.7)
        axes[0, 0].axhline(y=np.mean(scores), color='r', linestyle='--',
                           alpha=0.5, label=f'Average: {np.mean(scores):.1f}')
        axes[0, 0].set_title('Overall Score Progress', fontweight='bold')
        axes[0, 0].set_ylabel('Score')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # 2. Grammar vs Fluency
        axes[0, 1].plot(dates, grammar_scores, marker='s',
                        label='Grammar', linewidth=2, markersize=4, color='#2ecc71')
        axes[0, 1].plot(dates, fluency_scores, marker='^',
                        label='Fluency', linewidth=2, markersize=4, color='#e74c3c')
        axes[0, 1].set_title('Grammar vs Fluency', fontweight='bold')
        axes[0, 1].set_ylabel('Score')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # 3. Session Distribution
        session_lengths = [s["summary"]["total_turns"] for s in sessions]
        axes[1, 0].bar(range(len(session_lengths)),
                       session_lengths, color='#9b59b6', alpha=0.7)
        axes[1, 0].set_title('Messages per Session', fontweight='bold')
        axes[1, 0].set_xlabel('Session')
        axes[1, 0].set_ylabel('Messages')
        axes[1, 0].grid(True, alpha=0.3, axis='y')

        # 4. Performance Level Distribution
        levels = [a["overall_score"]["performance_level"]
                  for s in sessions for a in s["assessments"]]
        level_counts = {level: levels.count(level) for level in set(levels)}
        axes[1, 1].pie(level_counts.values(), labels=level_counts.keys(
        ), autopct='%1.1f%%', startangle=90)
        axes[1, 1].set_title(
            'Performance Level Distribution', fontweight='bold')

        plt.tight_layout()
        plt.savefig(self.analytics_dir / "progress_dashboard.png",
                    dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()

        # Generate simple trend chart
        self._generate_simple_trend(dates, scores)

    def _generate_simple_trend(self, dates, scores):
        """Generate simple trend visualization"""
        plt.figure(figsize=(10, 6))
        plt.plot(dates, scores, marker='o', linewidth=2.5,
                 markersize=6, color='#27ae60')
        plt.fill_between(dates, scores, alpha=0.3, color='#27ae60')

        # Add trend line
        if len(dates) > 1:
            z = np.polyfit(range(len(dates)), scores, 1)
            p = np.poly1d(z)
            plt.plot(dates, p(range(len(dates))), "r--",
                     alpha=0.8, linewidth=2, label='Trend')

        plt.title('Overall Learning Trend', fontsize=14, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Score', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        plt.savefig(self.user_dir / "progress.png", dpi=200,
                    bbox_inches='tight', facecolor='white')
        plt.close()

    def _append_to_assessments_file(self, assessment: Dict):
        """Append to main assessments file (backward compatibility)"""
        if self.assessments_file.exists():
            with open(self.assessments_file, "r", encoding="utf-8") as f:
                assessments = json.load(f)
        else:
            assessments = []

        assessments.append(assessment)

        # Keep only last 100 assessments
        if len(assessments) > 100:
            assessments = assessments[-100:]

        with open(self.assessments_file, "w", encoding="utf-8") as f:
            json.dump(assessments, f, indent=2, ensure_ascii=False)

    def get_progress_summary(self) -> Dict:
        """Get comprehensive progress summary from sessions or assessments"""
        # First, try to load from assessments.json if sessions are empty
        self._migrate_assessments_to_sessions()

        if not self.progress_file.exists():
            # Generate progress from sessions if progress.json doesn't exist
            return self._generate_progress_from_sessions()

        with open(self.progress_file, "r", encoding="utf-8") as f:
            progress = json.load(f)

        # Add recent sessions info
        sessions = self._load_all_sessions()
        if sessions:
            recent_session = sessions[-1]
            # Safely get expert from summary or assessments
            expert = None
            if isinstance(recent_session.get("summary"), dict):
                expert = recent_session["summary"].get("expert")
            if not expert and isinstance(recent_session.get("assessments"), list) and len(recent_session["assessments"]) > 0:
                expert = recent_session["assessments"][0].get(
                    "expert", "healthcare")
            if not expert:
                expert = recent_session.get("expert", "healthcare")

            score = recent_session.get("summary", {}).get("avg_overall_score", 0) if isinstance(
                recent_session.get("summary"), dict) else 0

            progress["last_session"] = {
                "date": recent_session.get("start_time", ""),
                "expert": expert,
                "score": score
            }

        return progress

    def _migrate_assessments_to_sessions(self):
        """Migrate assessments.json to session format if sessions are empty"""
        assessments_file = self.user_dir / "assessments.json"

        # Only migrate if we have assessments
        if not assessments_file.exists():
            return

        # Check if we already have actual session files (not just metadata)
        existing_sessions = list(self.sessions_dir.glob("*.json"))
        existing_sessions = [
            f.name for f in existing_sessions if "_metadata" not in f.name and not f.name.endswith("_metadata.json")]
        if existing_sessions and len(existing_sessions) > 0:
            return  # Already have session data, don't migrate

        try:
            with open(assessments_file, "r", encoding="utf-8") as f:
                assessments = json.load(f)

            if not isinstance(assessments, list) or len(assessments) == 0:
                return

            # Group assessments by day to create sessions
            sessions_by_date = {}
            for assessment in assessments:
                timestamp = assessment.get(
                    "timestamp", datetime.now().isoformat())
                date_key = timestamp[:10]  # YYYY-MM-DD

                if date_key not in sessions_by_date:
                    sessions_by_date[date_key] = []
                sessions_by_date[date_key].append(assessment)

            # Create session files from grouped assessments
            for date_key, date_assessments in sorted(sessions_by_date.items()):
                session_id = f"session_{date_key.replace('-', '')}_000000"

                # Calculate session summary
                avg_grammar = sum(a.get("language_analysis", {}).get("grammar_score", 0)
                                  for a in date_assessments) / len(date_assessments) if date_assessments else 0
                avg_fluency = sum(a.get("language_analysis", {}).get("fluency_score", 0)
                                  for a in date_assessments) / len(date_assessments) if date_assessments else 0
                avg_overall = sum(a.get("overall_score", {}).get("overall_score", 0)
                                  for a in date_assessments) / len(date_assessments) if date_assessments else 0

                session_data = {
                    "session_id": session_id,
                    "user_id": self.user_id,
                    "start_time": date_assessments[0].get("timestamp", datetime.now().isoformat()),
                    "end_time": date_assessments[-1].get("timestamp", datetime.now().isoformat()),
                    "assessments": date_assessments,
                    "summary": {
                        "total_messages": len(date_assessments),
                        "avg_grammar_score": round(avg_grammar, 2),
                        "avg_fluency_score": round(avg_fluency, 2),
                        "avg_overall_score": round(avg_overall, 2),
                        "expert": date_assessments[0].get("expert", "healthcare"),
                        "language": date_assessments[0].get("language", "dutch")
                    }
                }

                session_file = self.sessions_dir / f"{session_id}.json"
                with open(session_file, "w", encoding="utf-8") as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)

            # Update progress.json based on migrated sessions
            self._update_progress_from_sessions()

        except Exception as e:
            logger.error(f"Failed to migrate assessments to sessions: {e}")

    def _generate_progress_from_sessions(self) -> Dict:
        """Generate progress summary from session data"""
        sessions = self._load_all_sessions()

        if not sessions:
            return {
                "user_id": self.user_id,
                "total_sessions": 0,
                "total_messages": 0,
                "total_practice_minutes": 0,
                "current_streak": 0,
                "by_expert": {},
                "by_language": {},
                "milestones": []
            }

        # Calculate aggregated stats
        total_messages = sum(len(s.get("assessments", [])) for s in sessions)
        by_expert = {}
        by_language = {}

        for session in sessions:
            expert = session.get("summary", {}).get("expert", "healthcare")
            language = session.get("summary", {}).get("language", "dutch")

            if expert not in by_expert:
                by_expert[expert] = {
                    "sessions": 0,
                    "total_messages": 0,
                    "avg_score": 0
                }
            by_expert[expert]["sessions"] += 1
            by_expert[expert]["total_messages"] += len(
                session.get("assessments", []))
            by_expert[expert]["avg_score"] = session.get(
                "summary", {}).get("avg_overall_score", 0)

            if language not in by_language:
                by_language[language] = {
                    "sessions": 0,
                    "avg_score": 0,
                    "vocab_level": "intermediate"
                }
            by_language[language]["sessions"] += 1
            by_language[language]["avg_score"] = session.get(
                "summary", {}).get("avg_overall_score", 0)

        return {
            "user_id": self.user_id,
            "total_sessions": len(sessions),
            "total_messages": total_messages,
            # Estimate 10 min per session
            "total_practice_minutes": len(sessions) * 10,
            "current_streak": 1,
            "by_expert": by_expert,
            "by_language": by_language,
            "milestones": []
        }

    def _update_progress_from_sessions(self):
        """Update progress.json from session data"""
        progress = self._generate_progress_from_sessions()
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)


# Integration functions for backward compatibility
async def save_assessment_data(user_id: str, assessment: Dict):
    """Enhanced save with session tracking (backward compatible)"""
    tracker = AssessmentTracker(user_id)

    # If no active session, just append to main file
    if not tracker.current_session_id:
        tracker._append_to_assessments_file(assessment)
    else:
        tracker.add_assessment_to_session(assessment)
