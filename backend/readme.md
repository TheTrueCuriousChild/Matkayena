# Server Architecture & API Responsibilities

## 🏛️ Server 1: Core / API Server (Public Gateway)

* **Port / URL:** `http://127.0.0.1:8000`
* **Swagger UI:** http://127.0.0.1:8000/docs
* **Entrypoint File:** `backend/services/core_server/main.py`

### 🎯 Primary Responsibilities

1. **Public API Gateway:** Front door for all client applications, web dashboards, and mobile frontends.
2. **Identity & JWT Token Issuance:** Authenticates users and issues signed JWT access tokens with embedded role claims (`RM`, `MANAGER`, `ADMIN`).
3. **Server-Side RBAC Enforcement:** Restricts Relationship Managers (RMs) from viewing data, tasks, or performance metrics belonging to other RMs.
4. **Customer 360 Aggregation:** Serves complete customer profiles, demographic details, product holdings, transaction history, and active leads.
5. **Microservice Request Routing:** Forwards event ingestion, action completion, and audit verification requests to downstream servers with correlation ID tracing.

### 🔌 Key Endpoints

| Method | Endpoint                                     | Description                                             |
| ------ | -------------------------------------------- | ------------------------------------------------------- |
| `POST` | `/api/v1/auth/generate-token`                | Issues JWT access token for testing.                    |
| `POST` | `/api/v1/events/submit-event`                | Ingests commercial/banking events; proxies to Server 2. |
| `GET`  | `/api/v1/customers/list-assigned`            | Lists customers assigned to the authenticated RM.       |
| `GET`  | `/api/v1/customers/360-view/{customer_id}`   | Returns a complete Customer 360 overview.               |
| `GET`  | `/api/v1/opportunities/list-opportunities`   | Lists detected commercial opportunities.                |
| `GET`  | `/api/v1/actions/list-actions`               | Lists RM tasks.                                         |
| `POST` | `/api/v1/actions/{id}/complete-conversion`   | Completes an RM conversion task.                        |
| `GET`  | `/api/v1/performance/evaluate-rm/{rm_id}`    | Returns RM performance diagnostics.                     |
| `GET`  | `/api/v1/manager/alerts/list-alerts`         | Returns managerial risk alerts and escalations.         |
| `GET`  | `/api/v1/audit/records/list-records`         | Lists audit ledger records.                             |
| `GET`  | `/api/v1/audit/verify-chain/validate-ledger` | Validates the audit ledger.                             |

---

## 🧠 Server 2: Event + Intelligence Server (The 3 Agents)

* **Port / URL:** `http://127.0.0.1:8001`
* **Swagger UI:** http://127.0.0.1:8001/docs
* **Entrypoint File:** `backend/services/event_intelligence_server/main.py`

### 🎯 Primary Responsibilities

1. **Event Ingestion & Idempotency:** Validates event payloads and idempotently deduplicates repeated submissions to prevent double-processing.

2. **Agent #1 — Opportunity Agent**

   * Automatically analyzes real-time customer deposit events (`PAYIN_RECEIVED`), activity events, and lead creations.
   * Detects cross-sell, upsell, and dormant customer reactivations.
   * Calculates deterministic weighted scores (`0.0` to `1.0`).
   * Provides full explainability evidence:

     * `what`
     * `why`
     * `rule_evaluated`
     * `signals`
   * Automatically posts actionable tasks to **Server 3**.

3. **Agent #2 — Performance Agent**

   * Evaluates RM quota pacing, conversion rates, follow-up SLA breaches, and pipeline value.
   * Diagnoses status:

     * `HEALTHY`
     * `ON_TRACK`
     * `AT_RISK`
     * `CRITICAL`
     * `EXCEPTIONAL`
   * Records achievement milestones such as `EARLY_TARGET_ACHIEVEMENT`.

4. **Agent #3 — Manager Agent**

   * Synthesizes risk alerts, quota shortfalls, and team escalations.
   * Employs anti-spam cooldown throttling to prevent alert fatigue.

### 🔌 Key Endpoints

| Method | Endpoint                                                | Description                                          |
| ------ | ------------------------------------------------------- | ---------------------------------------------------- |
| `POST` | `/api/v1/events/ingest-event`                           | Internal event ingestion and idempotency pipeline.   |
| `POST` | `/api/v1/intelligence/evaluate-customer-opportunity`    | Invokes the Opportunity Agent for a customer.        |
| `POST` | `/api/v1/intelligence/evaluate-rm-performance`          | Invokes the Performance Agent for an RM.             |
| `GET`  | `/api/v1/intelligence/manager-intelligence/list-alerts` | Synthesizes manager alerts.                          |
| `GET`  | `/api/v1/intelligence/opportunities/{opportunity_id}`   | Returns complete opportunity explainability details. |

---

## ⚡ Server 3: Action + Commission Server (State Machine & Math)

* **Port / URL:** `http://127.0.0.1:8002`
* **Swagger UI:** http://127.0.0.1:8002/docs
* **Entrypoint File:** `backend/services/action_commission_server/main.py`

