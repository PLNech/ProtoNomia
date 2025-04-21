import pytest
import time
from typing import Dict, Any, Optional
from pydantic import ValidationError

from models.actions import ActionType
from models.base import Agent, AgentFaction, AgentType

# Import the ActionResponse model we'll be working with
from llm_models import AgentActionResponse


class TestActionModels:
    """Tests for the action response models"""

    def test_agent_action_response_with_reasoning(self):
        """Test that the original format with reasoning works"""
        # Valid response with reasoning
        data = {
            "type": "BUY",
            "extra": {"desired_item": "Food Pack"},
            "reasoning": "I need food to survive and have enough credits to purchase it."
        }
        
        # This should validate successfully 
        response = AgentActionResponse(**data)
        assert response.type == ActionType.BUY
        assert response.extra["desired_item"] == "Food Pack"
        assert response.reasoning == "I need food to survive and have enough credits to purchase it."

    def test_agent_action_response_without_reasoning(self):
        """Test that the simplified format without reasoning still works"""
        # Response without reasoning (what gemma3:4b is producing)
        data = {
            "type": "BUY",
            "extra": {"desired_item": "Food Pack"}
        }
        
        # This should validate successfully with our improvements 
        response = AgentActionResponse(**data)
        assert response.type == ActionType.BUY
        assert response.extra["desired_item"] == "Food Pack"
        # Check that a default reasoning was provided
        assert "BUY" in response.reasoning
        assert "Food Pack" in response.reasoning

    def test_validation_and_autofill(self):
        """Test that we validate required action-specific fields and autofill where possible"""
        # Response with invalid action type
        with pytest.raises(ValidationError):
            AgentActionResponse(type="INVALID_TYPE", extra={})
            
        # Response with missing required fields for OFFER
        with pytest.raises(ValidationError):
            AgentActionResponse(type="OFFER", extra={"what": "10 credits"})
            
        # Response with all required fields for OFFER
        response = AgentActionResponse(
            type="OFFER", 
            extra={
                "what": "10 credits",
                "against_what": "5 water",
                "to_agent_id": "agent123"
            }
        )
        assert response.type == ActionType.OFFER
        
        # Test that reasoning is auto-generated for common actions
        search_job = AgentActionResponse(
            type="SEARCH_JOB", 
            extra={"reason": "My credits are low"}
        )
        assert "search" in search_job.reasoning.lower()
        assert "job" in search_job.reasoning.lower()
        assert "credits" in search_job.reasoning.lower()

    def test_custom_reasoning_from_extras(self):
        """Test that we extract reasoning from extra fields when available"""
        # LLM might include reasoning-like information in extra fields
        response = AgentActionResponse(
            type="SEARCH_JOB", 
            extra={"reason": "My resources are low, and I need a sustainable income source"}
        )
        
        # Check that we used the reason field as part of reasoning
        assert "resources are low" in response.reasoning
        assert "sustainable income" in response.reasoning

        # Test with reason in different fields that LLMs might use
        response2 = AgentActionResponse(
            type="REST", 
            extra={"explanation": "I'm tired and need to recover energy"}
        )
        assert "tired" in response2.reasoning
        assert "recover energy" in response2.reasoning 