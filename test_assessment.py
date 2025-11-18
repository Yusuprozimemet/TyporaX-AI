"""
Test assessment system directly
"""
import asyncio
from config.settings import config
from src.services.assessment import RealTimeAssessment


async def test_assessment():
    """Test the assessment system directly"""

    if not config.HF_TOKEN:
        print("❌ HF_TOKEN not found")
        return

    print(f"✅ HF_TOKEN found: {config.HF_TOKEN[:10]}...")

    # Create assessment system
    assessment_system = RealTimeAssessment(
        hf_token=config.HF_TOKEN,
        api_url=config.HF_API_URL
    )

    # Test message with obvious grammar issues
    test_message = "ik ben ziekte"

    print(f"\n🧪 Testing message: '{test_message}'")
    print("Expected issues: 'ziekte' should be 'ziek'")

    # Test language analysis directly
    try:
        result = await assessment_system._analyze_language_quality(test_message)
        print(f"\n📊 Result:")
        print(f"Grammar Score: {result.get('grammar_score', 'N/A')}")
        print(f"Vocabulary Level: {result.get('vocabulary_level', 'N/A')}")
        print(f"Fluency Score: {result.get('fluency_score', 'N/A')}")
        print(f"Errors: {result.get('errors', [])}")
        print(f"Corrections: {result.get('corrections', [])}")
        print(f"Improved Version: '{result.get('improved_version', 'N/A')}'")
        print(f"Explanation: {result.get('explanation', 'N/A')}")

        # Check if it's just fallback
        if result.get('improved_version') == test_message:
            print("⚠️  WARNING: No improvements detected - might be using fallback")
        else:
            print("✅ Real AI analysis detected")

    except Exception as e:
        print(f"❌ Assessment failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_assessment())
