import pytest
from datetime import datetime
from typing import Dict, List

from models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality, ResourceBalance, 
    ResourceType, EconomicInteraction, EconomicInteractionType, InteractionRole,
    InteractionOutcome
)

# We'll need to check if the economic interaction handlers exist
try:
    from economics.interactions.trust import TrustGameHandler
    from economics.interactions.ultimatum import UltimatumGameHandler
    HANDLERS_EXIST = True
except ImportError:
    HANDLERS_EXIST = False


@pytest.fixture
def agent_proposer():
    """Create a standard proposer agent for tests"""
    return Agent(
        name="Proposer",
        agent_type=AgentType.INDIVIDUAL,
        faction=AgentFaction.MARS_NATIVE,
        personality=AgentPersonality(
            cooperativeness=0.7,
            risk_tolerance=0.6,
            fairness_preference=0.5,
            altruism=0.3,
            rationality=0.8,
            long_term_orientation=0.7
        ),
        resources=[
            ResourceBalance(
                resource_type=ResourceType.CREDITS,
                amount=100.0
            )
        ]
    )


@pytest.fixture
def agent_responder():
    """Create a standard responder agent for tests"""
    return Agent(
        name="Responder",
        agent_type=AgentType.INDIVIDUAL,
        faction=AgentFaction.INDEPENDENT,
        personality=AgentPersonality(
            cooperativeness=0.6,
            risk_tolerance=0.4,
            fairness_preference=0.8,
            altruism=0.5,
            rationality=0.7,
            long_term_orientation=0.6
        ),
        resources=[
            ResourceBalance(
                resource_type=ResourceType.CREDITS,
                amount=50.0
            )
        ]
    )


@pytest.mark.skipif(not HANDLERS_EXIST, reason="Economic interaction handlers not implemented yet")
class TestUltimatumGame:
    """Tests for the Ultimatum Game economic interaction"""
    
    def test_create_ultimatum_game(self, agent_proposer, agent_responder):
        """Test that an Ultimatum Game interaction can be created"""
        # Create the interaction
        interaction = EconomicInteraction(
            interaction_type=EconomicInteractionType.ULTIMATUM,
            participants={
                agent_proposer.id: InteractionRole.PROPOSER,
                agent_responder.id: InteractionRole.RESPONDER
            },
            parameters={
                "total_amount": 10.0,
                "currency": ResourceType.CREDITS
            }
        )
        
        # Check interaction properties
        assert interaction.interaction_type == EconomicInteractionType.ULTIMATUM
        assert len(interaction.participants) == 2
        assert interaction.is_complete == False
        assert interaction.parameters["total_amount"] == 10.0
    
    def test_ultimatum_game_accept(self, agent_proposer, agent_responder):
        """Test a successful Ultimatum Game where responder accepts"""
        handler = UltimatumGameHandler()
        
        # Setup initial resources
        proposer_initial = 100.0
        responder_initial = 50.0
        
        # Create and execute the interaction with offer accepted
        result = handler.execute(
            proposer=agent_proposer,
            responder=agent_responder,
            total_amount=10.0,
            offer_amount=5.0,  # Offering half (fair)
            responder_accepts=True
        )
        
        # Verify the interaction
        assert result.is_complete == True
        assert len(result.outcomes) == 2
        
        # Check that resources were transferred correctly
        proposer_outcome = next(o for o in result.outcomes if o.agent_id == agent_proposer.id)
        responder_outcome = next(o for o in result.outcomes if o.agent_id == agent_responder.id)
        
        # Proposer should have lost 5.0 (keeping 5.0 of the 10.0)
        proposer_after = next(r.amount for r in agent_proposer.resources if r.resource_type == ResourceType.CREDITS)
        assert proposer_after == proposer_initial - 5.0
        
        # Responder should have gained 5.0
        responder_after = next(r.amount for r in agent_responder.resources if r.resource_type == ResourceType.CREDITS)
        assert responder_after == responder_initial + 5.0
    
    def test_ultimatum_game_reject(self, agent_proposer, agent_responder):
        """Test an Ultimatum Game where responder rejects the offer"""
        handler = UltimatumGameHandler()
        
        # Setup initial resources
        proposer_initial = 100.0
        responder_initial = 50.0
        
        # Create and execute the interaction with offer rejected
        result = handler.execute(
            proposer=agent_proposer,
            responder=agent_responder,
            total_amount=10.0,
            offer_amount=1.0,  # Offering only 1.0 (unfair)
            responder_accepts=False
        )
        
        # Verify the interaction
        assert result.is_complete == True
        assert len(result.outcomes) == 2
        
        # Check that resources were not transferred
        proposer_after = next(r.amount for r in agent_proposer.resources if r.resource_type == ResourceType.CREDITS)
        assert proposer_after == proposer_initial
        
        responder_after = next(r.amount for r in agent_responder.resources if r.resource_type == ResourceType.CREDITS)
        assert responder_after == responder_initial