### 🎯 Primary Responsibilities

1. **Action Task Lifecycle Management**

   * Enforces a strict finite state machine:
     `PROPOSED → ASSIGNED → IN_PROGRESS → COMPLETED`
   * Alternative terminal or transitional states include:

     * `SNOOZED`
     * `REASSIGNED`
     * `REJECTED`
     * `EXPIRED`
   * Maintains complete transition audit history with timestamps and reasons in `action_history`.

2. **100% Deterministic Commission Engine (0% LLM)**

   * Uses pure mathematical calculations:

   $$
   \text{Commission}
   =================

   \text{Converted Value}
   \times
   \text{Base Rate}
   \times
   \text{Segment Multiplier}
   \times
   \text{Volume Tier Multiplier}
   $$

   * Zero hallucinations.
   * 100% reproducible and verifiable.

3. **Audit Emission**

   * Automatically transmits completed conversion and commission events to **Server 4** for cryptographic hash-chaining.

### 🔌 Key Endpoints

| Method | Endpoint                                          | Description                                                |
| ------ | ------------------------------------------------- | ---------------------------------------------------------- |
| `POST` | `/api/v1/actions/create-action`                   | Creates an actionable task.                                |
| `GET`  | `/api/v1/actions/list-actions`                    | Lists tasks by RM, customer, or status.                    |
| `GET`  | `/api/v1/actions/{action_id}`                     | Returns task details, outcome, and full lifecycle history. |
| `POST` | `/api/v1/actions/{action_id}/complete-conversion` | Marks a task as completed and computes commission.         |
| `POST` | `/api/v1/actions/{action_id}/snooze`              | Defers task follow-up.                                     |
| `POST` | `/api/v1/actions/{action_id}/reassign`            | Reassigns a task to another RM.                            |

---

## 🔒 Server 4: Audit + Blockchain Server (Ledger & Proofs)

* **Port / URL:** `http://127.0.0.1:8003`
* **Swagger UI:** http://127.0.0.1:8003/docs
* **Entrypoint File:** `backend/services/audit_blockchain_server/main.py`

### 🎯 Primary Responsibilities

1. **Canonical JSON Serialization & Hashing**

   * Computes deterministic SHA-256 hashes of canonical, sorted JSON payloads.

2. **Cryptographic Sequential Hash Chain**

   * Maintains a tamper-evident hash chain beginning from the Genesis hash (`0000...`).

   $$
   \text{Node Hash}
   ================

   \text{SHA256}
   \left(
   \text{Previous Hash}
   ,|,
   \text{Payload Hash}
   ,|,
   \text{Entity Type}
   ,|,
   \text{Entity ID}
   ,|,
   \text{Action}
   \right)
   $$

3. **Ledger Integrity Verification**

   * Traverses and validates the ledger to ensure that no database record or hash link has been modified.

4. **Blockchain Proof Anchoring & Failure Isolation**

   * Anchors batch root hashes through `LocalIntegrityLedgerAdapter` or an external Web3 network.
   * Never stores customer PII on-chain.
   * **Failure Isolation Guarantee:** Blockchain downtime leaves records in `PENDING` retry status and **never halts or rolls back CRM business actions**.

### 🔌 Key Endpoints

| Method | Endpoint                                  | Description                                                 |
| ------ | ----------------------------------------- | ----------------------------------------------------------- |
| `POST` | `/api/v1/audit/create-record`             | Creates a new hash-chain entry and queues it for anchoring. |
| `GET`  | `/api/v1/audit/list-records`              | Lists chronological audit records and transaction proofs.   |
| `GET`  | `/api/v1/audit/verify-record/{record_id}` | Cryptographically verifies an individual record.            |
| `GET`  | `/api/v1/audit/verify-full-chain`         | Validates unbroken full-ledger continuity.                  |

---

## 🔄 Server Communication Flow

```text
                    ┌──────────────────────────┐
                    │     Client Applications  │
                    │ Web / Mobile / Dashboard │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │       SERVER 1            │
                    │     Core / API Gateway    │
                    │        Port: 8000         │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
      ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
      │   SERVER 2   │   │   SERVER 3   │   │   SERVER 4   │
      │ Event +      │   │ Action +     │   │ Audit +      │
      │ Intelligence │   │ Commission   │   │ Blockchain   │
      │   Port 8001  │   │   Port 8002  │   │   Port 8003  │
      └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
             │                  │                  │
             │                  └─────────────────►│
             │                                     │
             └──────────────► Server 3 ────────────┘
```

### Overall Responsibility

| Server       | Primary Role                                                            |   Port |
| ------------ | ----------------------------------------------------------------------- | -----: |
| **Server 1** | Public API, Authentication, RBAC, Customer 360, Routing                 | `8000` |
| **Server 2** | Event Processing, Opportunity Intelligence, Performance, Manager Agents | `8001` |
| **Server 3** | Action Lifecycle, State Machine, Commission Calculation                 | `8002` |
| **Server 4** | Audit Ledger, Hash Chain, Blockchain Anchoring                          | `8003` |
