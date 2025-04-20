import requests
import json
import time
import random
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime

import instructor
from openai import OpenAI

from ..models.base import Agent, AgentType, AgentFaction, AgentPersonality, ResourceType, ResourceBalance
from ..models.actions import (
    AgentAction, ActionType, AgentDecision, AgentState, AgentNeighbor,
    Offer, Job, AgentMemoryEntry, MarketItem
)

logger = logging.getLogger(__name__)

class LLMAgentController:
    """Controller for LLM-based agents in the simulation"""
    
    def __init__(
        self, 
        ollama_base_url: str = "http://localhost:11434/v1",
        model_name: str = "gemma:1b",
        timeout: int = 5,
        max_retries: int = 3,
        temperature: float = 0.7
    ):
        """Initialize the LLM agent controller
        
        Args:
            ollama_base_url: Base URL for Ollama API
            model_name: Name of the model to use
            timeout: Timeout for requests in seconds
            max_retries: Maximum number of retries for failed requests
            temperature: Temperature for LLM generation (0.0-1.0)
        """
        self.ollama_base_url = ollama_base_url
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        
        # Initialize OpenAI-compatible client with Instructor
        self.client = instructor.from_openai(
            OpenAI(
                base_url=ollama_base_url,
                api_key="ollama",  # Required but unused
            ),
            mode=instructor.Mode.JSON,
            max_retries=max_retries
        )
        
        # Cache for agent prompts to avoid regenerating between retries
        self._prompt_cache = {}
    
    def _generate_system_prompt(self) -> str:
        """Generate the system prompt for the LLM agent"""
        return """You are an intelligent agent in a simulated cyberpunk Mars economy in the year 2993. You operate with limited information and must make decisions based on your needs, resources, and social context. You're designed to be strategically selfish but capable of cooperation when beneficial.

IMPORTANT INSTRUCTIONS:
1. Analyze your current state and resources
2. Consider your needs and goals
3. Evaluate opportunities and threats
4. Make a decision among the available actions
5. Provide brief reasoning for your decision

Your output MUST be valid JSON matching the specified format. Do not include explanations outside the JSON structure.
"""
    
    def _generate_agent_prompt(self, state: AgentState) -> str:
        """Generate the user prompt for the LLM agent based on its state"""
        # Check if we have a cached prompt for this state
        state_hash = hash(state.model_dump_json())
        if state_hash in self._prompt_cache:
            return self._prompt_cache[state_hash]
        
        # Format resources section
        resources_str = "\n".join([f"- {res_type}: {amount}" for res_type, amount in state.resources.items()])
        
        # Format needs section
        needs_str = "\n".join([f"- {need_type}: {level}/1.0" for need_type, level in state.needs.items()])
        
        # Format neighbors section
        neighbors_str = "\n".join([
            f"- {n.name} (Faction: {n.faction}, Relationship: {n.relationship:.2f})"
            for n in state.neighbors
        ])
        
        # Format incoming offers
        if state.incoming_offers:
            offers_str = "\n".join([
                f"- Offer #{i+1} (ID: {offer.id}): {offer.from_agent_name} offers {offer.offer_amount} {offer.offer_resource_type} "
                f"for {offer.request_amount} {offer.request_resource_type}"
                for i, offer in enumerate(state.incoming_offers)
            ])
        else:
            offers_str = "No current offers"
        
        # Format available jobs
        if state.available_jobs:
            jobs_str = "\n".join([
                f"- Job #{i+1} (ID: {job.id}): {job.title} at {job.employer_name}, paying {job.salary} credits"
                for i, job in enumerate(state.available_jobs)
            ])
        else:
            jobs_str = "No available jobs"
        
        # Format market information
        if state.market_items:
            market_str = "\n".join([
                f"- {item.item_type}: {item.avg_price} credits (Availability: {item.availability:.2f})"
                for item in state.market_items
            ])
        else:
            market_str = "Limited market information"
        
        # Format memory
        memory_str = "\n".join([
            f"- {mem.timestamp}: {mem.content}"
            for mem in state.memory
        ]) if state.memory else "No significant memories"
        
        # Format current job
        job_str = f"{state.current_job.title} at {state.current_job.employer_name} (ID: {state.current_job.id})" if state.current_job else "unemployed"
        
        # Construct the full prompt
        prompt = f"""You are {state.name}, a {state.faction} living on Mars in the year 2993.

## YOUR CURRENT STATE:
Location: {state.location}
Age: {state.age_days} days
Job: {job_str}
Turn: {state.current_turn}/{state.max_turns}

## YOUR RESOURCES:
{resources_str}

## YOUR NEEDS (higher is better):
{needs_str}

## YOUR PERSONALITY:
{', '.join([f"{trait}: {value:.2f}" for trait, value in state.personality.items()])}

## YOUR NEIGHBORS:
{neighbors_str}

## INCOMING OFFERS:
{offers_str}

## AVAILABLE JOBS:
{jobs_str}

## MARKET INFORMATION:
{market_str}

## YOUR RECENT MEMORIES:
{memory_str}

## AVAILABLE ACTIONS:
- REST: Recover energy, do nothing this turn
- OFFER: Make an offer to another agent (specify what you offer and what you want)
- NEGOTIATE: Counter an existing offer with modified terms
- ACCEPT: Accept an existing offer
- REJECT: Reject an existing offer
- SEARCH_JOB: Look for available jobs
- WORK: Work at your current job (if employed)
- BUY: Purchase goods or services
- SELL: Sell goods or services
- MOVE: Move to a new location
- LEARN: Learn a new skill or improve existing ones
- SOCIALIZE: Interact socially with other agents
- INVEST: Invest in assets or projects
- DONATE: Donate to others or public goods
- PRODUCE: Produce goods or services
- CONSUME: Consume goods or services

Think carefully about your current situation and what action would be most beneficial to you.

Respond with a decision in this format:
```json
{
  "type": "ACTION_TYPE",
  "extra": {
    "key1": "value1",
    "key2": "value2"
  },
  "reasoning": "Brief explanation of your decision"
}
```
"""
        
        # Cache the prompt
        self._prompt_cache[state_hash] = prompt
        
        return prompt
    
    def _format_example_decisions(self) -> List[Dict[str, Any]]:
        """Generate example decisions to help guide the LLM"""
        examples = [
            {
                "type": "REST",
                "extra": {},
                "reasoning": "My energy is low (0.2), and I need to recover before taking other actions."
            },
            {
                "type": "OFFER",
                "extra": {
                    "target_agent_id": "agent123",
                    "offer_resource_type": "digital_goods",
                    "offer_amount": 5,
                    "request_resource_type": "credits",
                    "request_amount": 100,
                    "message": "I'm offering premium entertainment software for credits."
                },
                "reasoning": "I have excess digital goods and need credits for food."
            },
            {
                "type": "SEARCH_JOB",
                "extra": {},
                "reasoning": "I'm unemployed and running low on credits. Need steady income."
            },
            {
                "type": "BUY",
                "extra": {
                    "item_type": "food",
                    "quantity": 2,
                    "max_price": 15
                },
                "reasoning": "My hunger is high (0.8), need to buy food before it gets critical."
            },
            {
                "type": "ACCEPT",
                "extra": {
                    "offer_id": "offer456",
                    "message": "This is a fair deal that benefits both of us."
                },
                "reasoning": "The offer gives me resources I need at a good exchange rate."
            }
        ]
        return examples
    
    def _state_to_formatted_messages(self, state: AgentState) -> List[Dict[str, Any]]:
        """Convert agent state to formatted messages for the LLM"""
        # Generate system and user prompts
        system_prompt = self._generate_system_prompt()
        user_prompt = self._generate_agent_prompt(state)
        
        # Build the messages list
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return messages
    
    def get_agent_decision(self, state: AgentState) -> Optional[AgentAction]:
        """Get a decision from the LLM agent based on its current state
        
        Args:
            state: Current state of the agent
            
        Returns:
            An AgentAction representing the agent's decision, or None if the request failed
        """
        messages = self._state_to_formatted_messages(state)
        
        try:
            # Call the LLM using Instructor for structured output
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_model=AgentDecision,
                temperature=self.temperature,
                timeout=self.timeout
            )
            
            # Convert the response to an AgentAction
            return self._decision_to_action(response, state.agent_id)
            
        except Exception as e:
            logger.error(f"Error getting decision for agent {state.agent_id}: {str(e)}")
            
            # Fallback to a random basic action if LLM call fails
            return self._generate_fallback_action(state)
    
    def _decision_to_action(self, decision: AgentDecision, agent_id: str) -> AgentAction:
        """Convert an AgentDecision to an AgentAction
        
        Args:
            decision: The decision from the LLM
            agent_id: ID of the agent making the decision
            
        Returns:
            An AgentAction representing the agent's decision
        """
        # Create the base action
        action = AgentAction(
            agent_id=agent_id,
            action_type=decision.type,
            timestamp=datetime.now(),
            reasoning=decision.reasoning
        )
        
        # Add action-specific data based on the decision type
        extra = decision.extra or {}
        
        if decision.type == ActionType.REST:
            action.rest_data = extra
        elif decision.type == ActionType.OFFER:
            action.offer_data = extra
        elif decision.type == ActionType.NEGOTIATE:
            action.negotiate_data = extra
        elif decision.type == ActionType.ACCEPT:
            action.accept_data = extra
        elif decision.type == ActionType.REJECT:
            action.reject_data = extra
        elif decision.type == ActionType.SEARCH_JOB:
            action.search_job_data = extra
        elif decision.type == ActionType.WORK:
            action.work_data = extra
        elif decision.type == ActionType.BUY:
            action.buy_data = extra
        elif decision.type == ActionType.SELL:
            action.sell_data = extra
        elif decision.type == ActionType.MOVE:
            action.move_data = extra
        elif decision.type == ActionType.LEARN:
            action.learn_data = extra
        elif decision.type == ActionType.SOCIALIZE:
            action.socialize_data = extra
        elif decision.type == ActionType.INVEST:
            action.invest_data = extra
        elif decision.type == ActionType.DONATE:
            action.donate_data = extra
        elif decision.type == ActionType.PRODUCE:
            action.produce_data = extra
        elif decision.type == ActionType.CONSUME:
            action.consume_data = extra
        elif decision.type == ActionType.STEAL:
            action.steal_data = extra
        elif decision.type == ActionType.SABOTAGE:
            action.sabotage_data = extra
        elif decision.type == ActionType.FORM_COALITION:
            action.form_coalition_data = extra
        
        return action
    
    def _generate_fallback_action(self, state: AgentState) -> AgentAction:
        """Generate a fallback action when LLM call fails
        
        Args:
            state: Current state of the agent
            
        Returns:
            A basic AgentAction as fallback
        """
        # For fallback, choose a simple action like REST
        # We could make this more sophisticated based on agent needs
        fallback_action = AgentAction(
            agent_id=state.agent_id,
            action_type=ActionType.REST,
            timestamp=datetime.now(),
            rest_data={},
            reasoning="Fallback action due to decision-making error"
        )
        
        return fallback_action
    
    def prepare_agent_state(self, agent: Agent, simulation_state: Any) -> AgentState:
        """Prepare an AgentState for the LLM based on actual agent and simulation state
        
        Args:
            agent: The agent
            simulation_state: Current state of the simulation
            
        Returns:
            An AgentState ready to be sent to the LLM
        """
        # This would extract relevant information from the simulation state
        # and convert it to an AgentState for the LLM
        # Implementation depends on the specific simulation state structure
        
        # TODO: Implement this method based on the actual simulation state
        # For MVP, we'll just create a dummy state
        state = AgentState(
            agent_id=agent.id,
            name=agent.name,
            faction=agent.faction.value,
            age_days=agent.age_days,
            resources={rb.resource_type.value: rb.amount for rb in agent.resources},
            needs={
                need_type: getattr(agent.needs, need_type) 
                for need_type in ["subsistence", "security", "social", "esteem", "self_actualization"]
            },
            skills=agent.skills,
            current_job=None,  # TODO: Get from simulation state
            location=agent.location,
            neighbors=[],  # TODO: Get from simulation state
            available_jobs=[],  # TODO: Get from simulation state
            incoming_offers=[],  # TODO: Get from simulation state
            outgoing_offers=[],  # TODO: Get from simulation state
            market_items=[],  # TODO: Get from simulation state
            memory=[],  # TODO: Get from simulation state
            personality={
                trait: getattr(agent.personality, trait) 
                for trait in ["cooperativeness", "risk_tolerance", "fairness_preference", 
                             "altruism", "rationality", "long_term_orientation"]
            },
            current_turn=0,  # TODO: Get from simulation state
            max_turns=0,  # TODO: Get from simulation state
            global_economic_indicators={}  # TODO: Get from simulation state
        )
        
        return state

# Factory function to create an LLM agent controller
def create_llm_agent_controller(
    ollama_base_url: str = "http://localhost:11434/v1",
    model_name: str = "gemma:1b",
    timeout: int = 5,
    max_retries: int = 3,
    temperature: float = 0.7
) -> LLMAgentController:
    """Create an LLM agent controller
    
    Args:
        ollama_base_url: Base URL for Ollama API
        model_name: Name of the model to use
        timeout: Timeout for requests in seconds
        max_retries: Maximum number of retries for failed requests
        temperature: Temperature for LLM generation (0.0-1.0)
        
    Returns:
        An LLM agent controller
    """
    return LLMAgentController(
        ollama_base_url=ollama_base_url,
        model_name=model_name,
        timeout=timeout,
        max_retries=max_retries,
        temperature=temperature
    )