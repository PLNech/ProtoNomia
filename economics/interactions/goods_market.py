"""
Goods market interaction handler for ProtoNomia.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import random

from models.base import (
    Agent, EconomicInteraction, InteractionRole,
    InteractionOutcome, InteractionStrategy, ResourceBalance, ResourceType, ActionType
)
from economics.interactions.base import InteractionHandler
from models.economy import GoodsListing

logger = logging.getLogger(__name__)

class GoodsMarketHandler(InteractionHandler):
    """Handler for goods market interactions"""
    
    interaction_type = ActionType.GOODS_PURCHASE
    
    def create_interaction(self, **kwargs) -> EconomicInteraction:
        """Create a new goods purchase interaction
        
        Args:
            seller: The seller agent
            buyer: The buyer agent
            goods_listing: The goods listing being purchased
            purchase_amount: The amount being purchased
            
        Returns:
            A new goods purchase interaction
        """
        seller = kwargs.get("seller")
        buyer = kwargs.get("buyer")
        goods_listing = kwargs.get("goods_listing")
        purchase_amount = kwargs.get("purchase_amount", 1.0)
        
        if not seller or not buyer or not goods_listing:
            raise ValueError("Seller, buyer, and goods_listing are required")
        
        # TODO: Consider reputation and other factors resulting in rejecting purchases

        # Ensure purchase amount is valid
        available_amount = goods_listing.amount
        if purchase_amount <= 0 or purchase_amount > available_amount:
            purchase_amount = min(available_amount, 1.0)
        
        # TODO: Consider reputation and other factors in pricing

        # Calculate total price
        price_per_unit = goods_listing.price_per_unit
        total_price = price_per_unit * purchase_amount
        
        # Create the interaction
        interaction = EconomicInteraction(
            interaction_type=self.interaction_type,
            participants={
                seller: InteractionRole.SELLER,
                buyer: InteractionRole.BUYER
            },
            parameters={
                "goods_id": goods_listing.id,
                "resource_type": goods_listing.resource_type,
                "purchase_amount": purchase_amount,
                "price_per_unit": price_per_unit,
                "total_price": total_price,
                "stage": "purchase",
                "purchase_successful": None
            },
            narrative_significance=random.uniform(0.2, 0.6)  # Mid-to-low range significance
        )
        
        return interaction
    
    def progress_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Progress a goods purchase interaction
        
        Args:
            interaction: The interaction to progress
            
        Returns:
            The updated interaction
        """
        # Check stage
        stage = interaction.parameters.get("stage")
        
        if stage == "purchase":
            # Get buyer and check if they have enough resources
            buyer = None
            for agent, role in interaction.participants.items():
                if role == InteractionRole.BUYER:
                    buyer = agent
                    break
            
            if not buyer:
                interaction.parameters["purchase_successful"] = False
                interaction.parameters["failure_reason"] = "Buyer not found"
                interaction.parameters["stage"] = "complete"
                return self.complete_interaction(interaction)
            
            # Check if buyer has enough credits
            total_price = interaction.parameters.get("total_price", 0)
            has_enough = False
            
            for resource in buyer.resources:
                if resource.resource_type == ResourceType.CREDITS and resource.amount >= total_price:
                    has_enough = True
                    break
            
            # Set success or failure
            interaction.parameters["purchase_successful"] = has_enough
            if not has_enough:
                interaction.parameters["failure_reason"] = "Insufficient funds"
            
            interaction.parameters["stage"] = "complete"
            
            # Complete the interaction
            return self.complete_interaction(interaction)
            
        return interaction
    
    def complete_interaction(self, interaction: EconomicInteraction) -> EconomicInteraction:
        """Complete a goods purchase interaction
        
        Args:
            interaction: The interaction to complete
            
        Returns:
            The completed interaction with outcomes
        """
        # Mark as complete
        interaction.is_complete = True
        interaction.end_time = datetime.now()
        
        # Get seller and buyer
        seller = None
        buyer = None
        
        for agent, role in interaction.participants.items():
            if role == InteractionRole.SELLER:
                seller = agent
            elif role == InteractionRole.BUYER:
                buyer = agent
        
        if not seller or not buyer:
            logger.error("Missing seller or buyer in goods purchase interaction")
            return interaction
        
        # Get interaction parameters
        successful = interaction.parameters.get("purchase_successful", False)
        purchase_amount = interaction.parameters.get("purchase_amount", 0)
        total_price = interaction.parameters.get("total_price", 0)
        resource_type = interaction.parameters.get("resource_type")
        
        if successful:
            # Record resource balances before the transaction
            buyer_credits_before = next((r.amount for r in buyer.resources if r.resource_type == ResourceType.CREDITS), 0)
            buyer_resource_before = next((r.amount for r in buyer.resources if r.resource_type == resource_type), 0)
            
            seller_credits_before = next((r.amount for r in seller.resources if r.resource_type == ResourceType.CREDITS), 0)
            seller_resource_before = next((r.amount for r in seller.resources if r.resource_type == resource_type), 0)
            
            # Transfer resources
            # Buyer loses credits, gains the resource
            buyer_credits = next((r for r in buyer.resources if r.resource_type == ResourceType.CREDITS), None)
            if buyer_credits:
                buyer_credits.amount -= total_price
            
            buyer_resource = next((r for r in buyer.resources if r.resource_type == resource_type), None)
            if buyer_resource:
                buyer_resource.amount += purchase_amount
            else:
                buyer.resources.append(ResourceBalance(
                    resource_type=resource_type,
                    amount=purchase_amount
                ))
            
            # Seller gains credits, loses the resource
            seller_credits = next((r for r in seller.resources if r.resource_type == ResourceType.CREDITS), None)
            if seller_credits:
                seller_credits.amount += total_price
            else:
                seller.resources.append(ResourceBalance(
                    resource_type=ResourceType.CREDITS,
                    amount=total_price
                ))
            
            seller_resource = next((r for r in seller.resources if r.resource_type == resource_type), None)
            if seller_resource:
                seller_resource.amount -= purchase_amount
            
            # Record resource balances after the transaction
            buyer_credits_after = next((r.amount for r in buyer.resources if r.resource_type == ResourceType.CREDITS), 0)
            buyer_resource_after = next((r.amount for r in buyer.resources if r.resource_type == resource_type), 0)
            
            seller_credits_after = next((r.amount for r in seller.resources if r.resource_type == ResourceType.CREDITS), 0)
            seller_resource_after = next((r.amount for r in seller.resources if r.resource_type == resource_type), 0)
            
            # Create outcomes with detailed resource changes
            buyer_outcome = InteractionOutcome(
                interaction_id=interaction.id,
                agent=buyer,
                role=InteractionRole.BUYER,
                resources_before=[
                    ResourceBalance(resource_type=ResourceType.CREDITS, amount=buyer_credits_before),
                    ResourceBalance(resource_type=resource_type, amount=buyer_resource_before)
                ],
                resources_after=[
                    ResourceBalance(resource_type=ResourceType.CREDITS, amount=buyer_credits_after),
                    ResourceBalance(resource_type=resource_type, amount=buyer_resource_after)
                ],
                utility_change=5,  # Arbitrary utility gain from purchase
                description=f"Purchased {purchase_amount} of {resource_type.value}"
            )
            
            seller_outcome = InteractionOutcome(
                interaction_id=interaction.id,
                agent=seller,
                role=InteractionRole.SELLER,
                resources_before=[
                    ResourceBalance(resource_type=ResourceType.CREDITS, amount=seller_credits_before),
                    ResourceBalance(resource_type=resource_type, amount=seller_resource_before)
                ],
                resources_after=[
                    ResourceBalance(resource_type=ResourceType.CREDITS, amount=seller_credits_after),
                    ResourceBalance(resource_type=resource_type, amount=seller_resource_after)
                ],
                utility_change=3,  # Arbitrary utility gain from sale
                description=f"Sold {purchase_amount} of {resource_type.value}"
            )
        else:
            # Failed purchase
            buyer_outcome = InteractionOutcome(
                interaction_id=interaction.id,
                agent=buyer,
                role=InteractionRole.BUYER,
                resources_before=[],
                resources_after=[],
                utility_change=-1,  # Small negative utility from failed purchase
                description=f"Failed to purchase {resource_type.value}: {interaction.parameters.get('failure_reason', 'Unknown reason')}"
            )
            
            seller_outcome = InteractionOutcome(
                interaction_id=interaction.id,
                agent=seller,
                role=InteractionRole.SELLER,
                resources_before=[],
                resources_after=[],
                utility_change=0,  # No change for seller
                description="Failed sale"
            )
        
        interaction.outcomes = [buyer_outcome, seller_outcome]
        
        return interaction 