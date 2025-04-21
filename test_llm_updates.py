#!/usr/bin/env python
"""
Test script to validate the LLM updates.
This script tests the updated response models with validators and the OllamaClient methods.
"""
import sys

from pydantic import ValidationError

from llm_models import NarrativeResponse, AgentActionResponse
from llm_utils import OllamaClient


def test_narrative_response():
    """Test the NarrativeResponse model with validators"""
    print("Testing NarrativeResponse...")
    
    # Valid response
    valid_data = {
        "title": "Trade Agreement on Mars",
        "description": "Two colonists engaged in a fair trade of water for solar panels. The exchange benefited both parties and strengthened community bonds.",
        "tags": ["trade", "cooperation", "resources"]
    }
    
    try:
        response = NarrativeResponse(**valid_data)
        print(f"✓ Valid response accepted: {response.title}")
    except ValidationError as e:
        print(f"✗ Error with valid data: {e}")
        return False
    
    # Invalid response (too short description)
    invalid_data = {
        "title": "Trade",
        "description": "Short.",
        "tags": ["trade"]
    }
    
    try:
        response = NarrativeResponse(**invalid_data)
        print(f"✗ Invalid response accepted: {response.title}")
        return False
    except ValidationError as e:
        print(f"✓ Validation caught short description")
    
    # Invalid response (prohibited term)
    invalid_data = {
        "title": "Violent Encounter",
        "description": "This narrative contains harmful content that should be flagged.",
        "tags": ["violent", "encounter"]
    }
    
    try:
        response = NarrativeResponse(**invalid_data)
        print(f"✗ Invalid response with prohibited terms accepted")
        return False
    except ValidationError as e:
        print(f"✓ Validation caught prohibited terms")
    
    return True

def test_agent_action_response():
    """Test the AgentActionResponse model with validators"""
    print("\nTesting AgentActionResponse...")
    
    # Valid response (OFFER)
    valid_offer = {
        "type": "OFFER",
        "extra": {
            "what": "10 credits",
            "against_what": "5 water",
            "to_agent_id": "agent123"
        },
        "reasoning": "The agent needs water and has excess credits to trade."
    }
    
    try:
        response = AgentActionResponse(**valid_offer)
        print(f"✓ Valid OFFER accepted: {response.type}")
    except ValidationError as e:
        print(f"✗ Error with valid OFFER: {e}")
        return False
    
    # Valid response (REST)
    valid_rest = {
        "type": "REST",
        "extra": {},
        "reasoning": "The agent needs to recover energy and has no good opportunities."
    }
    
    try:
        response = AgentActionResponse(**valid_rest)
        print(f"✓ Valid REST accepted: {response.type}")
    except ValidationError as e:
        print(f"✗ Error with valid REST: {e}")
        return False
    
    # Invalid response (missing offer details)
    invalid_offer = {
        "type": "OFFER",
        "extra": {
            "what": "10 credits"
            # missing against_what and to_agent_id
        },
        "reasoning": "The agent wants to make an offer."
    }
    
    try:
        response = AgentActionResponse(**invalid_offer)
        print(f"✗ Invalid OFFER (missing fields) accepted")
        return False
    except ValidationError as e:
        print(f"✓ Validation caught missing offer details")
    
    # Invalid response (invalid action type)
    invalid_type = {
        "type": "EXPLODE",
        "extra": {},
        "reasoning": "The agent wants to explode."
    }
    
    try:
        response = AgentActionResponse(**invalid_type)
        print(f"✗ Invalid action type accepted")
        return False
    except ValidationError as e:
        print(f"✓ Validation caught invalid action type")
    
    return True

def test_ollama_client_mock():
    """Test the OllamaClient in mock mode"""
    print("\nTesting OllamaClient (mock mode)...")
    
    client = OllamaClient(
        base_url="http://localhost:11434",
        model_name="nonexistent-model",
        temperature=0.7,
        max_retries=1,
        timeout=5
    )
    
    # Mock a narrative response
    mock_narrative = {
        "title": "Trade Agreement on Mars",
        "description": "Two colonists engaged in a fair trade of water for solar panels. The exchange benefited both parties and strengthened community bonds.",
        "tags": ["trade", "cooperation", "resources"]
    }
    
    # Monkey patch to avoid actual API calls
    client.is_connected = False
    client.generate_structured = lambda **kwargs: NarrativeResponse(**mock_narrative)
    
    try:
        narrative = client.generate_narrative(
            prompt="Generate a narrative about a trade",
            system_prompt="You are a creative narrator."
        )
        print(f"✓ Successfully generated mock narrative: {narrative.title}")
    except Exception as e:
        print(f"✗ Error generating mock narrative: {e}")
        return False
    
    return True

def main():
    """Run all tests and print a summary"""
    tests = [
        test_narrative_response,
        test_agent_action_response,
        test_ollama_client_mock
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n== Test Summary ==")
    print(f"Tests run: {len(tests)}")
    print(f"Tests passed: {sum(results)}")
    print(f"Tests failed: {len(tests) - sum(results)}")
    
    if all(results):
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 