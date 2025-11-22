"""
Test script to debug lesson generation issues
"""
from src.utils.utils import get_logger
from src.services.lesson_generator import LessonGenerator
import json
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent))


logger = get_logger("test_lesson_gen")


def test_lesson_generator():
    """Test the lesson generator with various inputs"""

    print("\n" + "="*60)
    print("TEST: LessonGenerator.generate_lesson_plan()")
    print("="*60)

    try:
        # Initialize generator
        print("\n[1] Initializing LessonGenerator...")
        generator = LessonGenerator()
        print("    ✓ Generator initialized")

        # Test parameters
        user_id = "test_user"
        language = "dutch"
        expert = "general"
        assessments = []

        print(f"\n[2] Calling generate_lesson_plan() with:")
        print(f"    - user_id: {user_id}")
        print(f"    - language: {language}")
        print(f"    - expert: {expert}")
        print(f"    - assessments: {assessments}")

        # Call the method
        lesson = generator.generate_lesson_plan(
            user_id, language, expert, assessments)

        print(f"\n[3] ✓ Lesson generated successfully!")
        print(f"    - Type: {type(lesson)}")
        print(
            f"    - Keys: {list(lesson.keys()) if isinstance(lesson, dict) else 'N/A'}")

        if isinstance(lesson, dict):
            print(f"\n[4] Lesson structure:")
            for key, value in lesson.items():
                if key == "exercises" and isinstance(value, list):
                    print(f"    - {key}: {len(value)} exercises")
                    for i, ex in enumerate(value[:2]):  # Show first 2
                        print(
                            f"        [{i}] type={ex.get('type')}, prompt={str(ex.get('prompt', ''))[:50]}...")
                else:
                    val_str = str(value)[:100] if not isinstance(
                        value, (dict, list)) else f"{type(value).__name__}"
                    print(f"    - {key}: {val_str}")

        # Test save_lesson
        print(f"\n[5] Testing save_lesson()...")
        lesson_path = generator.save_lesson(user_id, lesson)
        print(f"    ✓ Lesson saved to: {lesson_path}")

        # Verify file exists
        if Path(lesson_path).exists():
            print(f"    ✓ File exists and is readable")
            file_size = Path(lesson_path).stat().st_size
            print(f"    - File size: {file_size} bytes")
        else:
            print(f"    ✗ File NOT found: {lesson_path}")

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60 + "\n")
        return True

    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        print("\n" + "="*60)
        print("✗ TEST FAILED")
        print("="*60 + "\n")
        return False


def test_with_assessments():
    """Test with actual assessment data"""
    print("\n" + "="*60)
    print("TEST: LessonGenerator with sample assessments")
    print("="*60)

    try:
        generator = LessonGenerator()

        # Create sample assessment
        sample_assessments = [
            {
                "language_analysis": {
                    "grammar_score": 6,
                    "vocabulary_level": "intermediate",
                    "errors": [
                        "Missing subject pronoun",
                        "Verb conjugation error"
                    ]
                },
                "overall_score": {
                    "focus_areas": ["grammar", "pronunciation"]
                }
            }
        ]

        print(f"\n[1] Generating lesson with sample assessments...")
        lesson = generator.generate_lesson_plan(
            "test_user", "dutch", "general", sample_assessments)
        print(f"    ✓ Lesson generated")

        if isinstance(lesson, dict) and lesson.get("exercises"):
            print(f"    - Generated {len(lesson['exercises'])} exercises")

        return True

    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "█"*60)
    print("LESSON GENERATOR TEST SUITE")
    print("█"*60)

    test1_passed = test_lesson_generator()
    test2_passed = test_with_assessments()

    print("\n" + "█"*60)
    if test1_passed and test2_passed:
        print("✓ ALL TESTS PASSED - Lesson generator is working")
    else:
        print("✗ SOME TESTS FAILED - See errors above")
    print("█"*60 + "\n")
