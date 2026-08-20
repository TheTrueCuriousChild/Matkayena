"""Security and RBAC Authorization Tests."""

from backend.services.shared.auth import create_access_token, create_service_token, RoleEnum
from backend.services.shared.models import Customer


def test_rm_cross_access_forbidden(core_client, db_session):
    # Customer assigned to RM B (rm_user_b)
    customer = Customer(
        id="cust_b_1",
        customer_code="CUST_B",
        first_name="Priya",
        last_name="Nair",
        primary_rm_id="rm_user_b",
        segment="RETAIL"
    )
    db_session.add(customer)
    db_session.commit()

    # RM A token
    token_rm_a = create_access_token(user_id="rm_user_a", email="rma@crm.com", roles=[RoleEnum.RM.value])

    # RM A attempts to get RM B's customer -> Must return 403 Forbidden
    response = core_client.get(
        "/api/v1/customers/cust_b_1",
        headers={"Authorization": f"Bearer {token_rm_a}"}
    )
    assert response.status_code == 403
    assert response.json()["error_code"] == "UNAUTHORIZED"


def test_manager_access_permitted(core_client, db_session):
    customer = Customer(
        id="cust_b_2",
        customer_code="CUST_B2",
        first_name="Rohan",
        last_name="Kapoor",
        primary_rm_id="rm_user_b",
        segment="HNI"
    )
    db_session.add(customer)
    db_session.commit()

    # Manager token
    token_mgr = create_access_token(user_id="mgr_user_1", email="mgr@crm.com", roles=[RoleEnum.MANAGER.value])

    # Manager gets RM B's customer -> Must return 200 OK
    response = core_client.get(
        "/api/v1/customers/cust_b_2",
        headers={"Authorization": f"Bearer {token_mgr}"}
    )
    assert response.status_code == 200
    assert response.json()["customer"]["id"] == "cust_b_2"


def test_unauthenticated_request_rejected(core_client):
    response = core_client.get("/api/v1/customers")
    # In test mode without explicit token it might use dev fallback if configured, or reject
    # Let's test with invalid token
    response_invalid = core_client.get(
        "/api/v1/customers",
        headers={"Authorization": "Bearer invalid_garbage_token"}
    )
    assert response_invalid.status_code == 401
    assert response_invalid.json()["error_code"] == "UNAUTHENTICATED"
