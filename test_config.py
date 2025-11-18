"""
Test centralized configuration system
"""
from config.settings import config


def test_config():
    """Test that all configuration values are accessible"""
    print("🔧 Testing centralized configuration...")

    print(f"✓ DEFAULT_MODEL: {config.DEFAULT_MODEL}")
    print(f"✓ FALLBACK_MODEL: {config.FALLBACK_MODEL}")
    print(f"✓ HF_API_URL: {config.HF_API_URL}")
    print(f"✓ HF_TOKEN: {'Set' if config.HF_TOKEN else 'Not set'}")
    print(f"✓ APP_NAME: {config.APP_NAME}")
    print(f"✓ VERSION: {config.VERSION}")

    # Test config validation
    is_valid = config.validate()
    print(f"✓ Config validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")

    # Test import from different files
    print("\n🔗 Testing imports from expert files...")
    try:
        from src.experts.healthcare_expert import DEFAULT_MODEL, FALLBACK_MODEL, HF_API_URL
        print(f"✓ Healthcare Expert - DEFAULT_MODEL: {DEFAULT_MODEL}")
        print(f"✓ Healthcare Expert - FALLBACK_MODEL: {FALLBACK_MODEL}")
        print(f"✓ Healthcare Expert - HF_API_URL: {HF_API_URL}")
    except ImportError as e:
        print(f"❌ Healthcare Expert import failed: {e}")

    try:
        from src.services.lesson_bot import DEFAULT_MODEL, FALLBACK_MODEL, HF_API_URL
        print(f"✓ Lesson Bot - DEFAULT_MODEL: {DEFAULT_MODEL}")
        print(f"✓ Lesson Bot - FALLBACK_MODEL: {FALLBACK_MODEL}")
        print(f"✓ Lesson Bot - HF_API_URL: {HF_API_URL}")
    except ImportError as e:
        print(f"❌ Lesson Bot import failed: {e}")

    print("\n🎉 Configuration centralization test complete!")


if __name__ == "__main__":
    test_config()
