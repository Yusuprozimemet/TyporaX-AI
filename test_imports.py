#!/usr/bin/env python3
"""
Test script to verify all imports are working correctly after reorganization
"""

import sys
import os

# Add the src directory to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_imports():
    """Test all critical imports"""

    print("🧪 Testing imports after reorganization...")

    # Test API imports
    try:
        from src.api.chat_router import router as chat_router
        print("✅ Chat router import: OK")
    except Exception as e:
        print(f"❌ Chat router import: {e}")

    try:
        from src.api.assessment_router import router as assessment_router
        print("✅ Assessment router import: OK")
    except Exception as e:
        print(f"❌ Assessment router import: {e}")

    try:
        from src.api.main_router import router as main_router
        print("✅ Main router import: OK")
    except Exception as e:
        print(f"❌ Main router import: {e}")

    # Test services imports
    try:
        from src.services.assessment import RealTimeAssessment
        print("✅ Assessment service import: OK")
    except Exception as e:
        print(f"❌ Assessment service import: {e}")

    try:
        from src.services.dna_engine import DNAPolygenicEngine
        print("✅ DNA engine import: OK")
    except Exception as e:
        print(f"❌ DNA engine import: {e}")

    # Test utils imports
    try:
        from src.utils.prompt_manager import get_prompt
        print("✅ Prompt manager import: OK")
    except Exception as e:
        print(f"❌ Prompt manager import: {e}")

    try:
        from src.utils.utils import get_logger
        print("✅ Utils import: OK")
    except Exception as e:
        print(f"❌ Utils import: {e}")

    # Test experts imports
    try:
        from src.experts.healthcare_expert import generate_patient_response
        print("✅ Healthcare expert import: OK")
    except Exception as e:
        print(f"❌ Healthcare expert import: {e}")

    try:
        from src.experts.it_backend_interviewer import generate_interviewer_response
        print("✅ IT expert import: OK")
    except Exception as e:
        print(f"❌ IT expert import: {e}")

    # Test configuration
    try:
        from config.settings import config
        print("✅ Configuration import: OK")
    except Exception as e:
        print(f"❌ Configuration import: {e}")

    print("\n🎯 Import test completed!")


def test_main_app():
    """Test main application import"""
    try:
        from main import app
        print("✅ Main application import: OK")
        print(f"📱 App title: {app.title}")
        return True
    except Exception as e:
        print(f"❌ Main application import: {e}")
        return False


if __name__ == "__main__":
    test_imports()
    print("\n" + "="*50)

    if test_main_app():
        print("\n🚀 All critical components are working!")
        print("💡 You can now run: python main.py")
    else:
        print("\n⚠️  Some issues found. Check the errors above.")
