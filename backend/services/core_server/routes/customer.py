"""Customer 360 context and CRM lookup endpoints for Core Server."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session
from backend.services.shared.auth import get_current_user, UserContext, RoleEnum
from backend.services.shared.database import get_db
from backend.services.shared.errors import AuthorizationError, NotFoundError
from backend.services.shared.models import Customer
from backend.services.shared.repositories.customer_repo import CustomerRepository
from backend.services.shared.repositories.lead_repo import LeadRepository

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])


@router.get(
    "",
    summary="List Assigned Customers",
    description="Lists customers assigned to the authenticated RM (or all customers if Manager/Admin)."
)
@router.get(
    "/list-assigned",
    summary="List Assigned Customers (Descriptive Alias)",
    description="Lists customers assigned to the authenticated RM (or all customers if Manager/Admin)."
)
def list_customers(
    limit: int = Query(50, ge=1, le=200, description="Max number of customer records to fetch"),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Lists customers assigned to the authenticated RM (or all for Manager/Admin)."""
    if user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]):
        return CustomerRepository.list_all(db, limit=limit)
    return CustomerRepository.list_by_rm(db, rm_id=user.user_id, limit=limit)


@router.get(
    "/{customer_id}",
    summary="Get Customer 360-Degree Context",
    description="Fetches demographics, product holdings, transaction history, interactions, and active leads for a customer."
)
@router.get(
    "/360-view/{customer_id}",
    summary="Get Customer 360 Context (Descriptive Alias)",
    description="Fetches demographics, product holdings, transaction history, interactions, and active leads for a customer."
)
def get_customer_360(
    customer_id: str = Path(..., description="Unique Customer identifier", examples=["cust_101"]),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):


    """Retrieves 360-degree context for a customer: demographics, holdings, transactions, and leads."""
    customer = CustomerRepository.get_by_id(db, customer_id)
    if not customer:
        raise NotFoundError("Customer", customer_id)

    # Server-side RBAC validation
    if not user.has_any_role([RoleEnum.MANAGER.value, RoleEnum.ADMIN.value]) and customer.primary_rm_id != user.user_id:
        raise AuthorizationError(f"Access denied: You are not the assigned relationship manager for customer {customer_id}")

    holdings = CustomerRepository.get_holdings(db, customer_id)
    transactions = CustomerRepository.get_transactions(db, customer_id, limit=20)
    interactions = CustomerRepository.get_interactions(db, customer_id, limit=20)
    leads = LeadRepository.list_by_customer(db, customer_id)

    return {
        "customer": customer,
        "holdings": holdings,
        "recent_transactions": transactions,
        "recent_interactions": interactions,
        "active_leads": leads
    }
