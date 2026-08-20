🏛️ Server 1: Core / API Server (Public Gateway)
Port / URL: http://127.0.0.1:8000
Swagger UI: http://127.0.0.1:8000/docs
Entrypoint File: 

backend/services/core_server/main.py
🎯 Primary Responsibilities:
Public API Gateway: Front door for all client applications, web dashboards, and mobile frontends.
Identity & JWT Token Issuance: Authenticates users and issues signed JWT access tokens with embedded role claims (RM, MANAGER, ADMIN).
Server-Side RBAC Enforcement: Restricts Relationship Managers (RMs) from viewing data, tasks, or performance metrics belonging to other RMs.
Customer 360 Aggregation: Serves complete customer profiles, demographic details, product holdings, transaction history, and active leads.
Microservice Request Routing: Forwards event ingestion, action completion, and audit verification requests to downstream servers with correlation ID tracing.
🔌 Key Endpoints:
POST /api/v1/auth/generate-token — Issues JWT access token for testing.
POST /api/v1/events/submit-event — Ingests commercial/banking events (proxies to Server 2).
GET /api/v1/customers/list-assigned & /360-view/{customer_id} — Customer 360 overview.
GET /api/v1/opportunities/list-opportunities — Lists detected commercial opportunities.
GET /api/v1/actions/list-actions & POST /api/v1/actions/{id}/complete-conversion — RM tasks.
GET /api/v1/performance/evaluate-rm/{rm_id} — RM performance diagnostics.
GET /api/v1/manager/alerts/list-alerts — Managerial risk alerts and escalations.
GET /api/v1/audit/records/list-records & /verify-chain/validate-ledger — Audit ledger.
🧠 Server 2: Event + Intelligence Server (The 3 Agents)
Port / URL: http://127.0.0.1:8001
Swagger UI: http://127.0.0.1:8001/docs
Entrypoint File: 

backend/services/event_intelligence_server/main.py
🎯 Primary Responsibilities:
Event Ingestion & Idempotency: Validates event payloads and idempotently deduplicates repeated submissions to prevent double-processing.
Agent #1 (Opportunity Agent):
Automatically analyzes real-time customer deposit events (PAYIN_RECEIVED), activity events, and lead creations.
Detects cross-sell, upsell, and dormant customer reactivations.
Calculates deterministic weighted scores (0.0 to 1.0) and provides full explainability evidence (what, why, rule_evaluated, signals).
Automatically posts actionable tasks to Server 3.
Agent #2 (Performance Agent):
Evaluates RM quota pacing, conversion rates, follow-up SLA breaches, and pipeline value.
Diagnoses status: HEALTHY, ON_TRACK, AT_RISK, CRITICAL, or EXCEPTIONAL.
Records achievement milestones (e.g. EARLY_TARGET_ACHIEVEMENT).
Agent #3 (Manager Agent):
Synthesizes risk alerts, quota shortfalls, and team escalations.
Employs anti-spam cooldown throttling to prevent alert fatigue.
🔌 Key Endpoints:
POST /api/v1/events/ingest-event — Internal event ingestion & idempotency pipeline.
POST /api/v1/intelligence/evaluate-customer-opportunity — Invokes Opportunity Agent for a customer.
POST /api/v1/intelligence/evaluate-rm-performance — Invokes Performance Agent for an RM.
GET /api/v1/intelligence/manager-intelligence/list-alerts — Synthesizes manager alerts.
GET /api/v1/intelligence/opportunities/{opportunity_id} — Returns full explainability details.
⚡ Server 3: Action + Commission Server (State Machine & Math)
Port / URL: http://127.0.0.1:8002
Swagger UI: http://127.0.0.1:8002/docs
Entrypoint File: 

backend/services/action_commission_server/main.py
🎯 Primary Responsibilities:
Action Task Lifecycle Management:
Enforces a strict finite state machine: PROPOSED $\rightarrow$ ASSIGNED $\rightarrow$ IN_PROGRESS $\rightarrow$ COMPLETED (or SNOOZED, REASSIGNED, REJECTED, EXPIRED).
Maintains full transition audit history with timestamps and reasons in action_history.
100% Deterministic Commission Engine (0% LLM):
Pure mathematical calculations based on: $$\text{Commission} = \text{Converted Value} \times \text{Base Rate} \times \text{Segment Multiplier} \times \text{Volume Tier Multiplier}$$
Zero hallucinations, 100% reproducible and verifiable.
Audit Emission: Automatically transmits completed conversion and commission events to Server 4 for cryptographic hash-chaining.
🔌 Key Endpoints:
POST /api/v1/actions/create-action — Creates an actionable task.
GET /api/v1/actions/list-actions — Lists tasks by RM, customer, or status.
GET /api/v1/actions/{action_id} — Gets task details, outcome, and full lifecycle history.
POST /api/v1/actions/{action_id}/complete-conversion — Marks task completed and computes commission.
POST /api/v1/actions/{action_id}/snooze — Defers task follow-up.
POST /api/v1/actions/{action_id}/reassign — Reassigns task to another RM.
🔒 Server 4: Audit + Blockchain Server (Ledger & Proofs)
Port / URL: http://127.0.0.1:8003
Swagger UI: http://127.0.0.1:8003/docs
Entrypoint File: 

backend/services/audit_blockchain_server/main.py
🎯 Primary Responsibilities:
Canonical JSON Serialization & Hashing: Computes deterministic SHA-256 hashes of canonical sorted JSON payloads.
Cryptographic Sequential Hash-Chain:
Maintains a tamper-evident hash chain from Genesis (0000...): $$\text{Node Hash} = \text{SHA256}(\text{Previous Hash} ,|, \text{Payload Hash} ,|, \text{Entity Type} ,|, \text{Entity ID} ,|, \text{Action})$$
Ledger Integrity Verification: Traverses and validates that no database record or hash link has been modified.
Blockchain Proof Anchoring & Failure Isolation:
Anchors batch root hashes via LocalIntegrityLedgerAdapter or external Web3 network without storing any customer PII on-chain.
Failure Isolation Guarantee: Blockchain downtime leaves records in PENDING retry status and NEVER halts or rolls back CRM business actions.
🔌 Key Endpoints:
POST /api/v1/audit/create-record — Records a new hash-chain entry and queues anchoring.
GET /api/v1/audit/list-records — Lists chronological audit records and transaction proofs.
GET /api/v1/audit/verify-record/{record_id} — Cryptographically verifies an individual record.
GET /api/v1/audit/verify-full-chain — Validates unbroken full ledger continuity.