@pytest.mark.skipif(not HANDLERS_EXIST, reason="Economic interaction handlers not implemented yet")
class TestTrustGame:
    """Tests for the Trust Game economic interaction"""
    
    def test_create_trust_game(self, agent_proposer, agent_responder):
        """Test that a Trust Game interaction can be created"""
        # Create the interaction
        interaction = EconomicInteraction(
            interaction_type=EconomicInteractionType.TRUST,
            participants={
                agent_proposer.id: InteractionRole.INVESTOR,
                agent_responder.id: InteractionRole.TRUSTEE
            },
            parameters={
                "investment_amount": 5.0,
                "multiplier": 3.0,
                "currency": ResourceType.CREDITS
            }
        )
        
        # Check interaction properties
        assert interaction.interaction_type == EconomicInteractionType.TRUST
        assert len(interaction.participants) == 2
        assert interaction.is_complete == False
        assert interaction.parameters["investment_amount"] == 5.0
        assert interaction.parameters["multiplier"] == 3.0
    
    def test_trust_game_reciprocate(self, agent_proposer, agent_responder):
        """Test a Trust Game where trustee reciprocates"""
        handler = TrustGameHandler()
        
        # Setup initial resources
        investor_initial = 100.0
        trustee_initial = 50.0
        
        # Create and execute the interaction with trustee reciprocating
        result = handler.execute(
            investor=agent_proposer,
            trustee=agent_responder,
            investment_amount=10.0,
            multiplier=3.0,
            return_amount=15.0  # Returning half of the multiplied amount
        )
        
        # Verify the interaction
        assert result.is_complete == True
        assert len(result.outcomes) == 2
        
        # Check that resources were transferred correctly
        investor_outcome = next(o for o in result.outcomes if o.agent_id == agent_proposer.id)
        trustee_outcome = next(o for o in result.outcomes if o.agent_id == agent_responder.id)
        
        # Investor should have: initial - investment + return = 100 - 10 + 15 = 105
        investor_after = next(r.amount for r in agent_proposer.resources if r.resource_type == ResourceType.CREDITS)
        assert investor_after == investor_initial - 10.0 + 15.0
        
        # Trustee should have: initial + (investment * multiplier) - return = 50 + (10 * 3) - 15 = 65
        trustee_after = next(r.amount for r in agent_responder.resources if r.resource_type == ResourceType.CREDITS)
        assert trustee_after == trustee_initial + (10.0 * 3.0) - 15.0
    
    def test_trust_game_no_reciprocation(self, agent_proposer, agent_responder):
        """Test a Trust Game where trustee doesn't reciprocate"""
        handler = TrustGameHandler()
        
        # Setup initial resources
        investor_initial = 100.0
        trustee_initial = 50.0
        
        # Create and execute the interaction with trustee not reciprocating
        result = handler.execute(
            investor=agent_proposer,
            trustee=agent_responder,
            investment_amount=10.0,
            multiplier=3.0,
            return_amount=0.0  # Returning nothing (defection)
        )
        
        # Verify the interaction
        assert result.is_complete == True
        assert len(result.outcomes) == 2
        
        # Investor should have lost their investment
        investor_after = next(r.amount for r in agent_proposer.resources if r.resource_type == ResourceType.CREDITS)
        assert investor_after == investor_initial - 10.0
        
        # Trustee should have gained the multiplied investment
        trustee_after = next(r.amount for r in agent_responder.resources if r.resource_type == ResourceType.CREDITS)
        assert trustee_after == trustee_initial + (10.0 * 3.0) 