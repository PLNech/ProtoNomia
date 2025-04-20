import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from ..models.base import (
    Agent, AgentType, AgentFaction, AgentPersonality, AgentNeeds,
    ResourceType, ResourceBalance
)

logger = logging.getLogger(__name__)

class AgentLifecycleManager:
    """Manages the lifecycle of agents, including needs, consumption, and aging"""
    
    def __init__(self, resource_scarcity: float = 0.5):
        """Initialize the agent lifecycle manager
        
        Args:
            resource_scarcity: Resource scarcity level (0.0-1.0) affecting consumption rates
        """
        self.resource_scarcity = resource_scarcity
    
    def update_agent_lifecycle(
        self, 
        agent: Agent, 
        current_date: datetime,
        time_delta: timedelta
    ) -> Tuple[bool, Dict[str, Any]]:
        """Update an agent's lifecycle for a time step
        
        Args:
            agent: The agent to update
            current_date: Current simulation date
            time_delta: Time passed since last update
            
        Returns:
            Tuple of (is_agent_alive, lifecycle_changes)
        """
        if not agent.is_alive:
            return False, {}
        
        # Update agent age
        agent.age_days = agent.calculate_age(current_date)
        
        # Update needs
        needs_changes = self._update_agent_needs(agent, time_delta)
        
        # Consume resources
        resource_changes = self._consume_resources(agent, time_delta)
        
        # Check for survival
        survival_check = self._check_health(agent)
        
        # Combine changes
        lifecycle_changes = {
            "needs_changes": needs_changes,
            "resource_changes": resource_changes,
            "survival_check": survival_check
        }
        
        return agent.is_alive, lifecycle_changes
    
    def _update_agent_needs(self, agent: Agent, time_delta: timedelta) -> Dict[str, float]:
        """Update an agent's needs based on time passage and state
        
        Args:
            agent: The agent to update
            time_delta: Time passed since last update
            
        Returns:
            Dictionary of need -> change amount
        """
        # Calculate base decay rate (per hour)
        hours_passed = time_delta.total_seconds() / 3600
        base_decay = 0.01 * hours_passed  # 1% per hour
        
        # Adjust for resource scarcity - higher scarcity means faster decay
        scarcity_factor = 1.0 + self.resource_scarcity
        
        # Store needs changes for return
        needs_changes = {}
        
        # Subsistence need (food, rest, etc.)
        subsistence_decay = base_decay * scarcity_factor * random.uniform(0.8, 1.2)
        old_subsistence = agent.needs.subsistence
        agent.needs.subsistence = max(0, agent.needs.subsistence - subsistence_decay)
        needs_changes["subsistence"] = agent.needs.subsistence - old_subsistence
        
        # Security need
        security_decay = base_decay * random.uniform(0.7, 1.1)
        # Decay faster if in risky situations
        if agent.faction == AgentFaction.UNDERGROUND or agent.needs.subsistence < 0.3:
            security_decay *= 1.5
        
        old_security = agent.needs.security
        agent.needs.security = max(0, agent.needs.security - security_decay)
        needs_changes["security"] = agent.needs.security - old_security
        
        # Social need
        social_decay = base_decay * random.uniform(0.8, 1.2)
        # Slower decay if agent has recent social interactions
        # This would be implemented with actual tracking of social interactions
        # For MVP, just use a random factor
        if random.random() < 0.2:  # Simulated chance of recent social interaction
            social_decay *= 0.5
        
        old_social = agent.needs.social
        agent.needs.social = max(0, agent.needs.social - social_decay)
        needs_changes["social"] = agent.needs.social - old_social
        
        # Esteem need
        esteem_decay = base_decay * 0.8 * random.uniform(0.7, 1.1)
        # Slower decay for high-status agents
        if agent.agent_type in [AgentType.CORPORATION, AgentType.GOVERNMENT]:
            esteem_decay *= 0.7
        
        old_esteem = agent.needs.esteem
        agent.needs.esteem = max(0, agent.needs.esteem - esteem_decay)
        needs_changes["esteem"] = agent.needs.esteem - old_esteem
        
        # Self-actualization need
        actualization_decay = base_decay * 0.5 * random.uniform(0.7, 1.0)
        # Slower decay if learning or creating
        # This would be implemented with actual tracking of activities
        # For MVP, just use a random factor
        if random.random() < 0.3:  # Simulated chance of learning/creating
            actualization_decay *= 0.6
        
        old_actualization = agent.needs.self_actualization
        agent.needs.self_actualization = max(0, agent.needs.self_actualization - actualization_decay)
        needs_changes["self_actualization"] = agent.needs.self_actualization - old_actualization
        
        return needs_changes
    
    def _consume_resources(self, agent: Agent, time_delta: timedelta) -> Dict[str, float]:
        """Have agents consume resources to maintain themselves
        
        Args:
            agent: The agent to update
            time_delta: Time passed since last update
            
        Returns:
            Dictionary of resource_type -> change amount
        """
        # Calculate consumption based on time
        hours_passed = time_delta.total_seconds() / 3600
        
        # Adjust for resource scarcity
        scarcity_factor = 1.0 + (self.resource_scarcity * 0.5)  # 1.0-1.5x multiplier
        
        # Different agent types have different consumption rates
        type_factor = {
            AgentType.INDIVIDUAL: 1.0,
            AgentType.CORPORATION: 2.5,
            AgentType.COLLECTIVE: 1.8,
            AgentType.GOVERNMENT: 2.2,
            AgentType.AI: 0.5
        }.get(agent.agent_type, 1.0)
        
        # Store resource changes
        resource_changes = {}
        
        # Consume oxygen
        oxygen_consumption_rate = 1.0 * hours_passed * type_factor  # Base units per hour
        oxygen_resource = next((r for r in agent.resources if r.resource_type == ResourceType.OXYGEN), None)
        
        if oxygen_resource:
            old_oxygen = oxygen_resource.amount
            oxygen_resource.amount = max(0, oxygen_resource.amount - oxygen_consumption_rate)
            oxygen_resource.last_updated = datetime.now()
            resource_changes["oxygen"] = oxygen_resource.amount - old_oxygen
        
        # Consume water
        water_consumption_rate = 0.8 * hours_passed * type_factor  # Base units per hour
        water_resource = next((r for r in agent.resources if r.resource_type == ResourceType.WATER), None)
        
        if water_resource:
            old_water = water_resource.amount
            water_resource.amount = max(0, water_resource.amount - water_consumption_rate)
            water_resource.last_updated = datetime.now()
            resource_changes["water"] = water_resource.amount - old_water
        
        # Consume energy (corporations and governments consume more)
        energy_consumption_rate = 0.5 * hours_passed * type_factor * scarcity_factor
        energy_resource = next((r for r in agent.resources if r.resource_type == ResourceType.ENERGY), None)
        
        if energy_resource:
            old_energy = energy_resource.amount
            energy_resource.amount = max(0, energy_resource.amount - energy_consumption_rate)
            energy_resource.last_updated = datetime.now()
            resource_changes["energy"] = energy_resource.amount - old_energy
        
        # Consume credits for maintenance
        credit_consumption_rate = 0.3 * hours_passed * type_factor * scarcity_factor
        credit_resource = next((r for r in agent.resources if r.resource_type == ResourceType.CREDITS), None)
        
        if credit_resource:
            old_credits = credit_resource.amount
            credit_resource.amount = max(0, credit_resource.amount - credit_consumption_rate)
            credit_resource.last_updated = datetime.now()
            resource_changes["credits"] = credit_resource.amount - old_credits
        
        return resource_changes
    
    def _check_health(self, agent: Agent) -> Dict[str, Any]:
        """Check an agent's health and update state accordingly
        
        Args:
            agent: The agent to check
            
        Returns:
            Dictionary of health check results
        """
        health_issues = []
        
        # Check critical resources
        oxygen = next((r.amount for r in agent.resources if r.resource_type == ResourceType.OXYGEN), 0)
        water = next((r.amount for r in agent.resources if r.resource_type == ResourceType.WATER), 0)
        
        if oxygen <= 0:
            agent.is_alive = False
            agent.death_date = datetime.now()
            health_issues.append("Oxygen depletion")
        
        if water <= 0:
            agent.is_alive = False
            agent.death_date = datetime.now()
            health_issues.append("Water depletion")
        
        # Check critical needs
        if agent.needs.subsistence <= 0:
            agent.is_alive = False
            agent.death_date = datetime.now()
            health_issues.append("Starvation/exhaustion")
        
        # Check for critical health impact from low resources
        if oxygen < 5 and agent.is_alive:
            # Critical oxygen shortage - reduce subsistence quickly
            agent.needs.subsistence = max(0, agent.needs.subsistence - 0.2)
            health_issues.append("Critical oxygen shortage")
        
        if water < 5 and agent.is_alive:
            # Critical water shortage - reduce subsistence
            agent.needs.subsistence = max(0, agent.needs.subsistence - 0.15)
            health_issues.append("Critical water shortage")
        
        # Check for health impact from low needs
        if agent.needs.subsistence < 0.2 and agent.is_alive:
            # Critical subsistence - chance of illness
            if random.random() < 0.1:
                agent.is_alive = False
                agent.death_date = datetime.now()
                health_issues.append("Health failure due to chronic need deprivation")
        
        health_status = "healthy"
        if health_issues:
            if agent.is_alive:
                if len(health_issues) > 1:
                    health_status = "critical"
                else:
                    health_status = "poor"
            else:
                health_status = "deceased"
        
        return {
            "status": health_status,
            "issues": health_issues,
            "is_alive": agent.is_alive
        }
    
    def restore_needs(self, agent: Agent, need_type: str, amount: float) -> float:
        """Restore an agent's specific need
        
        Args:
            agent: The agent to update
            need_type: Type of need to restore
            amount: Amount to restore
            
        Returns:
            Actual amount restored
        """
        if not agent.is_alive:
            return 0.0
        
        if need_type == "subsistence":
            old_value = agent.needs.subsistence
            agent.needs.subsistence = min(1.0, agent.needs.subsistence + amount)
            return agent.needs.subsistence - old_value
        elif need_type == "security":
            old_value = agent.needs.security
            agent.needs.security = min(1.0, agent.needs.security + amount)
            return agent.needs.security - old_value
        elif need_type == "social":
            old_value = agent.needs.social
            agent.needs.social = min(1.0, agent.needs.social + amount)
            return agent.needs.social - old_value
        elif need_type == "esteem":
            old_value = agent.needs.esteem
            agent.needs.esteem = min(1.0, agent.needs.esteem + amount)
            return agent.needs.esteem - old_value
        elif need_type == "self_actualization":
            old_value = agent.needs.self_actualization
            agent.needs.self_actualization = min(1.0, agent.needs.self_actualization + amount)
            return agent.needs.self_actualization - old_value
        else:
            logger.warning(f"Unknown need type: {need_type}")
            return 0.0
    
    def get_agent_health_summary(self, agent: Agent) -> Dict[str, Any]:
        """Get a summary of an agent's health/needs status
        
        Args:
            agent: The agent to summarize
            
        Returns:
            Dictionary of health/needs status
        """
        # Check resource levels
        resource_levels = {}
        for resource_type in [ResourceType.OXYGEN, ResourceType.WATER, ResourceType.ENERGY, ResourceType.CREDITS]:
            resource = next((r for r in agent.resources if r.resource_type == resource_type), None)
            if resource:
                if resource.amount <= 0:
                    resource_levels[resource_type.value] = "depleted"
                elif resource.amount < 10:
                    resource_levels[resource_type.value] = "critical"
                elif resource.amount < 30:
                    resource_levels[resource_type.value] = "low"
                else:
                    resource_levels[resource_type.value] = "sufficient"
            else:
                resource_levels[resource_type.value] = "unknown"
        
        # Check need levels
        need_levels = {}
        for need_name in ["subsistence", "security", "social", "esteem", "self_actualization"]:
            need_value = getattr(agent.needs, need_name, 0)
            if need_value <= 0:
                need_levels[need_name] = "depleted"
            elif need_value < 0.2:
                need_levels[need_name] = "critical"
            elif need_value < 0.5:
                need_levels[need_name] = "low"
            elif need_value < 0.8:
                need_levels[need_name] = "adequate"
            else:
                need_levels[need_name] = "high"
        
        # Determine overall health status
        if not agent.is_alive:
            health_status = "deceased"
        elif "depleted" in resource_levels.values() or "depleted" in need_levels.values():
            health_status = "critical"
        elif "critical" in resource_levels.values() or "critical" in need_levels.values():
            health_status = "poor"
        elif "low" in resource_levels.values() or "low" in need_levels.values():
            health_status = "fair"
        else:
            health_status = "good"
        
        return {
            "health_status": health_status,
            "resource_levels": resource_levels,
            "need_levels": need_levels,
            "is_alive": agent.is_alive,
            "age_days": agent.age_days
        }