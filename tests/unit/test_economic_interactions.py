import pytest
from datetime import datetime
from typing import Dict, List
import random

from models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality, ResourceBalance, 
    ResourceType, EconomicInteraction, EconomicInteractionType, InteractionRole,
    InteractionOutcome
)

from economics.interactions.base import InteractionHandler
from economics.interactions.ultimatum import UltimatumGameHandler
from economics.interactions.trust import TrustGameHandler
from economics.interactions.public_goods import PublicGoodsGameHandler
from economics.interactions.registry import InteractionRegistry

# Set a fixed seed for reproducibility
random.seed(42)

@pytest.fixture
def agent_factory():
    """Factory for creating test agents"""
    def _factory(name, credits=100.0):
        agent = Agent(
            name=name,
            agent_type=AgentType.INDIVIDUAL,
            faction=AgentFaction.MARS_NATIVE,
            personality=AgentPersonality(
                cooperativeness=0.7,
                risk_tolerance=0.5,
                fairness_preference=0.6,
                altruism=0.4,
                rationality=0.8,
                long_term_orientation=0.6
            ),
            resources=[
                ResourceBalance(
                    resource_type=ResourceType.CREDITS,
                    amount=credits
                )
            ]
        )
        return agent
    return _factory

@pytest.fixture
def interaction_registry():
    """Create an interaction registry for testing"""
    return InteractionRegistry()

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
        print(f"Proposer outcome: {proposer_outcome}")
        print(f"Responder outcome: {responder_outcome}")

        # Proposer should have gained only 5.0 (keeping 5.0 of the 10.0)
        assert proposer_outcome.utility_change == 5.0
        
        # Responder should have gained 5.0
        assert responder_outcome.utility_change == 5.0
    
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

        proposer_outcome = next(o for o in result.outcomes if o.agent_id == agent_proposer.id)
        responder_outcome = next(o for o in result.outcomes if o.agent_id == agent_responder.id)
        print(f"Proposer outcome: {proposer_outcome}")
        print(f"Responder outcome: {responder_outcome}")


        # Check that resources were not transferred
        assert proposer_outcome.resources_after[0].amount == 0
        
        assert responder_outcome.resources_after[0].amount == 0


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
        print(f"Investor outcome: {investor_outcome}")
        print(f"Trustee outcome: {trustee_outcome}")

        # Investor should have: initial - investment + return = 100 - 10 + 15 = 105
        assert investor_outcome.resources_after[0].amount == - 10.0 + 15.0
        
        trustee_after = trustee_outcome.resources_after[0].amount - trustee_outcome.resources_before[0].amount
        # Trustee should have: initial + (investment * multiplier) - return = 50 + (10 * 3) - 15 = 65
        assert trustee_after == (10.0 * 3.0) - 15.0
    
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

        investor_outcome = next(o for o in result.outcomes if o.agent_id == agent_proposer.id)
        trustee_outcome = next(o for o in result.outcomes if o.agent_id == agent_responder.id)
        print(f"Investor outcome: {investor_outcome}")
        print(f"Trustee outcome: {trustee_outcome}")

        # Investor should have lost their investment
        investor_after = investor_outcome.resources_after[0].amount - investor_outcome.resources_before[0].amount
        print(f"Investor after: {investor_after}")
        print(f"Outcomes: {result.outcomes}")
        assert investor_after == investor_initial - 10.0
        
        # Trustee should have gained the multiplied investment
        trustee_after = trustee_outcome.resources_after[0].amount - trustee_outcome.resources_before[0].amount
        assert trustee_after == trustee_initial + (10.0 * 3.0)

