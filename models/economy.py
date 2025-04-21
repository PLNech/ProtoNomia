"""
Economy models for ProtoNomia.
This module contains models for economic markets and listings.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Set
from uuid import uuid4

from pydantic import BaseModel, Field, validator

from models.base import ResourceType, Agent


class ListingType(str, Enum):
    """Types of market listings"""
    GOODS_OFFER = "goods_offer"           # Selling goods
    GOODS_REQUEST = "goods_request"       # Buying goods
    JOB_OFFER = "job_offer"               # Offering a job


class Listing(BaseModel):
    """Base model for market listings"""
    id: str = Field(default_factory=lambda: f"listing_{uuid4()}")
    listing_type: ListingType
    creator_id: str                           # ID of the agent who created the listing
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None     # When the listing expires
    active: bool = True                       # Whether the listing is active
    expiry_turn: Optional[int] = None         # Turn when listing expires (alternative to expires_at)


class GoodsListing(Listing):
    """Listing for goods market (offer or request)"""
    resource_type: ResourceType              # Type of resource being traded
    amount: float                            # Amount (positive for offer, negative for request)
    price_per_unit: float                    # Price per unit of the resource
    price_resource_type: ResourceType = ResourceType.CREDITS  # Type of resource for payment
    description: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v, values):
        """Validate that amount is consistent with listing type"""
        if 'listing_type' in values:
            if values['listing_type'] == ListingType.GOODS_OFFER and v <= 0:
                raise ValueError("Goods offers must have positive amount")
            if values['listing_type'] == ListingType.GOODS_REQUEST and v >= 0:
                raise ValueError("Goods requests must have negative amount")
        return v


class JobListing(Listing):
    """Listing for job market"""
    job_type: str                             # Type of job being offered
    salary_per_turn: float                    # Salary per turn
    salary_resource_type: ResourceType = ResourceType.CREDITS  # Type of resource for salary
    requirements: str                         # Requirements for the job (skills, etc.)
    description: Optional[str] = None
    max_employees: int = 1                    # Maximum number of employees for this job
    current_employees: List[str] = Field(default_factory=list)  # IDs of current employees
    
    @validator('listing_type')
    def validate_listing_type(cls, v):
        """Validate that listing type is JOB_OFFER"""
        if v != ListingType.JOB_OFFER:
            raise ValueError("Job listings must have listing_type=JOB_OFFER")
        return v


class Market(BaseModel):
    """Base model for markets"""
    listings: Dict[str, Listing] = Field(default_factory=dict)  # ID -> Listing
    
    def add_listing(self, listing: Listing) -> None:
        """Add a listing to the market"""
        self.listings[listing.id] = listing
    
    def remove_listing(self, listing_id: str) -> None:
        """Remove a listing from the market"""
        if listing_id in self.listings:
            del self.listings[listing_id]
    
    def deactivate_listing(self, listing_id: str) -> None:
        """Deactivate a listing"""
        if listing_id in self.listings:
            self.listings[listing_id].active = False
    
    def get_active_listings(self) -> List[Listing]:
        """Get all active listings"""
        return [listing for listing in self.listings.values() if listing.active]
    
    def get_listings_by_creator(self, creator_id: str) -> List[Listing]:
        """Get all listings created by an agent"""
        return [listing for listing in self.listings.values() if listing.creator_id == creator_id]


class GoodsMarket(Market):
    """Goods market"""
    
    def get_offers(self, resource_type: Optional[ResourceType] = None) -> List[GoodsListing]:
        """Get all goods offers, optionally filtered by resource type"""
        listings = [listing for listing in self.listings.values() 
                   if listing.active and listing.listing_type == ListingType.GOODS_OFFER]
        
        if resource_type:
            listings = [listing for listing in listings 
                       if isinstance(listing, GoodsListing) and listing.resource_type == resource_type]
        
        return [listing for listing in listings if isinstance(listing, GoodsListing)]
    
    def get_requests(self, resource_type: Optional[ResourceType] = None) -> List[GoodsListing]:
        """Get all goods requests, optionally filtered by resource type"""
        listings = [listing for listing in self.listings.values() 
                   if listing.active and listing.listing_type == ListingType.GOODS_REQUEST]
        
        if resource_type:
            listings = [listing for listing in listings 
                       if isinstance(listing, GoodsListing) and listing.resource_type == resource_type]
        
        return [listing for listing in listings if isinstance(listing, GoodsListing)]


class JobMarket(Market):
    """Job market"""
    
    def get_job_offers(self, job_type: Optional[str] = None) -> List[JobListing]:
        """Get all job offers, optionally filtered by job type"""
        listings = [listing for listing in self.listings.values() 
                   if listing.active and listing.listing_type == ListingType.JOB_OFFER]
        
        if job_type:
            listings = [listing for listing in listings 
                       if isinstance(listing, JobListing) and listing.job_type == job_type]
        
        return [listing for listing in listings if isinstance(listing, JobListing)]
    
    def add_employee_to_job(self, job_id: str, employee_id: str) -> bool:
        """Add an employee to a job"""
        if job_id in self.listings:
            job_listing = self.listings[job_id]
            if isinstance(job_listing, JobListing):
                if employee_id not in job_listing.current_employees:
                    if len(job_listing.current_employees) < job_listing.max_employees:
                        job_listing.current_employees.append(employee_id)
                        return True
        return False
    
    def remove_employee_from_job(self, job_id: str, employee_id: str) -> bool:
        """Remove an employee from a job"""
        if job_id in self.listings:
            job_listing = self.listings[job_id]
            if isinstance(job_listing, JobListing):
                if employee_id in job_listing.current_employees:
                    job_listing.current_employees.remove(employee_id)
                    return True
        return False


class EmploymentManager(BaseModel):
    """Manager for employment relationships"""
    job_assignments: Dict[str, str] = Field(default_factory=dict)  # employee_id -> job_id
    
    def assign_job(self, employee_id: str, job_id: str) -> bool:
        """Assign an employee to a job"""
        self.job_assignments[employee_id] = job_id
        return True
    
    def unassign_job(self, employee_id: str) -> bool:
        """Unassign an employee from their job"""
        if employee_id in self.job_assignments:
            del self.job_assignments[employee_id]
            return True
        return False
    
    def get_employee_job(self, employee_id: str) -> Optional[str]:
        """Get the job ID for an employee"""
        return self.job_assignments.get(employee_id)


class EconomyState(BaseModel):
    """State of the economy"""
    goods_market: GoodsMarket = Field(default_factory=GoodsMarket)
    job_market: JobMarket = Field(default_factory=JobMarket)
    employment_manager: EmploymentManager = Field(default_factory=EmploymentManager) 