import pytest
import asyncio
import os
from src.experts.tax_authority_expert import TaxAuthorityExpert


async def test_tax_authority_flow():
    scenario = "tax_authority_nl_for_en"
    expert = TaxAuthorityExpert()

    # Start session
    session = await expert.start_session("testuser", scenario)
    assert session.get("session_id")

    # Submit a learner turn
    reply = await expert.respond_to_text(session, "Hello, I need help with my income tax return.")
    assert isinstance(reply, str) and len(reply) > 0

    # Score a sample transcript
    transcript = "My name is Alex Jansen. Date of birth 12-03-1988. I need a refund for last year."
    result = expert.score_attempt(transcript)
    assert "total" in result and isinstance(result["total"], int)


if __name__ == "__main__":
    asyncio.run(test_tax_authority_flow())
"""
Unit tests for Tax Authority Expert
"""


@pytest.fixture
def tax_expert():
    """Create a tax authority expert instance"""
    return TaxAuthorityExpert()


def test_tax_expert_initialization(tax_expert):
    """Test that tax expert initializes correctly"""
    assert tax_expert is not None
    assert tax_expert.hf_token is not None
    assert tax_expert.default_model is not None


@pytest.mark.asyncio
async def test_start_english_session(tax_expert):
    """Test starting a Dutch tax authority session"""
    session = await tax_expert.start_session("test_user", "tax_authority")

    assert session["user_id"] == "test_user"
    assert session["scenario_id"] == "tax_authority"
    assert "session_id" in session
    assert "agent_greeting" in session
    assert "Good" in session["agent_greeting"] or "morning" in session["agent_greeting"]


@pytest.mark.asyncio
async def test_start_french_session(tax_expert):
    """Test starting a Dutch tax authority session"""
    session = await tax_expert.start_session("test_user", "tax_authority")

    assert session["scenario_id"] == "tax_authority"
    assert "agent_greeting" in session


@pytest.mark.asyncio
async def test_start_chinese_session(tax_expert):
    """Test starting a Dutch tax authority session"""
    session = await tax_expert.start_session("test_user", "tax_authority")

    assert session["scenario_id"] == "tax_authority"
    assert "agent_greeting" in session


@pytest.mark.asyncio
async def test_respond_to_english_text(tax_expert):
    """Test generating a Dutch response"""
    session = {
        "session_id": "test_session",
        "scenario_id": "tax_authority",
        "user_id": "test_user"
    }

    response = await tax_expert.respond_to_text(session, "Hello, I need help with my tax return.")

    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_respond_to_french_text(tax_expert):
    """Test generating a Dutch response"""
    session = {
        "session_id": "test_session",
        "scenario_id": "tax_authority",
        "user_id": "test_user"
    }

    response = await tax_expert.respond_to_text(session, "Bonjour, j'ai besoin d'aide avec ma déclaration d'impôts.")

    assert response is not None
    assert isinstance(response, str)


@pytest.mark.asyncio
async def test_respond_to_chinese_text(tax_expert):
    """Test generating a Dutch response"""
    session = {
        "session_id": "test_session",
        "scenario_id": "tax_authority",
        "user_id": "test_user"
    }

    response = await tax_expert.respond_to_text(session, "您好，我需要关于税务申报的帮助。")

    assert response is not None
    assert isinstance(response, str)


def test_score_complete_attempt(tax_expert):
    """Test scoring a complete tax call attempt"""
    transcript = """
    Hello, I'd like to speak to someone about my tax return.
    My name is John Smith and my tax ID is 123456789.
    I'd like to know what deductions I can claim for my home office.
    Can you also tell me when the filing deadline is?
    Thank you for your help.
    """

    result = tax_expert.score_attempt(transcript)

    assert "score" in result
    assert "breakdown" in result
    assert result["score"] >= 60  # Should score well for complete attempt


def test_score_incomplete_attempt(tax_expert):
    """Test scoring an incomplete attempt"""
    transcript = "Hello"

    result = tax_expert.score_attempt(transcript)

    assert "score" in result
    assert result["score"] < 60  # Should score lower for incomplete attempt


def test_score_professional_tone(tax_expert):
    """Test that rude language affects score"""
    transcript = "You are stupid! I hate this service!"

    result = tax_expert.score_attempt(transcript)

    # Should mark professional_tone as False
    assert result["breakdown"]["professional_tone"] == 0


def test_heuristic_response_tax_keywords(tax_expert):
    """Test heuristic response generation with tax keywords"""
    response = tax_expert._get_heuristic_response(
        "When is the tax return deadline?")

    assert response is not None
    assert len(response) > 0
    assert "May 1" in response or "deadline" in response.lower(
    ) or "filing" in response.lower()


def test_heuristic_response_deduction_keywords(tax_expert):
    """Test heuristic response for deduction questions"""
    response = tax_expert._get_heuristic_response(
        "What deductions can I claim?")

    assert response is not None
    assert "deduct" in response.lower() or "eligible" in response.lower()


def test_heuristic_response_goodbye(tax_expert):
    """Test heuristic response for goodbye"""
    response = tax_expert._get_heuristic_response("Thank you, goodbye!")

    assert response is not None
    assert "thank" in response.lower(
    ) or "good" in response.lower() or "bye" in response.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