def test_ultimatum_game_updates_resources(agent_factory, interaction_registry):
    """Test that the UltimatumGameHandler properly updates agent resources"""
    # Create agents
    proposer = agent_factory("Proposer", 100.0)
    responder = agent_factory("Responder", 50.0)
    
    # Initial resource check
    assert proposer.resources[0].amount == 100.0
    assert responder.resources[0].amount == 50.0
    
    # Create and process an Ultimatum Game interaction
    handler = UltimatumGameHandler()
    
    # Create interaction with a total amount of 20 credits
    interaction = handler.create_interaction(
        proposer=proposer,
        responder=responder,
        total_amount=20.0
    )
    
    # Check that interaction was created correctly
    assert interaction.interaction_type == EconomicInteractionType.ULTIMATUM
    assert len(interaction.participants) == 2
    assert proposer in interaction.participants
    assert responder in interaction.participants
    assert interaction.participants[proposer] == InteractionRole.PROPOSER
    assert interaction.participants[responder] == InteractionRole.RESPONDER
    
    # Process proposal stage
    interaction = handler.progress_interaction(interaction)
    
    # The proposed amount should be set
    assert interaction.parameters.get("proposed_amount") is not None
    assert interaction.parameters.get("stage") == "response"
    
    # Process response stage
    interaction = handler.progress_interaction(interaction)
    
    # Check that interaction is complete
    assert interaction.is_complete
    assert interaction.parameters.get("stage") == "completed"
    assert interaction.end_time is not None
    
    # Check that outcomes were calculated
    assert len(interaction.outcomes) == 2
    
    # Find proposer and responder outcomes
    proposer_outcome = next(o for o in interaction.outcomes if o.agent == proposer)
    responder_outcome = next(o for o in interaction.outcomes if o.agent == responder)
    
    # Check resource updates
    acceptance = interaction.parameters.get("response")
    proposed_amount = interaction.parameters.get("proposed_amount")
    
    if acceptance:
        # If accepted, proposer should have 100 - 20 + (20 - proposed_amount)
        expected_proposer_amount = 100.0 - proposed_amount
        # Responder gets the proposed amount
        expected_responder_amount = 50.0 + proposed_amount
    else:
        # If rejected, proposer keeps their original amount
        expected_proposer_amount = 100.0
        # Responder keeps their original amount
        expected_responder_amount = 50.0
    
    # Check actual resource amounts
    assert pytest.approx(proposer.resources[0].amount) == expected_proposer_amount
    assert pytest.approx(responder.resources[0].amount) == expected_responder_amount

def test_trust_game_updates_resources(agent_factory, interaction_registry):
    """Test that the TrustGameHandler properly updates agent resources"""
    # Create agents
    investor = agent_factory("Investor", 100.0)
    trustee = agent_factory("Trustee", 50.0)
    
    # Initial resource check
    assert investor.resources[0].amount == 100.0
    assert trustee.resources[0].amount == 50.0
    
    # Create a Trust Game interaction
    handler = TrustGameHandler()
    
    # Create interaction with an initial amount of 30 credits and multiplier of 3
    interaction = handler.create_interaction(
        investor=investor,
        trustee=trustee,
        initial_amount=30.0,
        multiplier=3.0
    )
    
    # Check that interaction was created correctly
    assert interaction.interaction_type == EconomicInteractionType.TRUST
    assert len(interaction.participants) == 2
    assert investor in interaction.participants
    assert trustee in interaction.participants
    assert interaction.participants[investor] == InteractionRole.INVESTOR
    assert interaction.participants[trustee] == InteractionRole.TRUSTEE
    
    # Process investment stage
    interaction = handler.progress_interaction(interaction)
    
    # The invested amount and multiplied amount should be set
    invested_amount = interaction.parameters.get("invested_amount")
    multiplied_amount = interaction.parameters.get("multiplied_amount")
    assert invested_amount is not None
    assert multiplied_amount is not None
    assert pytest.approx(multiplied_amount) == invested_amount * 3.0
    assert interaction.parameters.get("stage") == "return"
    
    # Process return stage
    interaction = handler.progress_interaction(interaction)
    
    # Check that interaction is complete
    assert interaction.is_complete
    assert interaction.parameters.get("stage") == "completed"
    assert interaction.end_time is not None
    
    # Check that outcomes were calculated
    assert len(interaction.outcomes) == 2
    
    # Find investor and trustee outcomes
    investor_outcome = next(o for o in interaction.outcomes if o.agent == investor)
    trustee_outcome = next(o for o in interaction.outcomes if o.agent == trustee)
    
    # Check resource updates
    returned_amount = interaction.parameters.get("returned_amount")
    
    # Investor should have 100 - invested_amount + returned_amount
    expected_investor_amount = 100.0 - invested_amount + returned_amount
    # Trustee gets multiplied_amount - returned_amount
    expected_trustee_amount = 50.0 + multiplied_amount - returned_amount
    
    # Check actual resource amounts
    assert pytest.approx(investor.resources[0].amount) == expected_investor_amount
    assert pytest.approx(trustee.resources[0].amount) == expected_trustee_amount

