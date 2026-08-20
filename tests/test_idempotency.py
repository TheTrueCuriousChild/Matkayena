"""Idempotency and duplicate processing tests."""

from backend.services.shared.auth import create_access_token, RoleEnum
from backend.services.shared.models import Customer


def test_event_ingestion_idempotency(event_client, db_session):
    customer = Customer(
        id="cust_idemp_1",
        customer_code="CUST_IDEMP",
        first_name="Deepak",
        last_name="Gupta",
        primary_rm_id="rm_1",
        segment="RETAIL"
    )
    db_session.add(customer)
    db_session.commit()

    token = create_access_token("rm_1", "rm1@crm.com", [RoleEnum.RM.value])
    headers = {"Authorization": f"Bearer {token}"}

    event_payload = {
        "event_type": "PAYIN_RECEIVED",
        "entity_type": "CUSTOMER",
        "entity_id": "cust_idemp_1",
        "payload": {"amount": 75000.0, "customer_id": "cust_idemp_1"},
        "idempotency_key": "idemp_test_key_999",
        "correlation_id": "corr_idemp_1"
    }

    # 1. First Submission -> Should process
    res1 = event_client.post("/api/v1/events/ingest", json=event_payload, headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["success"] is True
    event_id = data1["event_id"]

    # 2. Second Submission with exact same idempotency key -> Must be idempotently suppressed
    res2 = event_client.post("/api/v1/events/ingest", json=event_payload, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["success"] is True
    assert data2["event_id"] == event_id
    assert data2["details"]["status"] == "IDEMPOTENT_SUPPRESSION"
