"""Agent #1 — Opportunity Agent.

Identifies commercially meaningful opportunities from customer context and incoming events,
calculates deterministic weighted scores, generates explainability, and initiates RM actions.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session
from backend.services.event_intelligence_server.rules.engine import BusinessRuleEngine
from backend.services.event_intelligence_server.scoring.opportunity_scorer import OpportunityScorer
from backend.services.shared.config import settings
from backend.services.shared.events import EventEnvelope
from backend.services.shared.http_client import ServiceClient
from backend.services.shared.logging import setup_logger
from backend.services.shared.models import Opportunity, Customer, Product, Transaction, Lead
from backend.services.shared.repositories.customer_repo import CustomerRepository
from backend.services.shared.repositories.lead_repo import LeadRepository
from backend.services.shared.repositories.opportunity_repo import OpportunityRepository

logger = setup_logger("opportunity_agent")
action_client = ServiceClient("action_commission_server", settings.ACTION_COMMISSION_SERVER_URL)
audit_client = ServiceClient("audit_blockchain_server", settings.AUDIT_BLOCKCHAIN_SERVER_URL)


class OpportunityAgent:
    AGENT_VERSION = "OpportunityAgent_v1.0"

    @classmethod
    async def evaluate_event(cls, db: Session, event: EventEnvelope) -> List[Opportunity]:
        """Evaluates an incoming event in Event Mode."""
        logger.info(f"OpportunityAgent processing event {event.event_type} for {event.entity_type}:{event.entity_id}")
        opportunities = []

        if event.event_type == "PAYIN_RECEIVED":
            opp = await cls._handle_payin_event(db, event)
            if opp:
                opportunities.append(opp)
        elif event.event_type in ["CUSTOMER_ACTIVITY", "DIGITAL_ACTIVITY"]:
            opps = await cls.evaluate_customer(db, event.entity_id, event.correlation_id, source_event_id=event.event_id)
            opportunities.extend(opps)
        elif event.event_type in ["LEAD_CREATED", "LEAD_UPDATED"]:
            opp = await cls._handle_lead_event(db, event)
            if opp:
                opportunities.append(opp)

        return opportunities

    @classmethod
    async def evaluate_customer(
        cls,
        db: Session,
        customer_id: str,
        correlation_id: Optional[str] = None,
        source_event_id: Optional[str] = None
    ) -> List[Opportunity]:
        """Direct evaluation mode for a customer's product gap, upsell, and reactivation potential."""
        correlation_id = correlation_id or str(uuid.uuid4())
        customer = CustomerRepository.get_by_id(db, customer_id)
        if not customer:
            return []

        holdings = CustomerRepository.get_holdings(db, customer_id)
        held_product_ids = {h.product_id for h in holdings}
        all_products = CustomerRepository.list_products(db, active_only=True)
        all_categories = {p.category for p in all_products}

        # Categories held
        held_categories = set()
        for h in holdings:
            p = CustomerRepository.get_product_by_id(db, h.product_id)
            if p:
                held_categories.add(p.category)

        opportunities = []

        # 1. Check Product Gap / Cross-sell for missing categories
        if "INSURANCE" in all_categories and "INSURANCE" not in held_categories:
            insurance_product = next((p for p in all_products if p.category == "INSURANCE"), None)
            opp = await cls._create_or_dedup_opportunity(
                db=db,
                customer=customer,
                opp_type="CROSS_SELL",
                product=insurance_product,
                title=f"Insurance Cross-Sell for {customer.first_name} {customer.last_name}",
                rule_code="CROSS_SELL_INSURANCE",
                signals={
                    "segment": 0.9 if customer.segment in ["HNI", "ULTRA_HNI"] else 0.6,
                    "product_gap": 1.0,
                    "relationship": min(1.0, (customer.relationship_value or 0) / 1_000_000)
                },
                estimated_value=round((customer.relationship_value or 50000) * 0.10, 2),
                recommended_action="Present comprehensive health and term life protection coverage.",
                reason_codes=["NO_INSURANCE_HOLDING", "STRONG_RELATIONSHIP_VALUE"],
                correlation_id=correlation_id,
                source_event_id=source_event_id
            )
            if opp:
                opportunities.append(opp)

        # 2. Check Dormant Reactivation
        if customer.status == "DORMANT":
            opp = await cls._create_or_dedup_opportunity(
                db=db,
                customer=customer,
                opp_type="DORMANT_REACTIVATION",
                product=None,
                title=f"Reactivate Dormant Relationship: {customer.first_name} {customer.last_name}",
                rule_code="DORMANT_REACTIVATION",
                signals={
                    "relationship": min(1.0, (customer.relationship_value or 0) / 500_000),
                    "activity": 0.8
                },
                estimated_value=customer.relationship_value or 25000.0,
                recommended_action="Initiate relationship wellness check and present new investment opportunities.",
                reason_codes=["DORMANT_STATUS", "HIGH_HISTORICAL_VALUE"],
                correlation_id=correlation_id,
                source_event_id=source_event_id
            )
            if opp:
                opportunities.append(opp)

        return opportunities

    @classmethod
    async def _handle_payin_event(cls, db: Session, event: EventEnvelope) -> Optional[Opportunity]:
        """Handles deposit/payin events to detect immediate cross-sell/upsell."""
        customer_id = event.entity_id if event.entity_type == "CUSTOMER" else event.payload.get("customer_id")
        if not customer_id:
            return None

        customer = CustomerRepository.get_by_id(db, customer_id)
        if not customer:
            return None

        amount = float(event.payload.get("amount", 0.0))
        rule_config = BusinessRuleEngine.get_rule_config(db, "CROSS_SELL_INSURANCE")
        min_amount = rule_config.get("conditions", {}).get("min_payin_amount", 50000)

        # Check holdings
        holdings = CustomerRepository.get_holdings(db, customer_id)
        has_insurance = any(
            (CustomerRepository.get_product_by_id(db, h.product_id) or Product(category="")).category == "INSURANCE"
            for h in holdings
        )

        if amount >= min_amount and not has_insurance:
            insurance_product = next((p for p in CustomerRepository.list_products(db) if p.category == "INSURANCE"), None)

            # Scoring
            signals = {
                "payin": min(1.0, amount / 500_000),
                "segment": 0.9 if customer.segment in ["HNI", "ULTRA_HNI"] else 0.6,
                "product_gap": 1.0
            }

            return await cls._create_or_dedup_opportunity(
                db=db,
                customer=customer,
                opp_type="CROSS_SELL",
                product=insurance_product,
                title=f"Insurance Cross-Sell: ₹{int(amount):,} Payin by {customer.first_name} {customer.last_name}",
                rule_code="CROSS_SELL_INSURANCE",
                signals=signals,
                estimated_value=round(amount * 0.15, 2),
                recommended_action=f"Contact customer regarding guaranteed income insurance plan suited for recent deposit of ₹{int(amount):,}.",
                reason_codes=["RECENT_LARGE_PAYIN", "NO_INSURANCE_HOLDING", "INVESTMENT_SURPLUS"],
                correlation_id=event.correlation_id,
                source_event_id=event.event_id
            )

        return None

    @classmethod
    async def _handle_lead_event(cls, db: Session, event: EventEnvelope) -> Optional[Opportunity]:
        """Handles high-intent lead events."""
        lead = LeadRepository.get_by_id(db, event.entity_id)
        if not lead:
            return None

        intent_score = float(lead.intent_score or 0.5)
        if intent_score >= 0.70:
            customer = CustomerRepository.get_by_id(db, lead.customer_id) if lead.customer_id else None
            product = CustomerRepository.get_product_by_id(db, lead.product_id) if lead.product_id else None

            rm_id = lead.assigned_rm_id or (customer.primary_rm_id if customer else None)
            if not rm_id:
                return None

            signals = {
                "intent": intent_score,
                "value": min(1.0, (lead.estimated_value or 50000) / 500_000)
            }

            return await cls._create_or_dedup_opportunity(
                db=db,
                customer=customer or Customer(id=lead.id, first_name=lead.title, last_name="", primary_rm_id=rm_id, segment="RETAIL"),
                opp_type="HIGH_INTENT_LEAD",
                product=product,
                title=f"High-Intent Lead Priority: {lead.title}",
                rule_code="HIGH_INTENT_LEAD",
                signals=signals,
                estimated_value=lead.estimated_value,
                recommended_action=f"High conversion probability ({int(intent_score * 100)}%). Immediate follow-up required within 2 hours.",
                reason_codes=["HIGH_DIGITAL_INTENT", "PRODUCT_INTEREST_EXPRESSED"],
                correlation_id=event.correlation_id,
                source_event_id=event.event_id,
                lead_id=lead.id
            )

        return None

    @classmethod
    async def _create_or_dedup_opportunity(
        cls,
        db: Session,
        customer: Customer,
        opp_type: str,
        product: Optional[Product],
        title: str,
        rule_code: str,
        signals: Dict[str, float],
        estimated_value: Optional[float],
        recommended_action: str,
        reason_codes: List[str],
        correlation_id: str,
        source_event_id: Optional[str] = None,
        lead_id: Optional[str] = None
    ) -> Optional[Opportunity]:
        """Deduplicates against active opportunities and creates opportunity + prioritized RM action."""
        # 1. Deterministic deduplication check
        product_id = product.id if product else None
        duplicate = OpportunityRepository.find_duplicate_active(
            db=db,
            customer_id=customer.id,
            opportunity_type=opp_type,
            product_id=product_id
        )
        if duplicate:
            logger.info(f"Duplicate opportunity suppressed for customer {customer.id} type {opp_type}")
            return None

        # 2. Rule Configuration & Scoring
        rule_config = BusinessRuleEngine.get_rule_config(db, rule_code)
        weights = rule_config.get("weights", {})
        score, score_breakdown = OpportunityScorer.calculate_score(weights, signals)
        priority = OpportunityScorer.map_priority(score)

        # 3. Explainability Payload
        evidence = {
            "what": f"Detected {opp_type} opportunity for customer {customer.first_name} {customer.last_name}",
            "why": f"Evaluated rule {rule_code} (version {rule_config.get('version_number', 1)}) with score {score:.2f}",
            "signals": score_breakdown,
            "rule_evaluated": rule_config,
            "agent_version": cls.AGENT_VERSION,
            "source_event_id": source_event_id,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }

        rm_id = customer.primary_rm_id
        if not rm_id:
            # Fallback to test/default RM
            rm_id = "default_rm"

        opp = Opportunity(
            customer_id=customer.id,
            rm_id=rm_id,
            product_id=product_id,
            opportunity_type=opp_type,
            title=title,
            status="DETECTED",
            score=score,
            priority=priority,
            estimated_value=estimated_value,
            recommended_action=recommended_action,
            reason_codes=reason_codes,
            evidence=evidence,
            source_event_id=source_event_id,
            rule_version_id=rule_config.get("rule_version_id"),
            correlation_id=correlation_id
        )
        opp = OpportunityRepository.create_opportunity(db, opp)
        logger.info(f"Opportunity created: id={opp.id}, type={opp.opportunity_type}, score={opp.score}")

        # 4. Trigger Action Creation on Server 3
        try:
            await action_client.post(
                "/api/v1/actions",
                json_data={
                    "customer_id": customer.id,
                    "assigned_rm_id": rm_id,
                    "title": f"Follow-up: {title}",
                    "description": recommended_action,
                    "action_type": "OFFER_PRODUCT" if opp_type in ["CROSS_SELL", "UPSELL"] else "CALL_CUSTOMER",
                    "priority": priority,
                    "opportunity_id": opp.id,
                    "lead_id": lead_id,
                    "source_decision_id": opp.id,
                    "correlation_id": correlation_id
                },
                correlation_id=correlation_id,
                source_service="event_intelligence_server"
            )
        except Exception as e:
            logger.warning(f"Could not immediately post action to Server 3: {e}")

        # 5. Record Audit to Server 4
        try:
            await audit_client.post(
                "/api/v1/audit/record",
                json_data={
                    "entity_type": "OPPORTUNITY",
                    "entity_id": opp.id,
                    "action": "OPPORTUNITY_DETECTED",
                    "payload": {
                        "opportunity_id": opp.id,
                        "score": opp.score,
                        "type": opp.opportunity_type,
                        "reasons": opp.reason_codes,
                        "agent_version": cls.AGENT_VERSION
                    },
                    "actor_id": "opportunity_agent",
                    "correlation_id": correlation_id,
                    "causation_id": source_event_id
                },
                correlation_id=correlation_id,
                source_service="event_intelligence_server"
            )
        except Exception:
            pass  # Blockchain/Audit failure isolation

        return opp