def test_public_goods_game_updates_resources(agent_factory, interaction_registry):
    """Test that the PublicGoodsGameHandler properly updates agent resources"""
    # Create agents
    agents = [agent_factory(f"Agent_{i}", 100.0) for i in range(5)]
    
    # Initial resource check
    for agent in agents:
        assert agent.resources[0].amount == 100.0
    
    # Create a Public Goods Game interaction
    handler = PublicGoodsGameHandler()
    
    # Create interaction with an endowment of 20 credits and multiplier of 1.6
    interaction = handler.create_interaction(
        participants=agents,
        endowment=20.0,
        multiplier=1.6
    )
    
    # Check that interaction was created correctly
    assert interaction.interaction_type == EconomicInteractionType.PUBLIC_GOODS
    assert len(interaction.participants) == 5
    for agent in agents:
        assert agent in interaction.participants
        assert interaction.participants[agent] == InteractionRole.CONTRIBUTOR
    
    # Process contribution stage (completes the interaction)
    interaction = handler.progress_interaction(interaction)
    
    # Check that interaction is complete
    assert interaction.is_complete
    assert interaction.parameters.get("stage") == "completed"
    
    # Get contributions
    contributions = interaction.parameters.get("contributions", {})
    assert len(contributions) == 5
    
    # Calculate expected returns
    total_contribution = sum(contributions.values())
    total_return = total_contribution * interaction.parameters.get("multiplier")
    per_agent_return = total_return / len(agents)
    
    # Check resource updates for each agent
    for agent in agents:
        contribution = contributions.get(agent, 0)
        expected_amount = 100.0 - contribution + per_agent_return
        assert pytest.approx(agent.resources[0].amount) == expected_amount
        
        # Find agent's outcome
        outcome = next(o for o in interaction.outcomes if o.agent == agent)
        assert outcome.utility_change == expected_amount - 100.0

def test_interaction_registry_process_interaction(agent_factory, interaction_registry):
    """Test that the InteractionRegistry correctly processes interactions"""
    # Create agents
    proposer = agent_factory("Proposer", 100.0)
    responder = agent_factory("Responder", 50.0)
    
    # Create an Ultimatum Game interaction
    interaction = interaction_registry.create_interaction(
        interaction_type=EconomicInteractionType.ULTIMATUM,
        proposer=proposer,
        responder=responder,
        total_amount=20.0
    )
    
    # Process the interaction to completion
    updated_interaction = interaction_registry.process_interaction(interaction)
    
    # Check that we're in the response stage
    assert updated_interaction.parameters.get("stage") == "response"
    assert not updated_interaction.is_complete
    
    # Process again to complete
    final_interaction = interaction_registry.process_interaction(updated_interaction)
    
    # Check that the interaction is complete
    assert final_interaction.is_complete
    assert final_interaction.end_time is not None
    
    # Check that resources were updated
    acceptance = final_interaction.parameters.get("response")
    proposed_amount = final_interaction.parameters.get("proposed_amount")
    
    if acceptance:
        # If accepted, proposer should have lost the proposed amount
        assert proposer.resources[0].amount < 100.0
        # Responder should have gained the proposed amount
        assert responder.resources[0].amount > 50.0
    else:
        # If rejected, resources should remain unchanged
        assert proposer.resources[0].amount == 100.0
        assert responder.resources[0].amount == 50.0 